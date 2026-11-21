import os
import sys
import random
import argparse
import time
import math
import warnings
import glob
import hashlib
import tempfile
from pathlib import Path
import json
from contextlib import nullcontext
from typing import Any, Literal
from enum import Enum
from itertools import islice

import numpy

__package__ = "trainer"
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from pydantic import BaseModel, Field

from datasets import load_dataset, Features, Value
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader, DistributedSampler, Sampler
from transformers.activations import ACT2FN
from transformers import PreTrainedModel, GenerationMixin, PretrainedConfig
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from transformers.cache_utils import Cache
from transformers.modeling_outputs import MoeCausalLMOutputWithPast
from transformers.utils.chat_template_utils import render_jinja_template

warnings.filterwarnings("ignore")


# 下载数据集说明：modelscope download --dataset gongjy/minimind_dataset README.md --local_dir ./dataset

PYTORCH_IGNORE_INDEX: int = -100


class LLMTrainWeightType(Enum):
    kNone = 0
    kPretrain = 1
    kFullSFT = 2


class LLMTrainConfigureSave(BaseModel):
    save_weight: LLMTrainWeightType
    dir: str
    step_interval: int


class LLMTrainConfigureRopeScaling(BaseModel):
    beta_fast: int
    beta_slow: int
    factor: int
    original_max_position_embeddings: int
    attention_factor: float
    type: str


class LLMTrainConfigureTrain(BaseModel):
    stage: Literal["pretrain", "sft"] = "pretrain"
    from_weight: LLMTrainWeightType
    batch_size: int
    epochs: int
    learning_rate: float
    device: str
    use_compile: bool
    seed: int
    accumulation_steps: int
    grad_clip: float


class LLMTrainConfigureParam(BaseModel):
    eps: float
    dtype: Literal["bfloat16", "float16", "float32"]
    hidden_size: int
    num_hidden_layers: int
    dropout: float
    vocab_size: int
    bos_token_id: int
    eos_token_id: int
    flash_attn: bool
    num_attention_heads: int
    num_key_value_heads: int
    hidden_act: str
    intermediate_size: int
    max_position_embeddings: int
    rope_theta: float
    tie_word_embeddings: bool
    inference_rope_scaling: bool
    rope_scaling: LLMTrainConfigureRopeScaling | None = None
    use_moe: bool
    moe_num_experts: int
    moe_num_experts_per_tok: int
    moe_intermediate_size: int
    norm_topk_prob: bool
    router_aux_loss_coef: float


class LLMTrainConfigureLoader(BaseModel):
    num_workers: int
    data_item_max_length: int
    tokenizer_path: str
    sft_add_system_ratio: float = Field(default=0.2, ge=0, le=1)
    sft_empty_think_ratio: float = Field(default=0.2, ge=0, le=1)


class LLMTrainConfigureVisualizationWanDB(BaseModel):
    project: str


class LLMTrainConfigureVisualization(BaseModel):
    wandb: LLMTrainConfigureVisualizationWanDB | None


class LLMTrainConfigureLog(BaseModel):
    step_interval: int


class LLMTrainConfigureAll(BaseModel):
    model_name: str
    save: LLMTrainConfigureSave
    train: LLMTrainConfigureTrain
    param: LLMTrainConfigureParam
    loader: LLMTrainConfigureLoader
    visualization: LLMTrainConfigureVisualization | None
    log: LLMTrainConfigureLog


# torchrun 启动时会设置 RANK 和 LOCAL_RANK 环境变量
def init_distributed_mode(settings: LLMTrainConfigureAll):
    distributed = int(os.environ.get("RANK", -1)) != -1
    local_rank = int(os.environ["LOCAL_RANK"]) if distributed else 0
    device = torch.device(settings.train.device)
    if device.type == "cuda":
        if distributed and not dist.is_nccl_available():
            raise RuntimeError(
                "当前 PyTorch 未提供 NCCL/RCCL，无法启动 GPU DDP；请使用单进程 GPU，或在支持该后端的环境中运行。CPU DDP 可将 train.device 设为 cpu。"
            )
        if not torch.cuda.is_available():
            raise RuntimeError("配置要求 CUDA/ROCm 设备，但当前环境不可用")
        device = torch.device(
            "cuda",
            (
                local_rank
                if distributed
                else (
                    device.index
                    if device.index is not None
                    else torch.cuda.current_device()
                )
            ),
        )
        torch.cuda.set_device(device)
    elif device.type != "cpu":
        raise ValueError("本示例支持的训练设备为 cpu 和 cuda")
    settings.train.device = str(device)
    if distributed:
        backend = "nccl" if device.type == "cuda" else "gloo"
        if backend == "gloo" and not dist.is_gloo_available():
            raise RuntimeError("当前 PyTorch 未提供 Gloo，无法启动 CPU DDP")
        dist.init_process_group(backend=backend)
    return local_rank


LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE: int = 768
LLM_TRAIN_SETTINGS = LLMTrainConfigureAll.model_validate(
    {
        "model_name": "OWenTLLM",
        "save": {
            "save_weight": LLMTrainWeightType.kPretrain,
            "dir": "./out",
            # 每隔多少个 microbatch 保存一次，实际保存延后到窗口结束。
            "step_interval": 1000,
        },
        "train": {
            # 基于哪个权重训练，为none则从头开始
            "from_weight": LLMTrainWeightType.kNone,
            # Batch size
            "batch_size": 8,
            # 训练轮数
            "epochs": 2,
            # 余弦衰减的学习率上限，第一次更新按首个窗口的结束位置取值。
            "learning_rate": 2e-5,
            # 训练设备(如果有多GPU或者AMD的独显+集显，请注意选择正确的显卡设备)
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            # 是否使用torch.compile加速
            "use_compile": False,
            # 每个 epoch 的进程随机种子为 seed + epoch + rank，续训要求配置中的 seed 一致。
            "seed": 42,
            # 梯度累积步数。每个窗口最多 8 个 microbatch，窗口结束时尝试更新一次参数。
            # “梯度累积与参数更新” 章节详解了它的作用原理
            "accumulation_steps": 8,
            # 梯度裁剪阈值。所有参数梯度合在一起后的全局 L2 范数上限。
            # 近似处理公式 $g \leftarrow g \cdot \min\left(1,\frac{1.0}{\lVert g\rVert_2}\right)$
            # 总梯度范数超过阈值时，按同一比例缩小所有参数的梯度。
            "grad_clip": 1.0,
        },
        "param": {
            # epsilon 参数
            "eps": 1e-6,
            # 混合精度类型
            "dtype": "bfloat16",
            # Embedding 输出直接进入 Decoder Block。残差流、注意力和 FFN 的输入与输出均为 hidden_size。
            "hidden_size": LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE,
            # Decoder Block 数量，各层依次执行因果自注意力和前馈网络。
            "num_hidden_layers": 8,
            # Dropout 概率，设为 0 时关闭。
            "dropout": 0.0,
            # 词表大小，包括普通 token 和特殊 token
            "vocab_size": 6400,
            # BOS: Beginning of Sequence，表示序列开始。
            # 这个 ID 必须与 tokenizer 中的定义一致。ID 本身没有特殊语义，语义来自 tokenizer、训练数据和生成代码的共同约定。
            "bos_token_id": 1,
            # EOS，即 End of Sequence，表示序列结束。
            # 这个 ID 必须与 tokenizer 中的定义一致。ID 本身没有特殊语义，语义来自 tokenizer、训练数据和生成代码的共同约定。
            "eos_token_id": 2,
            # 是否允许走 PyTorch SDPA 路径，具体内核由 PyTorch 选择。
            "flash_attn": True,
            # 多头注意力的头数量，每个头分开计算。然后再concat到一起
            "num_attention_heads": 8,
            # KV头数量。 只有 4 个头，构成 GQA（Grouped Query Attention）
            # 这样可以将 K/V 投影参数量和 KV cache 减半，降低自回归解码时的显存占用和读取带宽；注意力输出仍保持 8 个头。
            # - num_key_value_heads == num_attention_heads：普通 MHA。
            # - num_key_value_heads == 1：MQA。
            "num_key_value_heads": 4,
            # 前馈网络使用的激活函数： $\operatorname{SiLU}(x)=x\operatorname{sigmoid}(x)$
            # 当前 FFN 实际使用的是 SwiGLU 结构：$\operatorname{FFN}(x) = W_{\text{down}} \left( \operatorname{SiLU}(W_{\text{gate}}x) \odot W_{\text{up}}x \right)$
            "hidden_act": "silu",
            # 普通稠密 FFN 的中间维度。当前计算结果为： $\left\lceil\frac{768\pi}{64}\right\rceil\times64 =38\times64 =2432$
            # 乘以 π 并向上对齐到 64 是这份模型的维度设计，不是 Transformer 的数学要求。
            "intermediate_size": math.ceil(
                LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE * math.pi / 64
            )
            * 64,
            # 当前代码用它确定预计算 RoPE 正余弦表的长度，因此可表示位置：0 ～ 32767
            # RoPE: Rotary Position Embedding，旋转位置编码。详见 “RoPE: Rotary Position Embedding，旋转位置编码” 章节。
            "max_position_embeddings": 32768,
            # RoPE 的频率基数。对维度为 d 的注意力头，第 j 个频率为： $f_j=\theta^{-2j/d}$
            # rope_theta 决定不同维度的旋转周期。
            "rope_theta": 1e6,
            # 表示输入 Embedding 和输出 lm_head 共享同一个参数矩阵
            "tie_word_embeddings": True,
            # 为 True 时构造 YaRN 配置，训练和推理共用按该配置生成的位置表。
            "inference_rope_scaling": False,
            # None表示使用原始 RoPE，不做额外频率缩放。
            "rope_scaling": None,
            # 是否是MOE模型
            "use_moe": True,
            # MOE 专家数
            "moe_num_experts": 8,
            # MOE 激活专家数
            "moe_num_experts_per_tok": 2,
            # 每一个 MoE 专家内部的 FFN 中间维度，当前也是 2432。
            "moe_intermediate_size": math.ceil(
                LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE * math.pi / 64
            )
            * 64,
            # 路由器先计算全部 moe_num_experts 个专家的 softmax 概率，再选择 Top-moe_num_experts_per_tok。
            # 设为 True 时，多专家权重归一化，Top-1 的前向权重固定为 1。
            "norm_topk_prob": True,
            # 这是每层负载均衡辅助损失的系数，控制 $a_{i,l}$ 对总训练损失的相对影响
            # 详见 “梯度累积与参数更新” 中 “MoE 的负载均衡辅助损失 $A_i$ 计算” 子章节
            "router_aux_loss_coef": 5e-4,
        },
        "loader": {
            # DataLoader 的 worker 进程数。
            "num_workers": 8,
            # 单条训练序列的长度上限，包含特殊 token。短序列补齐到该长度。Unsloth里QWen 3.8 27B默认2048，GPT-20b-oss默认1024 。
            "data_item_max_length": 2048,
            # tokenizer路径
            "tokenizer_path": "./model",
        },
        "visualization": None,
        "log": {
            # 日志打印间隔
            "step_interval": 100,
        },
    }
)

