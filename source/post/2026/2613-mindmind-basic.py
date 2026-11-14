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

from pydantic import BaseModel

from datasets import load_dataset, Features, Value
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader, DistributedSampler, Sampler
from transformers.activations import ACT2FN
from transformers import PreTrainedModel, GenerationMixin, PretrainedConfig
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from transformers.modeling_outputs import MoeCausalLMOutputWithPast

warnings.filterwarnings("ignore")


# 下载数据集 modelscope download --dataset gongjy/minimind_dataset README.md --local_dir ./dataset

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
            raise RuntimeError("当前 PyTorch 未提供 NCCL/RCCL，无法启动 GPU DDP；请使用单进程 GPU，或在支持该后端的环境中运行。CPU DDP 可将 train.device 设为 cpu。")
        if not torch.cuda.is_available():
            raise RuntimeError("配置要求 CUDA/ROCm 设备，但当前环境不可用")
        device = torch.device("cuda", local_rank if distributed else (device.index if device.index is not None else torch.cuda.current_device()))
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
            # 模型保存间隔
            "step_interval": 1000,
        },
        "train": {
            # 基于哪个权重训练，为none则从头开始
            "from_weight": LLMTrainWeightType.kNone,
            # Batch size
            "batch_size": 8,
            # 训练轮数
            "epochs": 2,
            # 初始学习率
            "learning_rate": 2e-5,
            # 训练设备(如果有多GPU或者AMD的独显+集显，请注意选择正确的显卡设备)
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            # 是否使用torch.compile加速
            "use_compile": False,
            # 随机种子（每轮每个 rank 为 seed+epoch+rank）。这个值可否随机？还是必须每次训练必须保持不变？
            "seed": 42,
            # 梯度累积步数。有什么作用？
            "accumulation_steps": 8,
            # 梯度裁剪阈值。有什么作用？
            "grad_clip": 1.0,
        },
        "param": {
            # epsilon 参数
            "eps": 1e-6,
            # 混合精度类型
            "dtype": "bfloat16",
            # 隐藏层维度，是否需要可word embedding的维度相同？
            "hidden_size": LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE,
            # 隐藏层数量，隐藏层越多，是否世界知识越丰富？
            "num_hidden_layers": 8,
            # dropout 现代模型 dropout 是否都是0？为什么？
            "dropout": 0.0,
            # 词表大小？
            "vocab_size": 6400,
            # 什么含义？和词表相关？
            "bos_token_id": 1,
            # 什么含义？和词表相关？
            "eos_token_id": 2,
            # 是否使用Flash Attention
            "flash_attn": True,
            # 多头注意力的头数量，每个头分开计算。然后再concat到一起
            "num_attention_heads": 8,
            # KV头数量，为什么要和num_attention_heads分开？
            "num_key_value_heads": 4,
            # 什么含义?
            "hidden_act": "silu",
            # 什么含义？
            "intermediate_size": math.ceil(
                LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE * math.pi / 64
            )
            * 64,
            # 什么含义？
            "max_position_embeddings": 32768,
            # 什么含义?
            "rope_theta": 1e6,
            # 什么含义？
            "tie_word_embeddings": True,
            # 什么含义?
            "inference_rope_scaling": False,
            # 什么作用？
            "rope_scaling": None,
            # 是否是MOE模型
            "use_moe": True,
            # MOE 专家数
            "moe_num_experts": 8,
            # MOE 激活专家数
            "moe_num_experts_per_tok": 2,
            # 什么含义？
            "moe_intermediate_size": math.ceil(
                LLM_TRAIN_CONST_VALUE_HIDDEN_SIZE * math.pi / 64
            )
            * 64,
            # 什么含义？
            "norm_topk_prob": True,
            # 什么含义？
            "router_aux_loss_coef": 5e-4,
        },
        "loader": {
            # 加载数据的工作线程数
            "num_workers": 8,
            # 每条训练数据的最大截断长度，Unsloth里QWen 3.8 27B默认2048，GPT-20b-oss默认1024
            "data_item_max_length": 2048,
            # tokenizer路径
            "tokenizer_path": "./model",
        },
        "visualization": None,
        "log": {
            # 日志打印间隔
            "step_interval": 100,
        }
    }
)
if LLM_TRAIN_SETTINGS.param.inference_rope_scaling:
    LLM_TRAIN_SETTINGS.param.rope_scaling = LLMTrainConfigureRopeScaling.model_validate(
        {
            # 下列参数分别什么含义？
            "beta_fast": 32,
            "beta_slow": 1,
            "factor": 16,
            "original_max_position_embeddings": 2048,
            "attention_factor": 1.0,
            "type": "yarn",
        }
    )


def is_main_process():
    return not dist.is_initialized() or dist.get_rank() == 0


def Logger(content):
    if is_main_process():
        print(content)


# 获取本次Step的学习率
# 带下限的余弦退火（Cosine Annealing）学习率衰减公式。
# SGDR: Stochastic Gradient Descent with Warm Restarts（Loshchilov & Hutter, 2017）
# lr_t = lr_min + (lr_max - lr_min) * (1 + cos(pi * x)) / 2
def get_learning_rate(current_step, total_steps, lr):
    return lr * (0.1 + 0.45 * (1 + math.cos(math.pi * current_step / total_steps)))


# 创建优化器
# Adam 部分：自适应学习率: 梯度大/波动大的参数（v_t大）自动用更小的步长，梯度稳定的参数用更大的步长。
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
        values = param.model_dump(exclude={"dtype", "eps", "moe_num_experts", "moe_num_experts_per_tok"})
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

def lm_get_ckp_file_name(settings : LLMTrainConfigureAll, weight : LLMTrainWeightType):
    moe_path = '-moe' if settings.param.use_moe else ''
    return f"{weight.name[1:].lower()}-{settings.param.hidden_size}{moe_path}.pth"
def lm_get_ckp_resume_file_name(settings : LLMTrainConfigureAll, weight : LLMTrainWeightType):
    moe_path = '-moe' if settings.param.use_moe else ''
    return f"{weight.name[1:].lower()}-{settings.param.hidden_size}{moe_path}.resume.pth"


def find_weight_file(directory, settings, weight, *, resume=False):
    name = lm_get_ckp_resume_file_name(settings, weight) if resume else lm_get_ckp_file_name(settings, weight)
    current = Path(directory) / name
    legacy_name = f"{str(weight)[1:]}-{settings.param.hidden_size}{'-moe' if settings.param.use_moe else ''}"
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
            for path in sorted(Path(directory).rglob("*")) if path.is_file()
        }
    return {
        "version": 1,
        "train": settings.train.model_dump(mode="json", exclude={"device", "from_weight"}),
        "model": settings.param.model_dump(mode="json"),
        "loader": {"data_item_max_length": dataset.max_length, "num_workers": settings.loader.num_workers},
        "device_type": torch.device(settings.train.device).type,
        "dataset": {"files": dataset.source_fingerprint, "rows": len(dataset)},
        "tokenizer": tokenizer_files,
    }


def validate_resume_metadata(checkpoint, expected):
    saved = checkpoint.get("resume_metadata")
    if saved is None:
        raise ValueError("旧检查点缺少完整续训信息，无法核对模型、精度、数据及 tokenizer；请通过 train.from_weight 加载对应导出权重，开始新训练。")
    changed = sorted(key for key in saved.keys() | expected.keys() if saved.get(key) != expected.get(key))
    if changed:
        raise ValueError(f"续训配置或输入内容与检查点不一致：{', '.join(changed)}；请恢复原配置与数据，或从权重开始新训练。")


def capture_rng_state(device):
    device = torch.device(device)
    numpy_state = numpy.random.get_state()
    return {
        "python": random.getstate(),
        "numpy": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state(device=device) if device.type == "cuda" else None,
    }


def restore_rng_state(state, device):
    device = torch.device(device)
    if (state["cuda"] is not None) != (device.type == "cuda"):
        raise ValueError("随机数状态的设备类型与当前训练设备不一致")
    random.setstate(state["python"])
    numpy_state = state["numpy"]
    numpy.random.set_state((numpy_state[0], numpy.array(numpy_state[1], dtype=numpy.uint32), *numpy_state[2:]))
    torch.set_rng_state(state["torch"])
    if device.type == "cuda":
        torch.cuda.set_rng_state(state["cuda"], device=device)