if LLM_TRAIN_SETTINGS.param.inference_rope_scaling:
    LLM_TRAIN_SETTINGS.param.rope_scaling = LLMTrainConfigureRopeScaling.model_validate(
        {
            # 快旋转分量的边界。原长度内旋转超过约 32 周的高频维度基本保持原频率，以保留局部位置分辨率。
            "beta_fast": 32,
            # 慢旋转分量的边界。原长度内旋转不足约 1 周的低频维度充分除以 factor。
            "beta_slow": 1,
            # 上下文扩展倍率 s = 16 , 充分缩放的低频分量，其频率会除以 16
            "factor": 16,
            # 扩展前的参考上下文长度,用于计算各 RoPE 维度在原长度内旋转多少周。这里与训练样本最大长度 2048 对应。
            "original_max_position_embeddings": 2048,
            # 同时缩放 RoPE 的 cos/sin，从而缩放旋转后的 Q、K；当前为 1，表示不做额外的注意力温度修正。
            "attention_factor": 1.0,
            # YaRN 缩放类型。
            "type": "yarn",
        }
    )


def is_main_process():
    return not dist.is_initialized() or dist.get_rank() == 0


def Logger(content):
    if is_main_process():
        print(content)


# 取 SGDR 的一段余弦衰减曲线，下限为 lr 的 0.1 倍。
# current_step 是窗口末尾的累计 microbatch 序号，total_steps 是训练计划的总 microbatch 数。
# SGDR: Stochastic Gradient Descent with Warm Restarts（Loshchilov & Hutter, 2017）
# lr_t = lr_min + (lr_max - lr_min) * (1 + cos(pi * x)) / 2
def get_learning_rate(current_step, total_steps, lr):
    return lr * (0.1 + 0.45 * (1 + math.cos(math.pi * current_step / total_steps)))


# 创建优化器
# Adam 项按梯度的一阶矩和二阶原始矩调整更新幅度，权重衰减独立应用于参数。
def create_optimizer(model, settings: LLMTrainConfigureAll, **kargs):
    return torch.optim.AdamW(
        model.parameters(), lr=settings.train.learning_rate, **kargs
    )


# 初始化种子
def setup_seed(seed: int):
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# 运行时配置结构
class LLMTrainRuntimeConfig(PretrainedConfig):
    model_type = LLM_TRAIN_SETTINGS.model_name

    def __init__(self, settings: LLMTrainConfigureAll | None = None, **kwargs):
        param = (settings or LLM_TRAIN_SETTINGS).param
        values = param.model_dump(
            exclude={"dtype", "eps", "moe_num_experts", "moe_num_experts_per_tok"}
        )
        values.update(
            rms_norm_eps=param.eps,
            num_experts=param.moe_num_experts,
            num_experts_per_tok=param.moe_num_experts_per_tok,
        )
        # 支持 Transformers 用序列化后的配置重新构造，不覆盖调用者传入的值。
        values.update(kwargs)
        values["head_dim"] = values["hidden_size"] // values["num_attention_heads"]

        # Transformers 5 在父类初始化时标准化 RoPE，所需长度须提前可用。
        legacy_rope = values.pop("rope_scaling", None)
        rope_parameters = dict(values.pop("rope_parameters", None) or legacy_rope or {})
        rope_parameters.setdefault("rope_type", rope_parameters.pop("type", "default"))
        rope_parameters.setdefault("rope_theta", values.pop("rope_theta"))
        self.max_position_embeddings = values["max_position_embeddings"]
        self.rope_parameters = rope_parameters
        values["rope_parameters"] = rope_parameters
        super().__init__(**values)


def lm_get_ckp_file_name(settings: LLMTrainConfigureAll, weight: LLMTrainWeightType):
    moe_path = "-moe" if settings.param.use_moe else ""
    return f"{weight.name[1:].lower()}-{settings.param.hidden_size}{moe_path}.pth"


def lm_get_ckp_resume_file_name(
    settings: LLMTrainConfigureAll, weight: LLMTrainWeightType
):
    moe_path = "-moe" if settings.param.use_moe else ""
    return (
        f"{weight.name[1:].lower()}-{settings.param.hidden_size}{moe_path}.resume.pth"
    )


def find_weight_file(directory, settings, weight, *, resume=False):
    name = (
        lm_get_ckp_resume_file_name(settings, weight)
        if resume
        else lm_get_ckp_file_name(settings, weight)
    )
    current = Path(directory) / name
    legacy_name = f"{weight.name[1:]}-{settings.param.hidden_size}{'-moe' if settings.param.use_moe else ''}"
    legacy = Path(directory) / (legacy_name + (".resume.pth" if resume else ".pth"))
    if current.is_file():
        return current
    if legacy.is_file():
        Logger(f"读取旧文件名的权重：{legacy}")
        return legacy
    raise FileNotFoundError(f"未找到文件：{current}（也已检查旧文件名 {legacy.name}）")


def sha256_file(path):
    with open(path, "rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def build_resume_metadata(settings, dataset, tokenizer):
    # 内容哈希在开始训练前计算一次；保存每个检查点时复用，不重复扫描语料。
    with tempfile.TemporaryDirectory(prefix="2613-tokenizer-") as directory:
        tokenizer.save_pretrained(directory)
        tokenizer_files = {
            path.relative_to(directory).as_posix(): sha256_file(path)
            for path in sorted(Path(directory).rglob("*"))
            if path.is_file()
        }
    return {
        "version": 2,
        "train": settings.train.model_dump(
            mode="json", exclude={"device", "from_weight"}
        ),
        "model": settings.param.model_dump(mode="json"),
        "loader": {
            "data_item_max_length": dataset.max_length,
            "num_workers": settings.loader.num_workers,
        },
        "device_type": torch.device(settings.train.device).type,
        "dataset": {
            "files": dataset.source_fingerprint,
            "rows": len(dataset),
            "processing": dataset.processing_config,
        },
        "tokenizer": tokenizer_files,
    }


def validate_resume_metadata(checkpoint, expected):
    saved = checkpoint.get("resume_metadata")
    if saved is None:
        raise ValueError(
            "旧检查点缺少完整续训信息，无法核对模型、精度、数据及 tokenizer；请通过 train.from_weight 加载对应导出权重，开始新训练。"
        )
    changed = sorted(
        key
        for key in saved.keys() | expected.keys()
        if saved.get(key) != expected.get(key)
    )
    if changed:
        raise ValueError(
            f"续训配置或输入内容与检查点不一致：{', '.join(changed)}；请恢复原配置与数据，或从权重开始新训练。"
        )


def capture_rng_state(device):
    device = torch.device(device)
    numpy_state = numpy.random.get_state()
    return {
        "python": random.getstate(),
        "numpy": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
        "torch": torch.get_rng_state(),
        "cuda": (
            torch.cuda.get_rng_state(device=device) if device.type == "cuda" else None
        ),
    }


def restore_rng_state(state, device):
    device = torch.device(device)
    if (state["cuda"] is not None) != (device.type == "cuda"):
        raise ValueError("随机数状态的设备类型与当前训练设备不一致")
    random.setstate(state["python"])
    numpy_state = state["numpy"]
    numpy.random.set_state(
        (
            numpy_state[0],
            numpy.array(numpy_state[1], dtype=numpy.uint32),
            *numpy_state[2:],
        )
    )
    torch.set_rng_state(state["torch"])
    if device.type == "cuda":
        torch.cuda.set_rng_state(state["cuda"], device=device)


# 读取或保存检查点
def lm_checkpoint(
    settings: LLMTrainConfigureAll,
    model=None,
    optimizer=None,
    epoch=0,
    step=0,
    wandb=None,
    *,
    resume_metadata,
    **kwargs,
):
    save_dir = f"{settings.save.dir}/checkpoint"
    os.makedirs(save_dir, exist_ok=True)
    ckp_path = f"{save_dir}/{lm_get_ckp_file_name(settings, settings.save.save_weight)}"
    resume_path = (
        f"{save_dir}/{lm_get_ckp_resume_file_name(settings, settings.save.save_weight)}"
    )

    if model is not None:
        # 所有 rank 都参与收集；只由主进程写文件。
        rng_states = [capture_rng_state(settings.train.device)]
        if dist.is_initialized():
            local_rng_state = rng_states[0]
            rng_states = [None] * dist.get_world_size()
            dist.all_gather_object(rng_states, local_rng_state)
        if not is_main_process():
            return
        raw_model = (
            model.module if isinstance(model, DistributedDataParallel) else model
        )
        raw_model = getattr(raw_model, "_orig_mod", raw_model)
        state_dict = raw_model.state_dict()
        state_dict = {k: v.detach().cpu() for k, v in state_dict.items()}
        ckp_tmp = ckp_path + ".tmp"
        torch.save(
            {
                k: v.half() if v.is_floating_point() else v
                for k, v in state_dict.items()
            },
            ckp_tmp,
        )
        os.replace(ckp_tmp, ckp_path)
        wandb_id = None
        if wandb:
            if hasattr(wandb, "get_run"):
                run = wandb.get_run()
                wandb_id = getattr(run, "id", None) if run else None
            else:
                wandb_id = getattr(wandb, "id", None)

        resume_data = {
            "model": state_dict,
            "optimizer": optimizer.state_dict(),
            "epoch": epoch,
            "step": step,
            "world_size": dist.get_world_size() if dist.is_initialized() else 1,
            "wandb_id": wandb_id,
            "rng_states": rng_states,
            "resume_metadata": resume_metadata,
        }
        for key, value in kwargs.items():
            if value is not None:
                if hasattr(value, "state_dict"):
                    raw_value = (
                        value.module
                        if isinstance(value, DistributedDataParallel)
                        else value
                    )
                    raw_value = getattr(raw_value, "_orig_mod", raw_value)
                    resume_data[key] = raw_value.state_dict()
                else:
                    resume_data[key] = value

        resume_tmp = resume_path + ".tmp"
        torch.save(resume_data, resume_tmp)
        os.replace(resume_tmp, resume_path)
        del state_dict, resume_data
        torch.cuda.empty_cache()
    else:  # 加载模式
        resume_path = find_weight_file(
            save_dir, settings, settings.save.save_weight, resume=True
        )
        ckp_data = torch.load(resume_path, map_location="cpu", weights_only=True)
        saved_ws = ckp_data.get("world_size", 1)
        current_ws = dist.get_world_size() if dist.is_initialized() else 1
        if saved_ws != current_ws:
            raise ValueError(
                f"续训要求 world_size 保持一致（保存值 {saved_ws}，当前值 {current_ws}）；改变 GPU 数量请从模型权重开始新训练。"
            )
        validate_resume_metadata(ckp_data, resume_metadata)
        if len(ckp_data.get("rng_states", [])) != current_ws:
            raise ValueError("检查点缺少各 rank 的随机数状态，无法续训")
        return ckp_data


# ==================================== 模型内容部分 ====================================


# 均方根归一化
class RMSNorm(torch.nn.Module):
    def __init__(self, dim: int, eps: float = LLM_TRAIN_SETTINGS.param.eps):
        super().__init__()
        self.eps = eps
        # 把weight变成可训练参数
        self.weight = torch.nn.Parameter(torch.ones(dim))

    def norm(self, x):
        # x.pow(2) 逐元素平方。mean(-1) 沿最后一维取均值，每个 token 得到一个值。
        # 对形状为 (B, T, D) 的 x，keepdim=True 让结果为 (B, T, 1)，可以沿特征维广播到 x。
        # 数据举例
        #    x = [[[1, 2, 3],      ← token A，坐标 (b=0, s=0)
        #        [4, 5, 6]]]       ← token B，坐标 (b=0, s=1)
        #    x.pow(2):
        #    token A: [1, 4, 9]      → 喂给 token A 自己的均值 (1+4+9)/3
        #    token B: [16, 25, 36]   → 喂给 token B 自己的均值 (16+25+36)/3
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x):
        return (self.weight * self.norm(x.float())).type_as(x)