# 读取或保存检查点
def lm_checkpoint(settings : LLMTrainConfigureAll, model=None, optimizer=None, epoch=0, step=0, wandb=None, *, resume_metadata, **kwargs):
    save_dir = f"{settings.save.dir}/checkpoint"
    os.makedirs(save_dir, exist_ok=True)
    ckp_path = f'{save_dir}/{lm_get_ckp_file_name(settings, settings.save.save_weight)}'
    resume_path = f'{save_dir}/{lm_get_ckp_resume_file_name(settings, settings.save.save_weight)}'

    if model is not None:
        # 所有 rank 都参与收集；只由主进程写文件。
        rng_states = [capture_rng_state(settings.train.device)]
        if dist.is_initialized():
            local_rng_state = rng_states[0]
            rng_states = [None] * dist.get_world_size()
            dist.all_gather_object(rng_states, local_rng_state)
        if not is_main_process():
            return
        raw_model = model.module if isinstance(model, DistributedDataParallel) else model
        raw_model = getattr(raw_model, '_orig_mod', raw_model)
        state_dict = raw_model.state_dict()
        state_dict = {k: v.detach().cpu() for k, v in state_dict.items()}
        ckp_tmp = ckp_path + '.tmp'
        torch.save({k: v.half() if v.is_floating_point() else v for k, v in state_dict.items()}, ckp_tmp)
        os.replace(ckp_tmp, ckp_path)
        wandb_id = None
        if wandb:
            if hasattr(wandb, 'get_run'):
                run = wandb.get_run()
                wandb_id = getattr(run, 'id', None) if run else None
            else:
                wandb_id = getattr(wandb, 'id', None)

        resume_data = {
            'model': state_dict,
            'optimizer': optimizer.state_dict(),
            'epoch': epoch,
            'step': step,
            'world_size': dist.get_world_size() if dist.is_initialized() else 1,
            'wandb_id': wandb_id,
            'rng_states': rng_states,
            'resume_metadata': resume_metadata,
        }
        for key, value in kwargs.items():
            if value is not None:
                if hasattr(value, 'state_dict'):
                    raw_value = value.module if isinstance(value, DistributedDataParallel) else value
                    raw_value = getattr(raw_value, '_orig_mod', raw_value)
                    resume_data[key] = raw_value.state_dict()
                else:
                    resume_data[key] = value

        resume_tmp = resume_path + '.tmp'
        torch.save(resume_data, resume_tmp)
        os.replace(resume_tmp, resume_path)
        del state_dict, resume_data
        torch.cuda.empty_cache()
    else:  # 加载模式
        resume_path = find_weight_file(save_dir, settings, settings.save.save_weight, resume=True)
        ckp_data = torch.load(resume_path, map_location='cpu', weights_only=True)
        saved_ws = ckp_data.get('world_size', 1)
        current_ws = dist.get_world_size() if dist.is_initialized() else 1
        if saved_ws != current_ws:
            raise ValueError(f'续训要求 world_size 保持一致（保存值 {saved_ws}，当前值 {current_ws}）；改变 GPU 数量请从模型权重开始新训练。')
        validate_resume_metadata(ckp_data, resume_metadata)
        if len(ckp_data.get('rng_states', [])) != current_ws:
            raise ValueError('检查点缺少各 rank 的随机数状态，无法续训')
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
        # x 的形状通常是 (batch_size, seq_len, hidden_size)，这里指对最后一维进行求平均
        # 求平均会让一个向量变成一个值，从而使一个维度消失，因此需要 keepdim=True 保持维度不变
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
        rope_scaling is not None and rope_scaling.get("rope_type", rope_scaling.get("type", "yarn")) == "yarn"
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
    def __init__(self, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.num_key_value_heads = (
            config.num_attention_heads
            if config.num_key_value_heads is None
            else config.num_key_value_heads
        )
        self.n_local_heads = config.num_attention_heads
        self.n_local_kv_heads = self.num_key_value_heads
        self.n_rep = self.n_local_heads // self.n_local_kv_heads
        self.head_dim = config.head_dim
        self.is_causal = True
        self.q_proj = torch.nn.Linear(
            config.hidden_size, config.num_attention_heads * self.head_dim, bias=False
        )
        self.k_proj = torch.nn.Linear(
            config.hidden_size, self.num_key_value_heads * self.head_dim, bias=False
        )
        self.v_proj = torch.nn.Linear(
            config.hidden_size, self.num_key_value_heads * self.head_dim, bias=False
        )
        self.o_proj = torch.nn.Linear(
            config.num_attention_heads * self.head_dim, config.hidden_size, bias=False
        )
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
        bsz, seq_len, _ = x.shape
        xq, xk, xv = self.q_proj(x), self.k_proj(x), self.v_proj(x)
        xq = xq.view(bsz, seq_len, self.n_local_heads, self.head_dim)
        xk = xk.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
        xv = xv.view(bsz, seq_len, self.n_local_kv_heads, self.head_dim)
        xq, xk = self.q_norm(xq), self.k_norm(xk)
        cos, sin = position_embeddings
        xq, xk = apply_rotary_pos_emb(xq, xk, cos, sin)
        if past_key_value is not None:
            xk = torch.cat([past_key_value[0], xk], dim=1)
            xv = torch.cat([past_key_value[1], xv], dim=1)
        past_kv = (xk, xv) if use_cache else None
        xq, xk, xv = (
            xq.transpose(1, 2),
            repeat_kv(xk, self.n_rep).transpose(1, 2),
            repeat_kv(xv, self.n_rep).transpose(1, 2),
        )
        if (
            self.flash
            and (seq_len > 1)
            and (not self.is_causal or past_key_value is None)
        ):
            sdpa_mask = None
            if attention_mask is not None and not torch.all(attention_mask == 1):
                sdpa_mask = attention_mask[:, None, None, :].bool()
                if self.is_causal:
                    causal_mask = torch.ones(seq_len, seq_len, dtype=torch.bool, device=x.device).tril()
                    sdpa_mask = sdpa_mask & causal_mask
            output = torch.nn.functional.scaled_dot_product_attention(
                xq,
                xk,
                xv,
                attn_mask=sdpa_mask,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=self.is_causal and sdpa_mask is None,
            )
        else:
            scores = (xq @ xk.transpose(-2, -1)).float() / math.sqrt(self.head_dim)
            if self.is_causal:
                scores[:, :, :, -seq_len:] += torch.full(
                    (seq_len, seq_len), float("-inf"), device=scores.device
                ).triu(1)
            if attention_mask is not None:
                scores += (1.0 - attention_mask.unsqueeze(1).unsqueeze(2).to(scores.dtype)) * -1e9
            output = self.attn_dropout(torch.nn.functional.softmax(scores, dim=-1).type_as(xq)) @ xv
        output = output.transpose(1, 2).reshape(bsz, seq_len, -1)
        output = self.resid_dropout(self.o_proj(output))
        return output, past_kv


class FeedForward(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig, intermediate_size: int = None):
        super().__init__()
        intermediate_size = intermediate_size or config.intermediate_size
        self.gate_proj = torch.nn.Linear(config.hidden_size, intermediate_size, bias=False)
        self.down_proj = torch.nn.Linear(intermediate_size, config.hidden_size, bias=False)
        self.up_proj = torch.nn.Linear(config.hidden_size, intermediate_size, bias=False)
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, x):
        return self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))


class MOEFeedForward(torch.nn.Module):
    def __init__(self, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.config = config
        self.gate = torch.nn.Linear(config.hidden_size, config.num_experts, bias=False)
        self.experts = torch.nn.ModuleList(
            [
                FeedForward(config, intermediate_size=config.moe_intermediate_size)
                for _ in range(config.num_experts)
            ]
        )
        self.act_fn = ACT2FN[config.hidden_act]

    def forward(self, x, token_mask=None):
        batch_size, seq_len, hidden_dim = x.shape
        x_flat = x.view(-1, hidden_dim)
        scores = torch.nn.functional.softmax(self.gate(x_flat), dim=-1)
        topk_weight, topk_idx = torch.topk(
            scores, k=self.config.num_experts_per_tok, dim=-1, sorted=False
        )
        if self.config.norm_topk_prob:
            if self.config.num_experts_per_tok > 1:
                topk_weight = topk_weight / (
                    topk_weight.sum(dim=-1, keepdim=True) + 1e-20
                )
            else:
                top1 = torch.topk(
                    torch.nn.functional.softmax(self.gate(x_flat.detach()), dim=-1),
                    k=1,
                    dim=-1,
                    sorted=False,
                )[0]
                topk_weight = (
                    top1 - top1.detach() + 1.0
                )  # k=1: 1.0 forward on purpose, gradient via straight-through
        y = torch.zeros_like(x_flat)
        for i, expert in enumerate(self.experts):
            mask = topk_idx == i
            if mask.any():
                token_idx = mask.any(dim=-1).nonzero().flatten()
                weight = topk_weight[mask].view(-1, 1)
                y.index_add_(
                    0, token_idx, (expert(x_flat[token_idx]) * weight).to(y.dtype)
                )
            elif self.training:
                y[0, 0] += 0 * sum(p.sum() for p in expert.parameters())
        if self.training and self.config.router_aux_loss_coef > 0:
            valid = token_mask.reshape(-1).bool() if token_mask is not None else torch.ones(
                batch_size * seq_len, dtype=torch.bool, device=x.device
            )
            if valid.any():
                load = torch.nn.functional.one_hot(topk_idx[valid], self.config.num_experts).float().mean(0)
                self.aux_loss = (
                    (load * scores[valid].mean(0)).sum()
                    * self.config.num_experts
                    * self.config.router_aux_loss_coef
                )
            else:
                self.aux_loss = scores.sum() * 0.0
        else:
            self.aux_loss = scores.new_zeros(1).squeeze()
        return y.view(batch_size, seq_len, hidden_dim)


# 单层 Transformer 解码块
class OWenTLLMBlock(torch.nn.Module):
    def __init__(self, layer_id: int, config: LLMTrainRuntimeConfig):
        super().__init__()
        self.self_attn = Attention(config)
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
        residual = hidden_states
        hidden_states, present_key_value = self.self_attn(
            self.input_layernorm(hidden_states),
            position_embeddings,
            past_key_value,
            use_cache,
            attention_mask,
        )
        hidden_states += residual
        mlp_input = self.post_attention_layernorm(hidden_states)
        if isinstance(self.mlp, MOEFeedForward):
            token_mask = attention_mask[:, -hidden_states.shape[1]:] if attention_mask is not None else None
            mlp_output = self.mlp(mlp_input, token_mask=token_mask)
        else:
            mlp_output = self.mlp(mlp_input)
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
        self.embed_tokens = torch.nn.Embedding(config.vocab_size, config.hidden_size)
        self.dropout = torch.nn.Dropout(config.dropout)
        self.layers = torch.nn.ModuleList(
            [OWenTLLMBlock(l, config) for l in range(self.num_hidden_layers)]
        )
        self.norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        freqs_cos, freqs_sin = precompute_freqs_cis(
            dim=config.head_dim,
            end=config.max_position_embeddings,
            rope_base=config.rope_parameters["rope_theta"],
            rope_scaling=config.rope_parameters,
        )
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
        if hasattr(past_key_values, "layers"):
            past_key_values = None
        past_key_values = past_key_values or [None] * len(self.layers)
        start_pos = (
            past_key_values[0][0].shape[1] if past_key_values[0] is not None else 0
        )
        hidden_states = self.dropout(self.embed_tokens(input_ids))
        # Recompute RoPE buffers lost during meta-device init (transformers>=5.x)
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
        position_embeddings = (
            self.freqs_cos[start_pos : start_pos + seq_length],
            self.freqs_sin[start_pos : start_pos + seq_length],
        )
        presents = []
        for layer, past_key_value in zip(self.layers, past_key_values):
            hidden_states, present = layer(
                hidden_states,
                position_embeddings,
                past_key_value=past_key_value,
                use_cache=use_cache,
                attention_mask=attention_mask,
            )
            presents.append(present)
        hidden_states = self.norm(hidden_states)
        aux_loss = sum(
            [l.mlp.aux_loss for l in self.layers if isinstance(l.mlp, MOEFeedForward)],
            hidden_states.new_zeros(1).squeeze(),
        )
        return hidden_states, presents, aux_loss


# 完整模型
class OWenTLLMForCausalLM(PreTrainedModel, GenerationMixin):
    config_class = LLMTrainRuntimeConfig
    _tied_weights_keys = {"lm_head.weight": "model.embed_tokens.weight"}

    def __init__(self, config: LLMTrainRuntimeConfig = None):
        self.config = config or LLMTrainRuntimeConfig(LLM_TRAIN_SETTINGS)
        super().__init__(self.config)
        self.model = OWenTLLMModel(self.config)
        self.lm_head = torch.nn.Linear(
            self.config.hidden_size, self.config.vocab_size, bias=False
        )
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
        hidden_states, past_key_values, aux_loss = self.model(
            input_ids, attention_mask, past_key_values, use_cache, **kwargs
        )
        slice_indices = (
            slice(-logits_to_keep, None)
            if isinstance(logits_to_keep, int)
            else logits_to_keep
        )
        logits = self.lm_head(hidden_states[:, slice_indices, :])
        loss = None
        if labels is not None:
            x, y = logits[..., :-1, :].contiguous(), labels[..., 1:].contiguous()
            loss = torch.nn.functional.cross_entropy(
                x.view(-1, x.size(-1)), y.view(-1), ignore_index=-100,
                reduction=loss_reduction,
            )
        return MoeCausalLMOutputWithPast(
            loss=loss,
            aux_loss=aux_loss,
            logits=logits,
            past_key_values=past_key_values,
            hidden_states=hidden_states,
        )

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
        input_ids = kwargs.pop("input_ids", inputs).repeat(num_return_sequences, 1)
        attention_mask = (
            attention_mask.repeat(num_return_sequences, 1)
            if attention_mask is not None
            else None
        )
        past_key_values = kwargs.pop("past_key_values", None)
        finished = torch.zeros(
            input_ids.shape[0], dtype=torch.bool, device=input_ids.device
        )
        if streamer:
            streamer.put(input_ids.cpu())
        for _ in range(max_new_tokens):
            past_len = past_key_values[0][0].shape[1] if past_key_values else 0
            outputs = self.forward(
                input_ids[:, past_len:],
                attention_mask,
                past_key_values,
                use_cache=use_cache,
                **kwargs,
            )
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
            logits = outputs.logits[:, -1, :] / temperature
            if repetition_penalty != 1.0:
                for i in range(input_ids.shape[0]):
                    seen = torch.unique(input_ids[i])
                    score = logits[i, seen]
                    logits[i, seen] = torch.where(
                        score > 0,
                        score / repetition_penalty,
                        score * repetition_penalty,
                    )
            if top_k > 0:
                logits[logits < torch.topk(logits, top_k)[0][..., -1, None]] = -float(
                    "inf"
                )
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                mask = (
                    torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1) > top_p
                )
                mask[..., 1:], mask[..., 0] = mask[..., :-1].clone(), 0
                logits[mask.scatter(1, sorted_indices, mask)] = -float("inf")
            next_token = (
                torch.multinomial(torch.softmax(logits, dim=-1), num_samples=1)
                if do_sample
                else torch.argmax(logits, dim=-1, keepdim=True)
            )
            if eos_token_id is not None:
                next_token = torch.where(
                    finished.unsqueeze(-1),
                    next_token.new_full((next_token.shape[0], 1), eos_token_id),
                    next_token,
                )
            input_ids = torch.cat([input_ids, next_token], dim=-1)
            past_key_values = outputs.past_key_values if use_cache else None
            if streamer:
                streamer.put(next_token.cpu())
            if eos_token_id is not None:
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
    settings: LLMTrainConfigureAll
):
    tokenizer = AutoTokenizer.from_pretrained(settings.loader.tokenizer_path)
    if len(tokenizer) != lm_config.vocab_size:
        raise ValueError(f"tokenizer 词表大小 {len(tokenizer)} 与模型词表大小 {lm_config.vocab_size} 不一致")
    for name in ("bos_token_id", "eos_token_id", "pad_token_id"):
        token_id = getattr(tokenizer, name)
        if token_id is None or not 0 <= token_id < lm_config.vocab_size:
            raise ValueError(f"tokenizer 的 {name} 未定义或超出模型词表范围")
        if name != "pad_token_id" and token_id != getattr(lm_config, name):
            raise ValueError(f"tokenizer 的 {name} 与模型配置不一致")
    model = OWenTLLMForCausalLM(lm_config)

    # 复用 tokenizer 不会复用 Embedding；from_weight 为 kNone 时，全部权重从头训练。
    if settings.train.from_weight != LLMTrainWeightType.kNone:
        weight_path = find_weight_file(f"{settings.save.dir}/output", settings, settings.train.from_weight)
        weights = torch.load(weight_path, map_location='cpu', weights_only=True)
        model.load_state_dict(weights)

    print_model_params(model, lm_config)
    Logger(
        f"Trainable Params: {sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e6:.3f}M"
    )
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