def precompute_freqs_cis(
    dim: int,
    end: int = int(32 * 1024),
    rope_base: float = 1e6,
    rope_scaling: dict = None,
):
    freqs, attn_factor = (
        1.0 / (rope_base ** (torch.arange(0, dim, 2)[: (dim // 2)].float() / dim)),
        1.0,
    )
    if (
        rope_scaling is not None
        and rope_scaling.get("rope_type", rope_scaling.get("type", "yarn")) == "yarn"
    ):  # YaRN: f'(i) = f(i)((1-γ) + γ/s), where γ∈[0,1] is linear ramp
        orig_max, factor, beta_fast, beta_slow, attn_factor = (
            rope_scaling.get("original_max_position_embeddings", 2048),
            rope_scaling.get("factor", 16),
            rope_scaling.get("beta_fast", 32.0),
            rope_scaling.get("beta_slow", 1.0),
            rope_scaling.get("attention_factor", 1.0),
        )
        if end / orig_max > 1.0:
            inv_dim = lambda b: (dim * math.log(orig_max / (b * 2 * math.pi))) / (
                2 * math.log(rope_base)
            )
            low, high = max(math.floor(inv_dim(beta_fast)), 0), min(
                math.ceil(inv_dim(beta_slow)), dim // 2 - 1
            )
            ramp = torch.clamp(
                (torch.arange(dim // 2, device=freqs.device).float() - low)
                / max(high - low, 0.001),
                0,
                1,
            )
            freqs = freqs * (1 - ramp + ramp / factor)
    t = torch.arange(end, device=freqs.device)
    freqs = torch.outer(t, freqs).float()
    freqs_cos = torch.cat([torch.cos(freqs), torch.cos(freqs)], dim=-1) * attn_factor
    freqs_sin = torch.cat([torch.sin(freqs), torch.sin(freqs)], dim=-1) * attn_factor
    return freqs_cos, freqs_sin


# 这里的Position Embedding的混入流程和经典 Transformer 的位置编码有所差异。
# 这里采用的是 RoPE 的方法，详见 “RoPE: Rotary Position Embedding，旋转位置编码” 章节。
def apply_rotary_pos_emb(q, k, cos, sin, unsqueeze_dim=1):
    def rotate_half(x):
        return torch.cat(
            (-x[..., x.shape[-1] // 2 :], x[..., : x.shape[-1] // 2]), dim=-1
        )

    q_embed = (
        (q * cos.unsqueeze(unsqueeze_dim))
        + (rotate_half(q) * sin.unsqueeze(unsqueeze_dim))
    ).to(q.dtype)
    k_embed = (
        (k * cos.unsqueeze(unsqueeze_dim))
        + (rotate_half(k) * sin.unsqueeze(unsqueeze_dim))
    ).to(k.dtype)
    return q_embed, k_embed


def repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    bs, slen, num_key_value_heads, head_dim = x.shape
    if n_rep == 1:
        return x
    return (
        x[:, :, :, None, :]
        .expand(bs, slen, num_key_value_heads, n_rep, head_dim)
        .reshape(bs, slen, num_key_value_heads * n_rep, head_dim)
    )


class Attention(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig, layer_idx: int = None):
        super().__init__()
        self.layer_idx = layer_idx

        # 默认使用 GQA，由一组 Q 头共享一对 Key/Value 头。
        self.num_key_value_heads = (
            config.num_attention_heads
            if config.num_key_value_heads is None
            else config.num_key_value_heads
        )

        self.n_local_heads = config.num_attention_heads
        self.n_local_kv_heads = self.num_key_value_heads

        # 几个Q共享一个K/V头。
        self.n_rep = self.n_local_heads // self.n_local_kv_heads

        # 每个头的注意力
        self.head_dim = config.head_dim

        # 标记本层是否是因果注意力
        self.is_causal = True

        # Q矩阵
        self.q_proj = torch.nn.Linear(
            config.hidden_size, config.num_attention_heads * self.head_dim, bias=False
        )

        # K矩阵
        self.k_proj = torch.nn.Linear(
            config.hidden_size, self.num_key_value_heads * self.head_dim, bias=False
        )

        # V矩阵
        self.v_proj = torch.nn.Linear(
            config.hidden_size, self.num_key_value_heads * self.head_dim, bias=False
        )

        # O矩阵/输出矩阵
        self.o_proj = torch.nn.Linear(
            config.num_attention_heads * self.head_dim, config.hidden_size, bias=False
        )

        # 分别沿 Q 和 Key 的头维度做 RMSNorm。
        self.q_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        self.k_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        self.attn_dropout = torch.nn.Dropout(config.dropout)
        self.resid_dropout = torch.nn.Dropout(config.dropout)
        self.dropout = config.dropout
        self.flash = (
            hasattr(torch.nn.functional, "scaled_dot_product_attention")
            and config.flash_attn
        )

    def forward(
        self,
        x,
        position_embeddings,
        past_key_value=None,
        use_cache=False,
        attention_mask=None,
    ):
        # x的形状 (batch_size, seq_len, hidden_size)
        bsz, seq_len, _ = x.shape
        xq, xk, xv = self.q_proj(x), self.k_proj(x), self.v_proj(x)

        # view 将投影的最后一维拆成 (头数, 每头维度)，得到 (B, T, 头数, 每头维度)。
        xq = xq.view(bsz, seq_len, self.n_local_heads, self.head_dim)
        xk = xk.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
        xv = xv.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
        xq, xk = self.q_norm(xq), self.k_norm(xk)
        cos, sin = position_embeddings

        # 附加Position Embedding
        xq, xk = apply_rotary_pos_emb(xq, xk, cos, sin)
        # 旧缓存是本层的 (K, V) 对，形状为 (B, T_cached, H_kv, D)。新 K/V 沿序列维接到历史之后。
        if isinstance(past_key_value, Cache):
            # transformers 5.x Cache（如 DynamicCache）期望 (B, heads, seq, head_dim) 布局，
            # update 沿 seq 维追加并返回完整 K/V；缓存本体就地更新，无需逐层返回
            keys, values = past_key_value.update(
                # transpose(1, 2)： 交换第1和第2维
                # (B, T, H, D) → (B, H, T, D)
                xk.transpose(1, 2),
                xv.transpose(1, 2),
                self.layer_idx,
            )
            # 更新完缓存后转回来
            xk, xv = keys.transpose(1, 2), values.transpose(1, 2)
            past_kv = None
        else:
            if past_key_value is not None:
                xk = torch.cat([past_key_value[0], xk], dim=1)
                xv = torch.cat([past_key_value[1], xv], dim=1)
            past_kv = (xk, xv) if use_cache else None

        # (B, T, H, D) → (B, H, T, D)
        xq, xk, xv = (
            xq.transpose(1, 2),
            repeat_kv(xk, self.n_rep).transpose(1, 2),  # K矩阵共享,对齐维度
            repeat_kv(xv, self.n_rep).transpose(1, 2),  # V矩阵共享,对齐维度
        )
        if (
            self.flash
            and (seq_len > 1)
            and (not self.is_causal or past_key_value is None)
        ):
            sdpa_mask = None
            # attention_mask 是 (B, T_kv) 的二维张量——每个元素标记对应 key 位置是否真实（1 真实 / 0 padding）。
            if attention_mask is not None and not torch.all(attention_mask == 1):
                # 这里 sdpa_mask的操作和下面的 attention_mask.unsqueeze(1).unsqueeze(2) 的操作是一样的
                sdpa_mask = attention_mask[:, None, None, :].bool()
                if self.is_causal:
                    # torch.tril(input, diagonal=0)   # 保留下三角：col − row ≤ diagonal 的元素，其余清零
                    # tril(): 只保留下三角（含对角线），即第 i 个 token 只能看到 <= i 的 token
                    causal_mask = torch.ones(
                        seq_len, seq_len, dtype=torch.bool, device=x.device
                    ).tril()
                    sdpa_mask = sdpa_mask & causal_mask
            # SDPA = Scaled Dot Product Attention，缩放点积注意力:
            # - scaled_dot_product_attention 是PyTorch标准注意力的封装。
            # - SDPA 是多后端调度器,满足特定条件（比如CUDA + bf16 + 常规形状)可能会用 FlashAttention(https://owent.net/2026/2611.html#flashattention)
            output = torch.nn.functional.scaled_dot_product_attention(
                xq,
                xk,
                xv,
                attn_mask=sdpa_mask,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=self.is_causal and sdpa_mask is None,
            )
        else:
            # @是矩阵乘法: $Q K^{\top}$
            scores = (xq @ xk.transpose(-2, -1)).float() / math.sqrt(self.head_dim)
            # scores 的形状是 (B, H, T_q, T_kv)
            if self.is_causal:
                # 缓存场景下 T_kv 可能长于 T_q，只对最后 seq_len 个 key 做因果上三角掩码。
                # torch.triu(input, diagonal=0)   # 保留上三角：col − row ≥ diagonal 的元素，其余清零
                # IEEE 754 规则: 有限值 + (-inf) = -inf
                scores[:, :, :, -seq_len:] += torch.full(
                    (seq_len, seq_len), float("-inf"), device=scores.device
                ).triu(1)
            # attention_mask 是 (B, T_kv) 的二维张量——每个元素标记对应 key 位置是否真实（1 真实 / 0 padding）。
            #   attention_mask.unsqueeze(1).unsqueeze(2) -> 插入2次维度。 -> (B, 1, 1, T_kv)
            # 加法会触发右对齐（复制/广播）：(B, 1, 1, T_kv) 与 (B, H, T_q, T_kv) 相加时，
            #   维度为 1 的轴会被广播展开（size 1 → 目标 size），尾部维度 T_kv 对齐不变。
            # (1.0 - attention_mask) * -1e9：真实位置得 0，padding 位置得 -1e9，
            #   softmax 对每一行的分数减去该行最大值后取指数。存在可见的真实位置时，
            #   padding 位置的分数相对低约 1e9，指数项在浮点运算中下溢为 0。
            if attention_mask is not None:
                scores += (
                    1.0 - attention_mask.unsqueeze(1).unsqueeze(2).to(scores.dtype)
                ) * -1e9
            # 注意力算法，softmax后再乘V矩阵，结果形状为 (B, H, T_q, D)
            output = (
                self.attn_dropout(
                    torch.nn.functional.softmax(scores, dim=-1).type_as(xq)
                )
                @ xv
            )
        # 先转回 (B, T, H, D) 结构，再reshape相当于把多头再cat到一起。
        output = output.transpose(1, 2).reshape(bsz, seq_len, -1)

        # 最后的输出投影矩阵的作用是维度衔接（num_attention_heads*head_dim并不总是等于hidden_size）和跨头信息混合。
        output = self.resid_dropout(self.o_proj(output))
        return output, past_kv


class FeedForward(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig, intermediate_size: int = None):
        super().__init__()
        intermediate_size = intermediate_size or config.intermediate_size
        self.gate_proj = torch.nn.Linear(
            config.hidden_size, intermediate_size, bias=False
        )
        self.down_proj = torch.nn.Linear(
            intermediate_size, config.hidden_size, bias=False
        )
        self.up_proj = torch.nn.Linear(
            config.hidden_size, intermediate_size, bias=False
        )
        # 使用配置的激活函数
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, x):
        # 输入 x 的形状为 (B, T, hidden_size)。
        # 1. gate_proj 和 up_proj 分别对每个 token 做线性投影，得到两个 (B, T, intermediate_size) 张量。
        # 2. act_fn 逐元素作用于 gate_proj 的输出。默认 SiLU 的输出可以为负，也可以大于 1。
        # 3. 这里的 * 是逐元素乘（⊙），用门控分支的各分量缩放 up_proj 的对应分量，形状不变。
        # 4. down_proj 将乘积投影回 (B, T, hidden_size)，供残差连接使用。
        return self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))


class MOEFeedForward(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.config = config

        # 路由器用无偏置线性层计算各专家的 logits，即 $xW^{\top}$。
        self.gate = torch.nn.Linear(config.hidden_size, config.num_experts, bias=False)

        # 创建 num_experts 个独立的 FFN，每个专家的中间维度为 moe_intermediate_size。
        self.experts = torch.nn.ModuleList(
            [
                FeedForward(config, intermediate_size=config.moe_intermediate_size)
                for _ in range(config.num_experts)
            ]
        )

        # 使用配置的激活函数
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, x, token_mask=None):
        batch_size, seq_len, hidden_dim = x.shape
        # 搞扁平 (batch_size*seq_len, hidden_dim)
        x_flat = x.view(-1, hidden_dim)

        # 对全部专家的 logits 做 softmax，得到路由概率，用于 Top-k 选择和负载统计。
        scores = torch.nn.functional.softmax(self.gate(x_flat), dim=-1)

        # topk_weight, topk_idx的形状是  (batch_size*seq_len, num_experts_per_tok)
        topk_weight, topk_idx = torch.topk(
            scores, k=self.config.num_experts_per_tok, dim=-1, sorted=False
        )
        if self.config.norm_topk_prob:
            # 归一化
            if self.config.num_experts_per_tok > 1:
                topk_weight = topk_weight / (
                    topk_weight.sum(dim=-1, keepdim=True) + 1e-20
                )
            else:
                # t.detach() 的含义是返回一个与 t 共享同一块数据的新张量，requires_grad=False、无 grad_fn——从计算图上"摘下来"
                #            不拷贝数据。相当于冻结某个值当常数用。
                # 如果没有这一层，只激活一个专家时，求导过程会变成:
                #   topk_weight = topk(scores, k=1)[0] / topk(scores, k=1)[0].sum(-1, keepdim=True)
                #               = p / p = 1.0，主损失通过这个权重传给路由器的梯度为零,学不到路由对错。
                top1 = torch.topk(
                    # x_flat.detach(): 这里阻断对x_flat的反向传播
                    # 这里是 STE（Straight-Through Estimator，直通估计器） 的产物。
                    #   STE 解决的问题是： 反向传播要求每个操作可微。反传时用的梯度不是前向函数的真实导数。
                    torch.nn.functional.softmax(self.gate(x_flat.detach()), dim=-1),
                    k=1,
                    dim=-1,
                    sorted=False,
                )[0]
                topk_weight = (
                    # 设置为 1.0, 但保持一份梯度（直接 top1 - top1 就消除了）
                    top1
                    - top1.detach()
                    + 1.0
                )  # k=1: 1.0 forward on purpose, gradient via straight-through
        y = torch.zeros_like(x_flat)
        for i, expert in enumerate(self.experts):
            # 逐元素比较，mask形状 (batch_size*seq_len, num_experts_per_tok)
            # 表示这个专家被用到的位置
            mask = topk_idx == i
            if mask.any():
                # 专家选中。当前专家在某个token的任意一个专家候选里则当前专家被选中。
                # nonzero返回的是下标。数据示例如下:
                #   topk_idx (N=6, 2)        mask = topk_idx == 1   (N, 2) bool
                #   token0: [1, 4]           [[T, F],                token0 选了专家 1
                #   token1: [0, 2]            [F, F],
                #   token2: [1, 3]            [T, F],
                #   token3: [5, 6]            [F, F],
                #   token4: [1, 2]            [T, F],
                #   token5: [0, 1]]           [F, T]]
                #
                #   ① mask.any(dim=-1)  →  [T, F, T, F, T, T]        (N,)
                #      "沿候选维(any)看：该 token 的两个候选里有没有专家 1"
                #
                #   ② .nonzero()        →  [[0], [2], [4], [5]]      (4, 1)
                #      "True 元素所在的位置下标"——一维张量里，位置下标 == 行号
                #
                #   ③ .flatten()        →  [0, 2, 4, 5]              (4,)
                #      拍平成行号列表 = 选了专家 1 的 token 编号
                token_idx = mask.any(dim=-1).nonzero().flatten()
                # A[B] 是布尔索引。A、B 形状相同时，返回 A 中 B 为 True 的位置组成的一维张量。
                # 每行至多有一个 True，所以 topk_weight[mask] 的顺序与上面的 token_idx 一致。
                # view(-1, 1) 将权重变成 (选中的 token 数, 1)，乘法时沿专家输出的特征维广播。
                #   如果两个张量A: (N, M) float，B: (N, M) bool 。A[B] 的操作是超出所有位置B为True的A的值。
                #   因为候选专家一定是不重复的，所以mask的最后一维必定只有一个值为True。
                weight = topk_weight[mask].view(-1, 1)
                y.index_add_(
                    # x_flat[token_idx] 取出本批次分给该专家的所有 token。index_add_ 沿第 0 维原地累加，
                    # 把加权输出的第 j 行加到 y[token_idx[j]]，同一个 token 可累加多个专家的输出。
                    0,
                    token_idx,
                    (expert(x_flat[token_idx]) * weight).to(y.dtype),
                )
            elif self.training:
                # 用零贡献把未被选中的专家接入计算图，使默认 DDP 仍能归约其零梯度。
                y[0, 0] += 0 * sum(p.sum() for p in expert.parameters())

        # 详见 “梯度累积与参数更新” 中 “MoE 的负载均衡辅助损失 $A_i$ 计算” 子章节
        if self.training and self.config.router_aux_loss_coef > 0:
            valid = (
                # reshape(-1) 是把 (batch_size, seq_len) 拉平，降低一维。
                token_mask.reshape(-1).bool()
                if token_mask is not None
                else torch.ones(batch_size * seq_len, dtype=torch.bool, device=x.device)
            )
            if valid.any():
                # load 的形状: (num_experts_per_tok, num_experts)
                load = (
                    # 把最后一维的下标向量转成one-hot向量（即对应位置填1，其他填0）。
                    # 数据类型是int64，会增加一维。
                    torch.nn.functional.one_hot(
                        topk_idx[valid], self.config.num_experts
                    )
                    .float()  # 然后转float方便求平均
                    .sum(0)
                    / topk_idx[valid].numel()  # 是元素总数。相当于公式里的 M * k。
                    # 沿 Top-k 槽位求和后得到公式中的每专家选择比例 $f_e$。
                )
                # 这里的aux_loss就是 文章公式里的 $a_{layer}$ 。
                self.aux_loss = (
                    # scores[valid].mean(0) 就是公式里的 p̄ ,形状为 (8)。
                    # load * scores[valid].mean(0)时会先把 scores[valid].mean(0) 广播右对齐。
                    # 比如:
                    #   load[0]: [l00, l01, l02, ..., l07]      p̄: [p0, p1, ..., p7]
                    #   load[1]: [l10, l11, ..., l17]
                    #
                    #   乘积 = [[l00·p0, l01·p1, ..., l07·p7],     ← 槽 1 每个专家 × 同一个 p̄
                    #           [l10·p0, l11·p1, ..., l17·p7]]     ← 槽 2 每个专家 × 同一个 p̄
                    (load * scores[valid].mean(0)).sum()
                    * self.config.num_experts
                    * self.config.router_aux_loss_coef
                )
            else:
                # 这个 microbatch 没有非 padding token。但是要让反向传播的图覆盖到，保证有梯度信息，所以手动设置零。
                self.aux_loss = scores.sum() * 0.0
        else:
            # 推理时不消费这个，只用专家权重topk_weight。所以这里设置为0即可。
            self.aux_loss = scores.new_zeros(1).squeeze()

        # 转换回和输入一样的形状
        return y.view(batch_size, seq_len, hidden_dim)


# 单层 Transformer 解码块
class OWenTLLMBlock(torch.nn.Module):
    def __init__(self, layer_id: int, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.self_attn = Attention(config, layer_idx=layer_id)
        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(
            config.hidden_size, eps=config.rms_norm_eps
        )
        self.mlp = FeedForward(config) if not config.use_moe else MOEFeedForward(config)

    def forward(
        self,
        hidden_states,
        position_embeddings,
        past_key_value=None,
        use_cache=False,
        attention_mask=None,
    ):
        # hidden_states形状 (B, T, hidden_size)
        residual = hidden_states
        # 注意力计算
        hidden_states, present_key_value = self.self_attn(
            self.input_layernorm(hidden_states),
            position_embeddings,
            past_key_value,
            use_cache,
            attention_mask,
        )

        # 残差连接
        hidden_states += residual

        # 再归一化
        mlp_input = self.post_attention_layernorm(hidden_states)

        # FFN前馈网络
        if isinstance(self.mlp, MOEFeedForward):
            # attention_mask 包含全部历史，MoE 辅助损失只需要统计本次前向的部分
            token_mask = (
                attention_mask[:, -hidden_states.shape[1] :]
                if attention_mask is not None
                else None
            )
            mlp_output = self.mlp(mlp_input, token_mask=token_mask)
        else:
            mlp_output = self.mlp(mlp_input)

        # 继续残差连接FFN的结果
        hidden_states = hidden_states + mlp_output
        return hidden_states, present_key_value


# 主干网络
class OWenTLLMModel(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.config = config
        self.vocab_size, self.num_hidden_layers = (
            config.vocab_size,
            config.num_hidden_layers,
        )
        # 随机初始化后训练Word Embedding
        self.embed_tokens = torch.nn.Embedding(config.vocab_size, config.hidden_size)
        self.dropout = torch.nn.Dropout(config.dropout)

        # 创建 num_hidden_layers 个参数独立的 Decoder Block。
        self.layers = torch.nn.ModuleList(
            [OWenTLLMBlock(l, config) for l in range(self.num_hidden_layers)]
        )

        # 所有 Decoder Block 之后的 RMSNorm。
        self.norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)

        # 位置嵌入
        freqs_cos, freqs_sin = precompute_freqs_cis(
            dim=config.head_dim,
            end=config.max_position_embeddings,
            rope_base=config.rope_parameters["rope_theta"],
            rope_scaling=config.rope_parameters,
        )

        # 数据注册到缓存，不需要更新但要跟着设备迁移
        self.register_buffer("freqs_cos", freqs_cos, persistent=False)
        self.register_buffer("freqs_sin", freqs_sin, persistent=False)

    def forward(
        self,
        input_ids,
        attention_mask=None,
        past_key_values=None,
        use_cache=False,
        **kwargs,
    ):
        batch_size, seq_length = input_ids.shape
        # 并行支持两种缓存格式：transformers 5.x 的 Cache 类对象（如 DynamicCache）
        # 与旧版 list[(K, V)] 元组（每层一个 (K, V)，K/V 形状 (B, T_cached, 4, 96)）
        is_hf_cache = isinstance(past_key_values, Cache)
        if is_hf_cache:
            # Cache 对象由各层 Attention 调 update 就地更新，已处理长度从缓存读取；
            # 每层拿到同一个 Cache 对象，靠 layer_idx 区分各层的 K/V
            start_pos = past_key_values.get_seq_length()
            layer_caches = [past_key_values] * len(self.layers)
        else:
            past_key_values = past_key_values or [None] * len(self.layers)
            start_pos = (
                past_key_values[0][0].shape[1] if past_key_values[0] is not None else 0
            )
            layer_caches = past_key_values
        hidden_states = self.dropout(self.embed_tokens(input_ids))
        # Recompute RoPE buffers lost during meta-device init (transformers>=5.x)
        # register_buffer设置了persistent=False非持久化，如果丢失了就重建
        if self.freqs_cos[0, 0] == 0:
            freqs_cos, freqs_sin = precompute_freqs_cis(
                dim=self.config.head_dim,
                end=self.config.max_position_embeddings,
                rope_base=self.config.rope_parameters["rope_theta"],
                rope_scaling=self.config.rope_parameters,
            )
            self.freqs_cos, self.freqs_sin = freqs_cos.to(
                hidden_states.device
            ), freqs_sin.to(hidden_states.device)

        # 位置权重
        position_embeddings = (
            self.freqs_cos[start_pos : start_pos + seq_length],
            self.freqs_sin[start_pos : start_pos + seq_length],
        )
        presents = []
        for layer, past_key_value in zip(self.layers, layer_caches):
            # 按隐藏层依次计算,present是本层的K/V Cache
            hidden_states, present = layer(
                hidden_states,
                position_embeddings,
                past_key_value=past_key_value,
                use_cache=use_cache,
                attention_mask=attention_mask,
            )
            presents.append(present)
        # 归一化
        hidden_states = self.norm(hidden_states)
        # 参数更新公式中的 $A_i$ ，所有层的 aux_loss 和。详见 “梯度累积与参数更新” 中 “MoE 的负载均衡辅助损失 $A_i$ 计算” 子章节
        aux_loss = sum(
            [l.mlp.aux_loss for l in self.layers if isinstance(l.mlp, MOEFeedForward)],
            hidden_states.new_zeros(1).squeeze(),
        )
        return hidden_states, (past_key_values if is_hf_cache else presents), aux_loss


# 完整模型
# HuggingFace Transformers 生态的标准双层模式
# - 外层 OWenTLLMForCausalLM：负责任务头 + 训练/生成接口
# - 里层OWenTLLMModel(纯 Transformer 主干): 负责“token ID → 隐藏状态”的表征计算
class OWenTLLMForCausalLM(PreTrainedModel, GenerationMixin):
    config_class = LLMTrainRuntimeConfig
    _tied_weights_keys = {"lm_head.weight": "model.embed_tokens.weight"}

    def __init__(self, config: LLMTrainRuntimeConfig = None):
        self.config = config or LLMTrainRuntimeConfig(LLM_TRAIN_SETTINGS)
        super().__init__(self.config)
        self.model = OWenTLLMModel(self.config)

        # 输出嵌入(Output Embedding)
        #   nn.Linear(in_features, out_features) 线性变换的两个参数不是权重矩阵的形状。
        #     构造参数是 (输入维, 输出维)
        #   $y = x \dot W^{\top}$
        self.lm_head = torch.nn.Linear(
            self.config.hidden_size, self.config.vocab_size, bias=False
        )

        # 输入嵌入(Word Embedding)和输出嵌入(Output Embedding)使用相同的
        if self.config.tie_word_embeddings:
            self.model.embed_tokens.weight = self.lm_head.weight
        self.post_init()

    def forward(
        self,
        input_ids,
        attention_mask=None,
        past_key_values=None,
        use_cache=False,
        logits_to_keep=0,
        labels=None,
        loss_reduction="mean",
        **kwargs,
    ):
        # 返回 (隐藏层矩阵, K/V缓存, MoE 的负载均衡辅助损失 $A_i$)
        # hidden_states 形状 (batch, seq_len, hidden_size) = (B, T, 768) 的三维浮点张量。
        #                     第 0 维 batch、第 1 维序列位置、第 2 维每个位置的特征向量。
        #                     seq_len 对应输入 input_ids 的位置。
        hidden_states, past_key_values, aux_loss = self.model(
            input_ids, attention_mask, past_key_values, use_cache, **kwargs
        )

        # 最后 logits_to_keep 个序列位置才做 lm_head 投影，其余位置的 logits 干脆不算。
        # 训练入口用默认值 0，计算全部 logits。逐 token 生成时只消费最后一个位置的 logits。
        slice_indices = (
            slice(-logits_to_keep, None)
            if isinstance(logits_to_keep, int)
            else logits_to_keep
        )

        # (B, T', hidden_size) -> (B, T', vocab_size))
        logits = self.lm_head(hidden_states[:, slice_indices, :])
        loss = None
        # labels的形状是 (B, T)
        if labels is not None:
            # labels 与 logits 同窗错位：logits 的槽位 t 预测原序列 t+1 处的 token。
            # logits_to_keep=0 时窗口为全量，等价于原先的 labels[..., 1:]；
            # logits_to_keep>0 时若不同步切片，x 的行数 B*(k-1) 与 y 的行数 B*(T-1)
            # 不相等，cross_entropy 会直接报 batch_size 不匹配。
            if isinstance(logits_to_keep, int):
                y = labels[..., slice_indices][..., 1:]
            else:
                # 张量索引形式：槽位是前 k-1 个被保留位置，目标取各自 +1 处
                y = labels[..., logits_to_keep[:-1] + 1]
            # 连续布局 (contiguous) 的含义：如果张量的内存布局与逻辑形状一致，原样返回；
            #   否则新分配一块内存，把数据按逻辑顺序重新排布一份副本。
            #   它不改变形状和数值，改变的只是“数值在内存里摆放的顺序”。
            #   逻辑形状:            [[a, b, c],
            #                        [d, e, f]]
            #   连续布局 (contiguous): 内存 abcdef，strides=(3, 1)
            #                         → 元素(i,j) 在偏移 i*3 + j 处
            x, y = logits[..., :-1, :].contiguous(), y.contiguous()

            # cross_entropy 行为，对每一行
            # ① softmax 归一化：  p_j = exp(x_{n,j}) / Σ_j exp(x_{n,j})
            # ② 取正确答案的概率：p = p_{y_n}     （y_n = 该位置真实 token 的 ID）
            # ③ 取负对数：        ℓ_n = -log(p)
            # 跳过 ignore_index 标签，再按 reduction 聚合。当前训练上层传入的参数是求和。
            loss = torch.nn.functional.cross_entropy(
                x.view(
                    -1, x.size(-1)
                ),  # x 拉平到二维，最后一维使用 x.size(-1)，第一维自动计算（B*(T'-1)）
                y.view(-1),  # y 强制拉平到一维（B*(T'-1)）
                ignore_index=PYTORCH_IGNORE_INDEX,
                reduction=loss_reduction,
            )

        # 打包结果返回
        return MoeCausalLMOutputWithPast(
            loss=loss,
            aux_loss=aux_loss,
            logits=logits,
            past_key_values=past_key_values,
            hidden_states=hidden_states,
        )

    # 自回归解码循环：把训练学到的“单步预测下一个 token”能力，迭代成一段完整的回复。
    # 此接口给推理使用，训练时不使用
    # https://github.com/jingyaogong/minimind/discussions/611
    @torch.inference_mode()
    def generate(
        self,
        inputs=None,
        attention_mask=None,
        max_new_tokens=8192,
        temperature=0.85,
        top_p=0.85,
        top_k=50,
        eos_token_id=2,
        streamer=None,
        use_cache=True,
        num_return_sequences=1,
        do_sample=True,
        repetition_penalty=1.0,
        **kwargs,
    ):
        # 调用方可能用两种风格传 prompt：
        # - model.generate(inputs=prompt_ids)
        # - model.generate(input_ids=prompt_ids)
        # 这里复制 num_return_sequences 次以生成多条候选
        input_ids = kwargs.pop("input_ids", inputs).repeat(num_return_sequences, 1)
        attention_mask = (
            attention_mask.repeat(num_return_sequences, 1)
            if attention_mask is not None
            else None
        )

        # 每层算出来的K/V历史，也是KV Cache 的载体。结构如下
        # past_key_values               : list，长度 = 层数（8 层，每层一份）
        # ├─ [0]  → (K₀, V₀)            第 1 层的缓存
        # │    ├─ [0] → K₀ : (B, T_cached, 4, 96)   ← past_key_values[0][0]
        # │    └─ [1] → V₀ : (B, T_cached, 4, 96)
        # ├─ [1]  → (K₁, V₁)            第 2 层
        # │    ...
        # └─ [7]  → (K₇, V₇)            第 8 层
        # T_cached = 已经处理过的 token 总数（prompt + 已生成部分）
        # 4 = num_key_value_heads（GQA），96 = head_dim
        # 也支持传入 transformers 5.x 的 Cache 对象（如 DynamicCache）：
        # K/V 改存为 (B, heads, seq, head_dim)，由各层 Attention 调 update 就地维护
        past_key_values = kwargs.pop("past_key_values", None)

        # input_ids                     : (B, T_total)
        #                         B = 输入 batch 大小 × num_return_sequences
        #                         T_total = prompt 长度 + 已生成的 token 数
        finished = torch.zeros(
            input_ids.shape[0], dtype=torch.bool, device=input_ids.device
        )

        # 先把 prompt 输入推给消费流（UI上先显示出问题）
        # .cpu() 是 PyTorch 张量的设备迁移方法：把张量从它当前所在的设备（GPU 显存）复制到主机内存（CPU RAM），返回一个位于 CPU 的新张量。
        if streamer:
            streamer.put(input_ids.cpu())
        for _ in range(max_new_tokens):
            past_len = (
                past_key_values.get_seq_length()
                if isinstance(past_key_values, Cache)
                else (past_key_values[0][0].shape[1] if past_key_values else 0)
            )
            outputs = self.forward(
                input_ids[:, past_len:],
                attention_mask,
                past_key_values,
                use_cache=use_cache,
                **kwargs,
            )
            # 每生成一个token， input_ids会增加一个，mask也要增加一个
            # 使用 attention_mask.new_ones 是为了保持和原掩码同 dtype、同设备
            attention_mask = (
                torch.cat(
                    [
                        attention_mask,
                        attention_mask.new_ones(attention_mask.shape[0], 1),
                    ],
                    -1,
                )
                if attention_mask is not None
                else None
            )
            # 采样温度缩放词表 logits，控制下一 token 的采样分布。
            # outputs.logits : (batch, seq_len, vocab_size) = (B, S, 6400)
            #                     │      │        └ 第 2 维：词表 6400 个 token 各自的打分（logit）
            #                     │      └ 第 1 维：每个序列位置对应一组下一 token 的 logits
            #                     └ 第 0 维：复制后的 batch
            # 用最后一个输入位置的 logits 选择下一 token。
            logits = outputs.logits[:, -1, :] / temperature

            # repetition_penalty > 1 时，降低上下文中已出现过的 token 的分数。
            # 小模型在采样时特别容易陷入循环：反复输出同一个短语，或几句话来回打转。
            if repetition_penalty != 1.0:
                for i in range(input_ids.shape[0]):  # 逐行（每条候选独立处理）
                    seen = torch.unique(
                        input_ids[i]
                    )  # 该行上下文里出现过的所有 token ID
                    # 取子集，“花式索引”（advanced indexing，也叫按值索引/gather 式收集）。
                    score = logits[i, seen]  # 取出这些 token 当前的 logit
                    # torch.where 按元素选择。惩罚系数大于 1 时，正分和负分都会下降，零分保持不变。
                    logits[i, seen] = torch.where(
                        score > 0,
                        score / repetition_penalty,  # 正分 → 除以惩罚系数，向 0 收缩
                        score * repetition_penalty,  # 负分 → 乘惩罚系数，推向更负
                    )
            # 取top k
            if top_k > 0:
                # torch.topk(logits, top_k)          : 每行取前 top_k 大：返回 (values, indices)
                # [0]                                : 只要 values，形状 (B, top_k)，已降序
                # [..., -1, None]                    : -1 = top_k 个里的最后一个 = 第 k 名的分数（门槛值）
                #                                    : 前面的-1操作会导致降一维，所以这里要用 None 补回来
                # logits < 该阈值                   : 得到 (B, V) 布尔掩码，True 表示得分低于第 k 名
                #                                    : 与第 k 名并列的 token 也会保留
                # logits[掩码] = -inf                : 布尔掩码写入：一次性置 -inf
                logits[logits < torch.topk(logits, top_k)[0][..., -1, None]] = -float(
                    "inf"
                )
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                # mask记录了截止到哪里的累加和超过top_p
                mask = (
                    torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1) > top_p
                )
                # 掩码右移一位，保留首个使累计概率超过 top_p 的 token。
                # 若概率最高的 token 自身已超过 top_p，右移后仍会把它保留为候选。
                mask[..., 1:], mask[..., 0] = mask[..., :-1].clone(), 0
                # scatter(1, sorted_indices, mask) 按 sorted_indices[i, r]（第 r 名的原位置）把决策写回原词表坐标系
                # 结果[i, 原位置] = mask[i, r]
                logits[mask.scatter(1, sorted_indices, mask)] = -float("inf")
            next_token = (
                # softmax 将过滤后的 logits 转为概率，被置为 -inf 的候选概率为 0。
                # torch.multinomial 以每行概率为权重随机抽样。num_samples=1 时，每行返回一个 token ID。
                torch.multinomial(torch.softmax(logits, dim=-1), num_samples=1)
                if do_sample
                else torch.argmax(logits, dim=-1, keepdim=True)
            )
            if eos_token_id is not None:
                next_token = torch.where(
                    # 后面增加一维
                    finished.unsqueeze(-1),  # 此行是否已结束
                    # 用 eos_token_id 填充张量
                    next_token.new_full((next_token.shape[0], 1), eos_token_id),
                    next_token,
                )
            # 下一次生成 token 的输入加上这一次的预测结果
            input_ids = torch.cat([input_ids, next_token], dim=-1)
            past_key_values = outputs.past_key_values if use_cache else None
            # 每生成下一个token后，推给输出端流
            if streamer:
                streamer.put(next_token.cpu())
            if eos_token_id is not None:
                # 记录是否结束，因为next_token的维度是（B, 1）, 比finished 多一个维度，所以这里要降维
                finished |= next_token.squeeze(-1).eq(eos_token_id)
                if finished.all():
                    break
        if streamer:
            streamer.end()
        if kwargs.get("return_kv"):
            return {"generated_ids": input_ids, "past_kv": past_key_values}
        return input_ids


# ============================================ 模型数据结构相关的初始化接口 ============================================
def print_model_params(model, config):
    total = sum(p.numel() for p in model.parameters()) / 1e6
    n_routed = getattr(config, "n_routed_experts", getattr(config, "num_experts", 0))
    n_active = getattr(config, "num_experts_per_tok", 0)
    n_shared = getattr(config, "n_shared_experts", 0)
    expert = (
        sum(p.numel() for n, p in model.named_parameters() if "mlp.experts.0." in n)
        / 1e6
    )
    shared_expert = (
        sum(
            p.numel()
            for n, p in model.named_parameters()
            if "mlp.shared_experts.0." in n
        )
        / 1e6
    )
    base = total - (expert * n_routed) - (shared_expert * n_shared)
    active = base + (expert * n_active) + (shared_expert * n_shared)
    if active < total:
        Logger(f"Model Params: {total:.2f}M-A{active:.2f}M")
    else:
        Logger(f"Model Params: {total:.2f}M")


def init_model(
    lm_config: LLMTrainRuntimeConfig,
    settings: LLMTrainConfigureAll,
    load_initial_weights: bool = True,
):
    # 加载词表
    tokenizer = AutoTokenizer.from_pretrained(settings.loader.tokenizer_path)
    if len(tokenizer) != lm_config.vocab_size:
        raise ValueError(
            f"tokenizer 词表大小 {len(tokenizer)} 与模型词表大小 {lm_config.vocab_size} 不一致"
        )
    for name in ("bos_token_id", "eos_token_id", "pad_token_id"):
        token_id = getattr(tokenizer, name)
        if token_id is None or not 0 <= token_id < lm_config.vocab_size:
            raise ValueError(f"tokenizer 的 {name} 未定义或超出模型词表范围")
        if name != "pad_token_id" and token_id != getattr(lm_config, name):
            raise ValueError(f"tokenizer 的 {name} 与模型配置不一致")
    model = OWenTLLMForCausalLM(lm_config)

    # 仅仅复用 tokenizer；from_weight 为 kNone 时，全部权重从头训练。
    if load_initial_weights and settings.train.from_weight != LLMTrainWeightType.kNone:
        weight_path = find_weight_file(
            f"{settings.save.dir}/output", settings, settings.train.from_weight
        )
        weights = torch.load(weight_path, map_location="cpu", weights_only=True)
        model.load_state_dict(weights)

    print_model_params(model, lm_config)
    Logger(
        f"Trainable Params: {sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e6:.3f}M"
    )

    # 将模型参数和 buffer 迁移到训练设备。
    return model.to(settings.train.device), tokenizer


class SkipBatchSampler(Sampler):
    def __init__(self, sampler, batch_size, skip_batches=0):
        self.sampler = sampler
        self.batch_size = batch_size
        self.skip_batches = skip_batches

    def __iter__(self):
        batch = []
        skipped = 0
        for idx in self.sampler:
            batch.append(idx)
            if len(batch) == self.batch_size:
                if skipped < self.skip_batches:
                    skipped += 1
                    batch = []
                    continue
                yield batch
                batch = []
        if len(batch) > 0 and skipped >= self.skip_batches:
            yield batch

    def __len__(self):
        total_batches = (len(self.sampler) + self.batch_size - 1) // self.batch_size
        return max(0, total_batches - self.skip_batches)


def load_training_json(data_path, *, kind, features=None, cache_dir=None):
    data_files = [
        str(Path(path).resolve())
        for path in sorted(glob.glob(os.fspath(data_path), recursive=True))
        if Path(path).is_file()
    ]
    if not data_files:
        raise FileNotFoundError(f"未找到本地 JSON/JSONL 数据文件：{data_path}")
    fingerprints = [sha256_file(path) for path in data_files]
    content_id = hashlib.sha256("".join(fingerprints).encode("ascii")).hexdigest()
    samples = load_dataset(
        "json",
        name=f"{kind}-{content_id}",
        data_files=data_files,
        split="train",
        features=features,
        cache_dir=cache_dir,
    )
    return samples, fingerprints


# 预训练数据提取
class PretrainDataset(torch.utils.data.Dataset):
    def __init__(self, data_path, tokenizer, max_length=512, *, cache_dir=None):
        super().__init__()
        if max_length < 3:
            raise ValueError("max_length 至少为 3，以容纳 BOS、正文和 EOS")
        self.tokenizer = tokenizer
        self.max_length = max_length
        # 同大小、同时间戳的文件替换也必须重新构建 Arrow 缓存。
        self.samples, self.source_fingerprint = load_training_json(
            data_path, kind="pretrain", cache_dir=cache_dir
        )
        self.processing_config = {"kind": "pretrain", "version": 1}

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        tokens = self.tokenizer(
            str(sample["text"]),
            add_special_tokens=False,
            # 裁剪数据不能超过 max_length，并且预留BOS和EOS。
            max_length=self.max_length - 2,
            truncation=True,
        ).input_ids
        tokens = [self.tokenizer.bos_token_id] + tokens + [self.tokenizer.eos_token_id]
        input_ids = tokens + [self.tokenizer.pad_token_id] * (
            self.max_length - len(tokens)
        )
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        labels = input_ids.clone()
        # 按实际长度屏蔽 padding，即使 PAD 与 EOS 使用同一 token ID，也保留真实 EOS 标签。
        # 非 padding 的标签沿用输入 token ID，计算损失时取下一位置的标签作为目标。
        labels[len(tokens) :] = PYTORCH_IGNORE_INDEX
        attention_mask = torch.arange(self.max_length) < len(tokens)
        # 返回的数据（这个结构由train_epoch里的消费实现决定）
        #   - 实际输入模型的 token ID；短序列用 PAD 补齐到 max_length。
        #   - 移位前的标签，忽略位置为 PYTORCH_IGNORE_INDEX。
        #   - 注意力掩码，真实 token 为 True，padding 为 False，也用于 MoE 负载统计。
        return input_ids, labels, attention_mask


# 后训练数据提取
class SFTDataset(torch.utils.data.Dataset):
    def __init__(
        self,
        jsonl_path,
        tokenizer,
        max_length=1024,
        *,
        seed=42,
        add_system_ratio=0.2,
        empty_think_ratio=0.2,
        cache_dir=None,
    ):
        super().__init__()
        if max_length < 3 or not tokenizer.is_fast:
            raise ValueError(
                "SFT 要求 max_length 至少为 3，并使用支持 offset_mapping 的 fast tokenizer"
            )
        if not 0 <= add_system_ratio <= 1 or not 0 <= empty_think_ratio <= 1:
            raise ValueError("SFT 增强概率必须在 [0, 1] 内")
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.seed, self.epoch = seed, 0
        self.add_system_ratio, self.empty_think_ratio = (
            add_system_ratio,
            empty_think_ratio,
        )
        features = Features(
            {
                "conversations": [
                    {
                        "role": Value("string"),
                        "content": Value("string"),
                        "reasoning_content": Value("string"),
                        "tools": Value("string"),
                        "tool_calls": Value("string"),
                    }
                ]
            }
        )
        self.samples, self.source_fingerprint = load_training_json(
            jsonl_path, kind="sft", features=features, cache_dir=cache_dir
        )
        # assistant 分支记录独立字符区间；不在正文中搜索角色标记。
        assistant_branch = '{%- elif message.role == "assistant" %}'
        tool_branch = '{%- elif message.role == "tool" %}'
        template = tokenizer.get_chat_template()
        if (
            template.count(assistant_branch) != 1
            or template.count(tool_branch) != 1
            or "{% generation" in template
        ):
            raise ValueError("此 SFT 示例要求使用包含 assistant/tool 的模板")
        # transformers.utils.chat_template_utils.render_jinja_template 接口约定
        # - {% generation %}...{% endgeneration %} 是 transformers 注册的 Jinja 自定义标签。
        self.training_template = template.replace(
            assistant_branch, assistant_branch + "{% generation -%}"
        ).replace(tool_branch, "{%- endgeneration %}" + tool_branch)
        self.assistant_header = f"{tokenizer.bos_token}assistant\n"
        self.processing_config = {
            "kind": "sft",
            "version": 1,
            "seed": seed,
            "add_system_ratio": add_system_ratio,
            "empty_think_ratio": empty_think_ratio,
            "template_sha256": hashlib.sha256(
                self.training_template.encode("utf-8")
            ).hexdigest(),
        }

    def __len__(self):
        return len(self.samples)

    def set_epoch(self, epoch):
        self.epoch = epoch

    def create_chat_prompt(self, conversations, *, return_spans=False):
        messages = []
        tools = None
        for message in conversations:
            message = dict(message)
            if message.get("role") == "system" and message.get("tools"):
                tools = (
                    json.loads(message["tools"])
                    if isinstance(message["tools"], str)
                    else message["tools"]
                )
            if message.get("tool_calls") and isinstance(message["tool_calls"], str):
                message["tool_calls"] = json.loads(message["tool_calls"])
            messages.append(message)
        rendered, spans = render_jinja_template(
            conversations=[messages],
            chat_template=self.training_template,
            return_assistant_tokens_mask=True,
            add_generation_prompt=False,
            tools=tools,
            **self.tokenizer.special_tokens_map,
        )
        return (rendered[0], spans[0]) if return_spans else rendered[0]

    def generate_labels(self, input_ids, offsets, spans):
        labels = [PYTORCH_IGNORE_INDEX] * len(input_ids)
        span_index = 0
        for index, (left, right) in enumerate(offsets):
            if right <= left:  # 空 offset，防御性跳过
                continue
            while span_index < len(spans) and left >= spans[span_index][1]:
                span_index += 1  # token 已越过当前 span → 移到下一个
            if (
                span_index < len(spans)
                and spans[span_index][0] <= left
                and right <= spans[span_index][1]
            ):
                labels[index] = input_ids[index]  # 完全落在 span 内 → 监督
        return labels

    def pre_processing_chat(self, conversations, rng):
        if not conversations:
            raise ValueError("SFT conversations 不能为空")
        # 含工具定义的对话跳过此处的 system 消息增强。
        if any(conv.get("tools") for conv in conversations):
            return conversations

        SYSTEM_PROMPTS = [
            "你是一个知识丰富的AI，尽力为用户提供准确的信息。",
            "你是OWenTExprLLM，一个小巧但有用的语言模型。",
            "你是一个专业的AI助手，请提供有价值的回答。",
            "你是OWenTExprLLM，请尽力帮助用户解决问题。",
            "你是一个可靠的AI，请给出准确的回答。",
            "You are a helpful AI assistant.",
            "You are OWenTExprLLM, a lightweight intelligent assistant.",
            "You are a friendly chatbot. Please answer the user's questions carefully.",
            "You are a knowledgeable AI. Try your best to provide accurate information.",
            "You are OWenTExprLLM, a small but useful language model.",
        ]
        # 概率性添加system
        if conversations[0].get("role") != "system":
            if rng.random() < self.add_system_ratio:
                return [
                    {"role": "system", "content": rng.choice(SYSTEM_PROMPTS)}
                ] + conversations
        return conversations

    def post_processing_chat(self, prompt_content, rng):
        # 只处理模板在 assistant 开头生成的空标签，保留正文中引用的相同文本。
        empty_prefix = self.assistant_header + "<think>\n\n</think>\n\n"
        if (
            prompt_content.startswith(empty_prefix)
            # 概率性保留空思考标签，让模型既见过“带空思考块”也见过“直接回答”两种格式
            and rng.random() > self.empty_think_ratio
        ):
            prompt_content = self.assistant_header + prompt_content[len(empty_prefix) :]
        return prompt_content

    def __getitem__(self, index):
        sample = self.samples[index]
        rng = random.Random(f"{self.seed}:{self.epoch}:{index}")
        # 按配置概率为缺少 system 消息的对话添加系统提示词。
        conversations = self.pre_processing_chat(sample["conversations"], rng)
        # 按模板渲染完整prompt文本
        prompt, spans = self.create_chat_prompt(conversations, return_spans=True)
        pieces, assistant_spans, cursor, length = [], [], 0, 0
        for start, end in spans:
            prefix = prompt[cursor:start]
            segment = self.post_processing_chat(prompt[start:end], rng)
            # assistant 区间必须以角色前缀开头，便于在构造监督区间时排除前缀。
            #   模板里注入{% generation %}的后面有 '<|im_start|>' + message.role + '\n<think>\n'
            #   所以下面的校验总是满足条件
            if not segment.startswith(self.assistant_header):
                raise ValueError("assistant 模板前缀不匹配")
            pieces.extend((prefix, segment))
            length += len(prefix)
            assistant_spans.append(
                (length + len(self.assistant_header), length + len(segment))
            )
            length += len(segment)
            cursor = end
        pieces.append(prompt[cursor:])
        prompt = "".join(pieces)
        # 完整prompt转换成token
        encoded = self.tokenizer(
            prompt,
            add_special_tokens=False,
            return_offsets_mapping=True,
            truncation=True,
            max_length=self.max_length,
        )
        input_ids = encoded.input_ids
        # 只监督完整落在 assistant 输出区间的 token，区间可以包含思考文本和工具调用。
        labels = self.generate_labels(
            input_ids, encoded.offset_mapping, assistant_spans
        )
        valid_length = len(input_ids)

        # 对齐到 max_length, 补PAD token
        padding = self.max_length - valid_length
        input_ids += [self.tokenizer.pad_token_id] * padding
        labels += [PYTORCH_IGNORE_INDEX] * padding
        attention_mask = torch.arange(self.max_length) < valid_length
        # 返回的数据（这个结构由train_epoch里的消费实现决定）
        #   - 实际输入模型的 token ID；短序列用 PAD 补齐。
        #   - 移位前的标签，忽略位置为 PYTORCH_IGNORE_INDEX。
        #   - 注意力掩码，真实 token 为 True，padding 为 False，也用于 MoE 负载统计。
        return (
            torch.tensor(input_ids, dtype=torch.long),
            torch.tensor(labels, dtype=torch.long),
            attention_mask,
        )


# ============================================ 流程入口 ============================================
def configure_training_stage(settings, stage, from_weight=None, *, resume=False):
    settings.train.stage = stage
    settings.save.save_weight = (
        LLMTrainWeightType.kFullSFT if stage == "sft" else LLMTrainWeightType.kPretrain
    )
    if from_weight is not None:
        settings.train.from_weight = {
            "none": LLMTrainWeightType.kNone,
            "pretrain": LLMTrainWeightType.kPretrain,
            "fullsft": LLMTrainWeightType.kFullSFT,
        }[from_weight]
    elif (
        stage == "sft"
        and settings.train.from_weight == LLMTrainWeightType.kNone
        and not resume
    ):
        settings.train.from_weight = LLMTrainWeightType.kPretrain


def create_train_dataset(settings, data_path, tokenizer, *, cache_dir=None):
    if settings.train.stage == "pretrain":
        return PretrainDataset(
            data_path,
            tokenizer,
            settings.loader.data_item_max_length,
            cache_dir=cache_dir,
        )
    return SFTDataset(
        data_path,
        tokenizer,
        settings.loader.data_item_max_length,
        seed=settings.train.seed,
        add_system_ratio=settings.loader.sft_add_system_ratio,
        empty_think_ratio=settings.loader.sft_empty_think_ratio,
        cache_dir=cache_dir,
    )


def create_train_loader(settings, dataset, epoch, start_step=0):
    if hasattr(dataset, "set_epoch"):
        dataset.set_epoch(epoch)
    sampler = (
        DistributedSampler(dataset, seed=settings.train.seed)
        if dist.is_initialized()
        else None
    )
    if sampler is not None:
        sampler.set_epoch(epoch)
    else:
        generator = torch.Generator().manual_seed(settings.train.seed + epoch)
        sampler = torch.randperm(len(dataset), generator=generator).tolist()
    iters = (len(sampler) + settings.train.batch_size - 1) // settings.train.batch_size
    if not 0 <= start_step <= iters:
        raise ValueError("检查点 step 超出了当前数据范围")
    rank = dist.get_rank() if dist.is_initialized() else 0
    loader = DataLoader(
        dataset,
        batch_sampler=SkipBatchSampler(sampler, settings.train.batch_size, start_step),
        num_workers=settings.loader.num_workers,
        pin_memory=torch.device(settings.train.device).type == "cuda",
        generator=torch.Generator().manual_seed(settings.train.seed + epoch + rank),
    )
    return loader, iters


def save_training_checkpoint(settings, epoch, step, iters, wandb, resume_metadata):
    if is_main_process():
        ckp = f"{settings.save.dir}/output/{lm_get_ckp_file_name(settings, settings.save.save_weight)}"
        raw_model = (
            model.module if isinstance(model, DistributedDataParallel) else model
        )
        raw_model = getattr(raw_model, "_orig_mod", raw_model)
        os.makedirs(os.path.dirname(ckp), exist_ok=True)
        torch.save(
            {
                k: v.half().cpu() if v.is_floating_point() else v.cpu()
                for k, v in raw_model.state_dict().items()
            },
            ckp,
        )
    lm_checkpoint(
        settings,
        model=model,
        optimizer=optimizer,
        scaler=scaler,
        epoch=epoch,
        step=step,
        wandb=wandb,
        iters=iters,
        resume_metadata=resume_metadata,
    )


# 开始一轮训练
def train_epoch(
    settings: LLMTrainConfigureAll,
    scaler: torch.amp.GradScaler,
    epoch: int,
    loader: DataLoader,
    iters: int,
    start_step: int = 0,
    wandb: Any = None,
    *,
    resume_metadata,
) -> None:
    if settings.train.accumulation_steps < 1 or settings.save.step_interval < 1:
        raise ValueError("accumulation_steps 和保存间隔必须为正数")
    if start_step % settings.train.accumulation_steps and start_step != iters:
        raise ValueError("检查点必须位于梯度累积窗口结束处")
    start_time = time.time()
    # 标记训练模式
    model.train()
    # 初始清空梯度
    optimizer.zero_grad(set_to_none=True)
    batches = iter(loader)
    step = start_step

    # 每个窗口最多取 accumulation_steps 个 microbatch，最后不足一个窗口的也处理。
    while window := list(islice(batches, settings.train.accumulation_steps)):
        # 只预取一个累积窗口的 CPU batch，按所有 rank 的有效预测 token 数归一化。
        token_counts = [
            # labels 第 0 维（batch）全部保留。第 1 维（列/位置）：从下标 1 取到末尾 → 丢掉第 0 列
            #   forward 里 logits[..., :-1] 为什么对 labels[..., 1:] ？因为因果预测是预测下一个token，所以要丢掉第 0 列
            #   这样处理以后logits某个位置的数据刚好对应labels里一样位置的预测目标。
            int((labels[:, 1:] != PYTORCH_IGNORE_INDEX).sum())
            for _, labels, _ in window
        ]
        total_tokens = torch.tensor(
            sum(token_counts), device=settings.train.device, dtype=torch.long
        )
        world_size = dist.get_world_size() if dist.is_initialized() else 1
        if dist.is_initialized():
            dist.all_reduce(total_tokens)
        window_end = step + len(window)
        if total_tokens.item() == 0:
            save_pending = (
                # 最后一个窗口总是保存
                window_end == iters
                # 跨保存窗口间隔总是保存
                or step // settings.save.step_interval
                < window_end // settings.save.step_interval
            )
            step = window_end
            Logger(
                f"Epoch {epoch + 1}, step {step}: 累积窗口没有监督 token，跳过参数更新"
            )
            if save_pending:
                save_training_checkpoint(
                    settings, epoch, step, iters, wandb, resume_metadata
                )
            continue
        # 对应文章中的 $W/N$。除以全局监督 token 数 N，乘 W 抵消 DDP 的梯度平均系数。
        loss_scale = world_size / total_tokens.item()

        # 按窗口结束时的累计 microbatch 序号计算学习率。
        lr = get_learning_rate(
            epoch * iters + window_end,
            settings.train.epochs * iters,
            settings.train.learning_rate,
        )
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr
        save_pending = False

        for (input_ids, labels, attention_mask), token_count in zip(
            window, token_counts
        ):
            step += 1
            input_ids = input_ids.to(settings.train.device)
            labels = labels.to(settings.train.device)
            attention_mask = attention_mask.to(settings.train.device)
            with autocast_ctx:
                # 这个会传到模型的forward接口里
                res = model(
                    input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                    loss_reduction="sum",
                )
                # CE 是 token 损失之和；辅助损失按各 microbatch 的有效预测 token 数加权。
                # 对应文章中的 $\ell_{r,i} = \frac{W}{N}\left(C_{r,i} + n_{r,i} A_{r,i}\right)$。
                loss = (res.loss + res.aux_loss * token_count) * loss_scale
            # backward() 将本次梯度加到参数的 .grad。启用 GradScaler 时，scale(loss) 将损失
            # 乘以缩放因子 S，反向传播得到的梯度也乘以 S。同一窗口内使用相同的 S。
            scaler.scale(loss).backward()

            # checkpoint 保存点，同样最后一个窗口总是保存
            save_pending |= step % settings.save.step_interval == 0 or step == iters

            # 日志打印周期
            if step % settings.log.step_interval == 0 or step == iters:
                spend_time = time.time() - start_time
                current_logits_loss = res.loss.item() / max(token_count, 1)
                current_aux_loss = res.aux_loss.item()
                current_loss = current_logits_loss + current_aux_loss
                current_lr = optimizer.param_groups[-1]["lr"]
                eta_min = spend_time / max(step - start_step, 1) * (iters - step) // 60
                Logger(
                    f"Epoch:[{epoch + 1}/{settings.train.epochs}]({step}/{iters}), loss: {current_loss:.4f}, logits_loss: {current_logits_loss:.4f}, aux_loss: {current_aux_loss:.4f}, lr: {current_lr:.8f}, epoch_time: {eta_min:.1f}min"
                )
                if wandb:
                    wandb.log(
                        {
                            "loss": current_loss,
                            "logits_loss": current_logits_loss,
                            "aux_loss": current_aux_loss,
                            "learning_rate": current_lr,
                            "epoch_time": eta_min,
                        }
                    )
            del input_ids, labels, attention_mask, res, loss

        # 对应前面的 scaler.scale(loss)。启用 GradScaler 时，unscale_ 将累积的 .grad
        # 原地除以缩放因子 S，接下来的梯度裁剪作用于解除缩放后的梯度。
        scaler.unscale_(optimizer)

        # clip_grad_norm_ 把所有梯度视为拼接后的一个向量来计算 L2 范数。
        # 超过阈值时，原地按同一个比例缩小各参数的梯度。
        torch.nn.utils.clip_grad_norm_(model.parameters(), settings.train.grad_clip)
        # 尝试更新参数。启用 GradScaler 且检测到非有限梯度时跳过。
        scaler.step(optimizer)

        # 按非有限梯度检测结果及连续有效更新次数维护缩放因子。
        scaler.update()

        # 然后清空梯度
        optimizer.zero_grad(set_to_none=True)

        # 保存间隔仍按 microbatch 计数，触发后在累积窗口处理完毕时保存。
        if save_pending:
            save_training_checkpoint(
                settings, epoch, step, iters, wandb, resume_metadata
            )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=f"{LLM_TRAIN_SETTINGS.model_name} {LLM_TRAIN_SETTINGS.save.save_weight.name}"
    )
    parser.add_argument(
        "--input-data-path",
        type=str,
        default=None,
        help="(预)训练数据路径",
        dest="input_data_path",
    )
    parser.add_argument(
        "--resume",
        default=False,
        action="store_true",
        help="恢复检查点；不存在或与当前配置不兼容时报错",
    )
    parser.add_argument(
        "--tokenizer",
        default=LLM_TRAIN_SETTINGS.loader.tokenizer_path,
        type=str,
        help="tokenizer文件路径",
    )
    parser.add_argument(
        "--stage",
        choices=("pretrain", "sft"),
        default=LLM_TRAIN_SETTINGS.train.stage,
        help="训练目标，与初始权重来源独立",
    )
    parser.add_argument(
        "--from-weight",
        choices=("none", "pretrain", "fullsft"),
        default=None,
        help="新训练的初始权重；SFT 默认使用 pretrain，续训直接恢复检查点",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    configure_training_stage(
        LLM_TRAIN_SETTINGS, args.stage, args.from_weight, resume=args.resume
    )

    # ========== 1. 初始化环境和随机种子 ==========
    local_rank = init_distributed_mode(LLM_TRAIN_SETTINGS)
    setup_seed(
        LLM_TRAIN_SETTINGS.train.seed
        + (dist.get_rank() if dist.is_initialized() else 0)
    )

    if args.tokenizer:
        LLM_TRAIN_SETTINGS.loader.tokenizer_path = args.tokenizer

    # ========== 2. 创建输出目录并构造模型配置 ==========
    os.makedirs(f"{LLM_TRAIN_SETTINGS.save.dir}/output", exist_ok=True)
    lm_config = LLMTrainRuntimeConfig(LLM_TRAIN_SETTINGS)

    # ========== 3. 设置混合精度 ==========
    device_type = "cuda" if "cuda" in LLM_TRAIN_SETTINGS.train.device else "cpu"
    dtype = getattr(torch, LLM_TRAIN_SETTINGS.param.dtype)
    autocast_ctx = (
        nullcontext()
        if device_type == "cpu" or dtype == torch.float32
        else torch.amp.autocast(device_type, dtype=dtype)
    )

    # ========== 4. 加载模型、数据，核对续训配置与输入内容 ==========
    model, tokenizer = init_model(
        lm_config, LLM_TRAIN_SETTINGS, load_initial_weights=not args.resume
    )
    # 读取训练数据集的加载器
    train_ds = create_train_dataset(LLM_TRAIN_SETTINGS, args.input_data_path, tokenizer)
    # 续训时，用这个resume_metadata来校验关键设置要匹配
    resume_metadata = build_resume_metadata(LLM_TRAIN_SETTINGS, train_ds, tokenizer)
    ckp_data = (
        lm_checkpoint(LLM_TRAIN_SETTINGS, resume_metadata=resume_metadata)
        if args.resume
        else None
    )
    # CPU 执行 FP32；仅 CUDA FP16 启用 GradScaler。
    # FP16 无法表示的一些小梯度会舍入为零。缩放损失可减轻这种下溢。
    # 缩放后的梯度仍可能溢出。检测到 inf 或 NaN 梯度时，跳过本次参数更新。
    scaler = torch.amp.GradScaler(
        device_type, enabled=(device_type == "cuda" and dtype == torch.float16)
    )

    # 创建优化器，即根据梯度计算并执行参数更新的算法。在 PyTorch 中，优化器对象还保存学习率、动量等运行状态。
    optimizer = create_optimizer(model, LLM_TRAIN_SETTINGS)

    # ========== 5. 初始化 SwanLab 日志（配置字段名为 wandb） ==========
    wandb = None
    if (
        is_main_process()
        and LLM_TRAIN_SETTINGS.visualization
        and LLM_TRAIN_SETTINGS.visualization.wandb
        and LLM_TRAIN_SETTINGS.visualization.wandb.project
    ):
        import swanlab as wandb

        wandb_id = ckp_data.get("wandb_id") if ckp_data else None
        resume = "must" if wandb_id else None
        wandb_project = f"{LLM_TRAIN_SETTINGS.model_name}-{str(LLM_TRAIN_SETTINGS.save.save_weight)[1:]}"
        wandb_run_name = f"{wandb_project}-Epoch-{LLM_TRAIN_SETTINGS.train.epochs}-BatchSize-{LLM_TRAIN_SETTINGS.train.batch_size}-LearningRate-{LLM_TRAIN_SETTINGS.train.learning_rate}"
        wandb.init(
            project=wandb_project, name=wandb_run_name, id=wandb_id, resume=resume
        )

    # ========== 6. 从ckp恢复状态 ==========
    start_epoch, start_step = 0, 0
    if ckp_data:
        model.load_state_dict(ckp_data["model"])
        optimizer.load_state_dict(ckp_data["optimizer"])
        scaler.load_state_dict(ckp_data["scaler"])
        start_epoch = ckp_data["epoch"]
        start_step = ckp_data.get("step", 0)

    # ========== 7. 编译和分布式包装 ==========
    if LLM_TRAIN_SETTINGS.train.use_compile:
        model = torch.compile(model)
        Logger("torch.compile enabled")
    if dist.is_initialized():
        model = DistributedDataParallel(
            model, device_ids=[local_rank] if device_type == "cuda" else None
        )

    # ========== 8. 开始训练 ==========
    for epoch in range(start_epoch, LLM_TRAIN_SETTINGS.train.epochs):
        rank = dist.get_rank() if dist.is_initialized() else 0
        setup_seed(LLM_TRAIN_SETTINGS.train.seed + epoch + rank)
        # 数据打乱和 DataLoader 的种子使用独立 Generator，不消耗模型 dropout 的 RNG。
        skip = start_step if (epoch == start_epoch and start_step > 0) else 0
        loader, iters = create_train_loader(LLM_TRAIN_SETTINGS, train_ds, epoch, skip)

        # 续训的首个 epoch 从检查点恢复当前 rank 的随机数状态。
        if ckp_data and epoch == start_epoch:
            if ckp_data.get("iters", iters) != iters:
                raise ValueError("数据批次数与检查点不一致，无法按保存位置续训")
            restore_rng_state(
                ckp_data["rng_states"][rank], LLM_TRAIN_SETTINGS.train.device
            )
        if skip > 0:
            Logger(
                f"Epoch [{epoch + 1}/{LLM_TRAIN_SETTINGS.train.epochs}]: 跳过前{start_step}个step，从step {start_step + 1}开始"
            )

        # 执行一个epoch训练
        train_epoch(
            LLM_TRAIN_SETTINGS,
            scaler,
            epoch,
            loader,
            iters,
            skip,
            wandb,
            resume_metadata=resume_metadata,
        )

    # ========== 9. 清理分布进程 ==========
    if dist.is_initialized():
        dist.barrier()
        dist.destroy_process_group()