# 预训练数据提取
class PretrainDataset(torch.utils.data.Dataset):
    def __init__(self, data_path, tokenizer, max_length=512):
        super().__init__()
        if max_length < 3:
            raise ValueError("max_length 至少为 3，以容纳 BOS、正文和 EOS")
        self.tokenizer = tokenizer
        self.max_length = max_length
        data_files = [str(Path(path).resolve()) for path in sorted(glob.glob(os.fspath(data_path), recursive=True)) if Path(path).is_file()]
        if not data_files:
            raise FileNotFoundError(f"未找到本地 JSON/JSONL 数据文件：{data_path}")
        self.source_fingerprint = [sha256_file(path) for path in data_files]
        # 同大小、同时间戳的文件替换也必须重新构建 Arrow 缓存。
        content_id = hashlib.sha256("".join(self.source_fingerprint).encode("ascii")).hexdigest()
        self.samples = load_dataset('json', name=f"pretrain-{content_id}", data_files=data_files, split='train')

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        tokens = self.tokenizer(str(sample['text']), add_special_tokens=False, max_length=self.max_length - 2, truncation=True).input_ids
        tokens = [self.tokenizer.bos_token_id] + tokens + [self.tokenizer.eos_token_id]
        input_ids = tokens + [self.tokenizer.pad_token_id] * (self.max_length - len(tokens))
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        labels = input_ids.clone()
        # 按实际长度屏蔽 padding，即使 PAD 与 EOS 使用同一 token ID，也保留真实 EOS 标签。
        labels[len(tokens):] = -100
        attention_mask = torch.arange(self.max_length) < len(tokens)
        # 返回的数据是什么含义？
        return input_ids, labels, attention_mask

# 后训练数据提取
class SFTDataset(torch.utils.data.Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=1024):
        super().__init__()
        self.tokenizer = tokenizer
        self.max_length = max_length
        features = Features({'conversations': [{'role': Value('string'), 'content': Value('string'), 'reasoning_content': Value('string'), 'tools': Value('string'), 'tool_calls': Value('string')}]})
        self.samples = load_dataset('json', data_files=jsonl_path, split='train', features=features)
        self.bos_id = tokenizer(f'{tokenizer.bos_token}assistant\n', add_special_tokens=False).input_ids
        self.eos_id = tokenizer(f'{tokenizer.eos_token}\n', add_special_tokens=False).input_ids

    def __len__(self):
        return len(self.samples)

    def create_chat_prompt(self, conversations):
        messages = []
        tools = None
        for message in conversations:
            message = dict(message)
            if message.get("role") == "system" and message.get("tools"):
                tools = json.loads(message["tools"]) if isinstance(message["tools"], str) else message["tools"]
            if message.get("tool_calls") and isinstance(message["tool_calls"], str):
                message["tool_calls"] = json.loads(message["tool_calls"])
            messages.append(message)
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            tools=tools
        )

    def generate_labels(self, input_ids):
        labels = [-100] * len(input_ids)
        i = 0
        while i < len(input_ids):
            if input_ids[i:i + len(self.bos_id)] == self.bos_id:
                start = i + len(self.bos_id)
                end = start
                while end < len(input_ids):
                    if input_ids[end:end + len(self.eos_id)] == self.eos_id:
                        break
                    end += 1
                for j in range(start, min(end + len(self.eos_id), self.max_length)):
                    labels[j] = input_ids[j]
                i = end + len(self.eos_id) if end < len(input_ids) else len(input_ids)
            else:
                i += 1
        return labels

    def pre_processing_chat(self, conversations, add_system_ratio=0.2):
        # tool use 数据完整保留不做处理
        if any(conv.get('tools') for conv in conversations): return conversations

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
            "You are OWenTExprLLM, a small but useful language model."
        ]
        # 概率性添加system
        if conversations[0].get('role') != 'system':
            if random.random() < add_system_ratio:
                return [{'role': 'system', 'content': random.choice(SYSTEM_PROMPTS)}] + conversations
        return conversations

    def post_processing_chat(self, prompt_content, empty_think_ratio=0.2):
        # 以80%概率移除空思考标签
        if '<think>\n\n</think>\n\n' in prompt_content and random.random() > empty_think_ratio:
            prompt_content = prompt_content.replace('<think>\n\n</think>\n\n', '')
        return prompt_content
    def __getitem__(self, index):
        sample = self.samples[index]
        conversations = self.pre_processing_chat(sample['conversations'])
        prompt = self.create_chat_prompt(conversations)
        prompt = self.post_processing_chat(prompt)
        input_ids = self.tokenizer(prompt).input_ids[:self.max_length]
        input_ids += [self.tokenizer.pad_token_id] * (self.max_length - len(input_ids))
        labels = self.generate_labels(input_ids)
        # # === 调试打印 ===
        # print(f"\n--- Sample {index} ---")
        # for i, (x, y) in enumerate(zip(input_ids[:-1], labels[1:])):
        #     print(f"{i:3d}: X={self.tokenizer.decode([x])!r:16s} ---> Y={self.tokenizer.decode([input_ids[i+1]])!r:16s} label={y}")
        # # ================
        return torch.tensor(input_ids, dtype=torch.long), torch.tensor(labels, dtype=torch.long)

# ============================================ 流程入口 ============================================
# 开始一轮训练
def train_epoch(settings: LLMTrainConfigureAll, epoch: int, loader: DataLoader, iters: int, start_step: int = 0, wandb: Any = None, *, resume_metadata) -> None:
    if settings.train.accumulation_steps < 1 or settings.save.step_interval < 1:
        raise ValueError("accumulation_steps 和保存间隔必须为正数")
    if start_step % settings.train.accumulation_steps and start_step != iters:
        raise ValueError("检查点必须位于梯度累积窗口结束处")
    start_time = time.time()
    model.train()
    optimizer.zero_grad(set_to_none=True)
    batches = iter(loader)
    step = start_step
    while window := list(islice(batches, settings.train.accumulation_steps)):
        # 只预取一个累积窗口的 CPU batch，按所有 rank 的有效预测 token 数归一化。
        token_counts = [int((labels[:, 1:] != -100).sum()) for _, labels, _ in window]
        total_tokens = torch.tensor(sum(token_counts), device=settings.train.device, dtype=torch.long)
        world_size = dist.get_world_size() if dist.is_initialized() else 1
        if dist.is_initialized():
            dist.all_reduce(total_tokens)
        loss_scale = world_size / max(total_tokens.item(), 1)
        window_end = step + len(window)
        lr = get_learning_rate(epoch * iters + window_end, settings.train.epochs * iters, settings.train.learning_rate)
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr
        save_pending = False

        for (input_ids, labels, attention_mask), token_count in zip(window, token_counts):
            step += 1
            input_ids = input_ids.to(settings.train.device)
            labels = labels.to(settings.train.device)
            attention_mask = attention_mask.to(settings.train.device)
            with autocast_ctx:
                res = model(input_ids, attention_mask=attention_mask, labels=labels, loss_reduction="sum")
                # CE 是 token 损失之和；辅助损失按各 microbatch 的有效预测 token 数加权。
                loss = (res.loss + res.aux_loss * token_count) * loss_scale
            scaler.scale(loss).backward()
            save_pending |= step % settings.save.step_interval == 0 or step == iters

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
                    wandb.log({
                        "loss": current_loss, "logits_loss": current_logits_loss,
                        "aux_loss": current_aux_loss, "learning_rate": current_lr,
                        "epoch_time": eta_min,
                    })
            del input_ids, labels, attention_mask, res, loss

        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), settings.train.grad_clip)
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)

        # 保存间隔仍按 microbatch 计数；若落在累积窗口中间，延后到本窗口更新完成。
        if save_pending:
            if is_main_process():
                ckp = f"{settings.save.dir}/output/{lm_get_ckp_file_name(settings, settings.save.save_weight)}"
                raw_model = model.module if isinstance(model, DistributedDataParallel) else model
                raw_model = getattr(raw_model, "_orig_mod", raw_model)
                os.makedirs(os.path.dirname(ckp), exist_ok=True)
                torch.save(
                    {k: v.half().cpu() if v.is_floating_point() else v.cpu() for k, v in raw_model.state_dict().items()},
                    ckp,
                )
            lm_checkpoint(
                settings, model=model, optimizer=optimizer, scaler=scaler,
                epoch=epoch, step=step, wandb=wandb, iters=iters,
                resume_metadata=resume_metadata,
            )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=f"{LLM_TRAIN_SETTINGS.model_name} {LLM_TRAIN_SETTINGS.save.save_weight.name}")
    parser.add_argument(
        "--input-data-path",
        type=str,
        default="../dataset/pretrain_t2t_mini.jsonl",
        help="(预)训练数据路径",
        dest="input_data_path"
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
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    # ========== 1. 初始化环境和随机种子 ==========
    local_rank = init_distributed_mode(LLM_TRAIN_SETTINGS)
    setup_seed(LLM_TRAIN_SETTINGS.train.seed + (dist.get_rank() if dist.is_initialized() else 0))

    if args.tokenizer:
        LLM_TRAIN_SETTINGS.loader.tokenizer_path = args.tokenizer

    # ========== 2. 配置目录和模型参数 ==========
    os.makedirs(f"{LLM_TRAIN_SETTINGS.save.dir}/output", exist_ok=True)
    lm_config = LLMTrainRuntimeConfig(LLM_TRAIN_SETTINGS)

    # ========== 3. 设置混合精度 ==========
    device_type = "cuda" if "cuda" in LLM_TRAIN_SETTINGS.train.device else "cpu"
    dtype = getattr(torch, LLM_TRAIN_SETTINGS.param.dtype)
    autocast_ctx = (
        nullcontext() if device_type == "cpu" or dtype == torch.float32 else torch.amp.autocast(device_type, dtype=dtype)
    )

    # ========== 4. 加载模型、数据，核对续训配置与输入内容 ==========
    model, tokenizer = init_model(lm_config, LLM_TRAIN_SETTINGS)
    if LLM_TRAIN_SETTINGS.train.from_weight == LLMTrainWeightType.kNone:
        train_ds = PretrainDataset(args.input_data_path, tokenizer, max_length=LLM_TRAIN_SETTINGS.loader.data_item_max_length)
    else:
        train_ds = SFTDataset(args.input_data_path, tokenizer, max_length=LLM_TRAIN_SETTINGS.loader.data_item_max_length)
    resume_metadata = build_resume_metadata(LLM_TRAIN_SETTINGS, train_ds, tokenizer)
    ckp_data = lm_checkpoint(LLM_TRAIN_SETTINGS, resume_metadata=resume_metadata) if args.resume else None
    train_sampler = DistributedSampler(train_ds, seed=LLM_TRAIN_SETTINGS.train.seed) if dist.is_initialized() else None
    # CPU 执行 FP32；仅 CUDA FP16 启用 GradScaler。
    # GradScaler的作用是什么？
    scaler = torch.amp.GradScaler(device_type, enabled=(device_type == "cuda" and dtype == torch.float16))
    optimizer = create_optimizer(model, LLM_TRAIN_SETTINGS)

    # ========== 5. 配wandb可视化， https://wandb.ai/ 注册账号和项目 ==========
    wandb = None
    if is_main_process() and LLM_TRAIN_SETTINGS.visualization and LLM_TRAIN_SETTINGS.visualization.wandb and LLM_TRAIN_SETTINGS.visualization.wandb.project:
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
        model = DistributedDataParallel(model, device_ids=[local_rank] if device_type == "cuda" else None)

    # ========== 8. 开始训练 ==========
    for epoch in range(start_epoch, LLM_TRAIN_SETTINGS.train.epochs):
        train_sampler and train_sampler.set_epoch(epoch)
        rank = dist.get_rank() if dist.is_initialized() else 0
        setup_seed(LLM_TRAIN_SETTINGS.train.seed + epoch + rank)
        # 数据打乱和 DataLoader 的种子使用独立 Generator，不消耗模型 dropout 的 RNG。
        sampler_generator = torch.Generator().manual_seed(LLM_TRAIN_SETTINGS.train.seed + epoch)
        indices = torch.randperm(len(train_ds), generator=sampler_generator).tolist() if train_sampler is None else None
        skip = start_step if (epoch == start_epoch and start_step > 0) else 0
        sample_count = len(train_sampler) if train_sampler is not None else len(indices)
        iters = (sample_count + LLM_TRAIN_SETTINGS.train.batch_size - 1) // LLM_TRAIN_SETTINGS.train.batch_size
        if skip > iters:
            raise ValueError("检查点 step 超出了当前数据范围")
        batch_sampler = SkipBatchSampler(
            train_sampler or indices, LLM_TRAIN_SETTINGS.train.batch_size, skip
        )
        loader = DataLoader(
            train_ds,
            batch_sampler=batch_sampler,
            num_workers=LLM_TRAIN_SETTINGS.loader.num_workers,
            pin_memory=True,
            generator=torch.Generator().manual_seed(LLM_TRAIN_SETTINGS.train.seed + epoch + rank),
        )
        if ckp_data and epoch == start_epoch:
            if ckp_data.get("iters", iters) != iters:
                raise ValueError("数据批次数与检查点不一致，无法按保存位置续训")
            restore_rng_state(ckp_data["rng_states"][rank], LLM_TRAIN_SETTINGS.train.device)
        if skip > 0:
            Logger(
                f"Epoch [{epoch + 1}/{LLM_TRAIN_SETTINGS.train.epochs}]: 跳过前{start_step}个step，从step {start_step + 1}开始"
            )
        train_epoch(LLM_TRAIN_SETTINGS, epoch, loader, iters, skip, wandb, resume_metadata=resume_metadata)

    # ========== 9. 清理分布进程 ==========
    if dist.is_initialized():
        dist.barrier()
        dist.destroy_process_group()
