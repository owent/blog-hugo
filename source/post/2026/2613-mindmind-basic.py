import os
import sys
import random
import argparse
import time
import math
import warnings
from contextlib import nullcontext
from typing import Any
from enum import Enum

import numpy

__package__ = "trainer"
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from pydantic import BaseModel

from datasets import load_dataset
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
    rope_scaling: LLMTrainConfigureRopeScaling
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
def init_distributed_mode():
    if int(os.environ.get("RANK", -1)) == -1:
        return 0  # 非DDP模式

    # 多卡训练
    # nccl是 NVIDIA 的多卡集合通信库，是 GPU 训练做梯度 all-reduce 的标准后端。
    dist.init_process_group(backend="nccl")
    # 取出本进程在本机内的 GPU 编号
    local_rank = int(os.environ["LOCAL_RANK"])
    # 绑定GPU
    torch.cuda.set_device(local_rank)
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
            # 随机种子（DDP下每个rank为seed+rank，每轮为seed+epoch）。这个值可否随机？还是必须每次训练必须保持不变？
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
            "tokenizer_path": "../model",
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

    def __init__(self, settings: LLMTrainConfigureAll, **kwargs):
        super().__init__(**kwargs)
        self.hidden_size = settings.param.hidden_size
        self.num_hidden_layers = settings.param.num_hidden_layers
        self.use_moe = settings.param.use_moe
        self.dropout = settings.param.dropout
        self.vocab_size = settings.param.vocab_size
        self.bos_token_id = settings.param.bos_token_id
        self.eos_token_id = settings.param.eos_token_id
        self.flash_attn = settings.param.flash_attn
        self.num_attention_heads = settings.param.num_attention_heads
        self.num_key_value_heads = settings.param.num_key_value_heads
        # 每头维度
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.hidden_act = settings.param.hidden_act
        self.intermediate_size = settings.param.intermediate_size
        self.max_position_embeddings = settings.param.max_position_embeddings
        self.rms_norm_eps = settings.param.eps
        self.rope_theta = settings.param.rope_theta
        self.tie_word_embeddings = settings.param.tie_word_embeddings
        self.inference_rope_scaling = settings.param.intermediate_size
        self.rope_scaling = settings.param.rope_scaling
        ### MoE specific configs (ignored if use_moe = False)
        self.num_experts = settings.param.moe_num_experts
        self.num_experts_per_tok = settings.param.moe_num_experts_per_tok
        self.moe_intermediate_size = settings.param.moe_intermediate_size
        self.norm_topk_prob = settings.param.norm_topk_prob
        self.router_aux_loss_coef = settings.param.router_aux_loss_coef

def lm_get_ckp_file_name(settings : LLMTrainConfigureAll, weight : LLMTrainWeightType):
    moe_path = '-moe' if settings.param.use_moe else ''
    return f"{str(weight)[1:]}-{settings.param.hidden_size}{moe_path}.pth"
def lm_get_ckp_resume_file_name(settings : LLMTrainConfigureAll, weight : LLMTrainWeightType):
    moe_path = '-moe' if settings.param.use_moe else ''
    return f"{str(weight)[1:]}-{settings.param.hidden_size}{moe_path}.resume.pth"
# 读取或保存检查点
def lm_checkpoint(settings : LLMTrainConfigureAll, model=None, optimizer=None, epoch=0, step=0, wandb=None, **kwargs):
    save_dir = f"{settings.save.dir}/checkpoint"
    os.makedirs(save_dir, exist_ok=True)
    ckp_path = f'{save_dir}/{lm_get_ckp_file_name(settings, settings.save.save_weight)}'
    resume_path = f'{save_dir}/{lm_get_ckp_resume_file_name(settings, settings.save.save_weight)}'

    if model is not None:
        raw_model = model.module if isinstance(model, DistributedDataParallel) else model
        raw_model = getattr(raw_model, '_orig_mod', raw_model)
        state_dict = raw_model.state_dict()
        state_dict = {k: v.half().cpu() for k, v in state_dict.items()}
        ckp_tmp = ckp_path + '.tmp'
        torch.save(state_dict, ckp_tmp)
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
            'wandb_id': wandb_id
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
        if os.path.exists(resume_path):
            ckp_data = torch.load(resume_path, map_location='cpu')
            saved_ws = ckp_data.get('world_size', 1)
            current_ws = dist.get_world_size() if dist.is_initialized() else 1
            if saved_ws != current_ws:
                ckp_data['step'] = ckp_data['step'] * saved_ws // current_ws
                Logger(f'GPU数量变化({saved_ws}→{current_ws})，step已自动转换为{ckp_data["step"]}')
            return ckp_data
        return None

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
        rope_scaling is not None
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
            and (attention_mask is None or torch.all(attention_mask == 1))
        ):
            output = torch.nn.functional.scaled_dot_product_attention(
                xq,
                xk,
                xv,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=self.is_causal,
            )
        else:
            scores = (xq @ xk.transpose(-2, -1)).float() / math.sqrt(self.head_dim)
            if self.is_causal:
                scores[:, :, :, -seq_len:] += torch.full(
                    (seq_len, seq_len), float("-inf"), device=scores.device
                ).triu(1)
            if attention_mask is not None:
                scores += (1.0 - attention_mask.unsqueeze(1).unsqueeze(2)) * -1e9
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

    def forward(self, x):
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
            load = torch.nn.functional.one_hot(topk_idx, self.config.num_experts).float().mean(0)
            self.aux_loss = (
                (load * scores.mean(0)).sum()
                * self.config.num_experts
                * self.config.router_aux_loss_coef
            )
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
        hidden_states = hidden_states + self.mlp(
            self.post_attention_layernorm(hidden_states)
        )
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
            rope_base=config.rope_theta,
            rope_scaling=config.rope_scaling,
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
                rope_base=self.config.rope_theta,
                rope_scaling=self.config.rope_scaling,
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
                x.view(-1, x.size(-1)), y.view(-1), ignore_index=-100
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
    model = OWenTLLMForCausalLM(lm_config)

    # 如果是从一个已经与训练好的模型做后训练，那么这里的 from_weight 是 LLMTrainWeightType.kPretrain
    if settings.train.from_weight != LLMTrainWeightType.kNone:
        weight_path = (
            f"{settings.save.dir}/output/{lm_get_ckp_file_name(settings, settings.train.from_weight)}"
        )
        weights = torch.load(weight_path, map_location=settings.train.device)
        model.load_state_dict(weights, strict=False)

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
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = load_dataset('json', data_files=data_path, split='train')

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        tokens = self.tokenizer(str(sample['text']), add_special_tokens=False, max_length=self.max_length - 2, truncation=True).input_ids
        tokens = [self.tokenizer.bos_token_id] + tokens + [self.tokenizer.eos_token_id]
        input_ids = tokens + [self.tokenizer.pad_token_id] * (self.max_length - len(tokens))
        input_ids = torch.tensor(input_ids, dtype=torch.long)
        labels = input_ids.clone()
        labels[input_ids == self.tokenizer.pad_token_id] = -100
        # 返回的是什么？
        return input_ids, labels

# ============================================ 流程入口 ============================================
# 开始一轮训练
def train_epoch(settings: LLMTrainConfigureAll, epoch: int, loader: DataLoader, iters: int, start_step: int = 0, wandb: Any = None) -> None:
    start_time = time.time()
    # 每一个Step都对应一组输入数据
    for step, (input_ids, labels) in enumerate(loader, start=start_step + 1):
        input_ids = input_ids.to(settings.train.device)
        labels = labels.to(settings.train.device)
        lr = get_learning_rate(
            epoch * iters + step,
            settings.train.epochs * iters,
            settings.train.learning_rate,
        )
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr

        with autocast_ctx:
            res = model(input_ids, labels=labels)
            loss = res.loss + res.aux_loss
            loss = loss / settings.train.accumulation_steps

        scaler.scale(loss).backward()

        if step % settings.train.accumulation_steps == 0 or step == iters:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), settings.train.grad_clip)

            scaler.step(optimizer)
            scaler.update()

            optimizer.zero_grad(set_to_none=True)

        if step % settings.log.step_interval == 0 or step == iters:
            spend_time = time.time() - start_time
            current_loss = loss.item() * settings.train.accumulation_steps
            current_aux_loss = res.aux_loss.item() if res.aux_loss is not None else 0.0
            current_logits_loss = current_loss - current_aux_loss
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

        if (step % settings.save.step_interval == 0 or step == iters) and is_main_process():
            model.eval()
            ckp = f"{settings.save.dir}/output/{lm_get_ckp_file_name(settings, settings.save.save_weight)}"
            raw_model = (
                model.module if isinstance(model, DistributedDataParallel) else model
            )
            raw_model = getattr(raw_model, "_orig_mod", raw_model)
            state_dict = raw_model.state_dict()
            torch.save({k: v.half().cpu() for k, v in state_dict.items()}, ckp)
            lm_checkpoint(
                settings,
                model=model,
                optimizer=optimizer,
                scaler=scaler,
                epoch=epoch,
                step=step,
                wandb=wandb,
            )
            model.train()
            del state_dict

        del input_ids, labels, res, loss


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"{LLM_TRAIN_SETTINGS.model_name} {str(LLM_TRAIN_SETTINGS.save.save_weight)[1:]}")
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
        type=bool,
        action="store_true",
        help="是否自动检测&续训",
    )
    args = parser.parse_args()

    # ========== 1. 初始化环境和随机种子 ==========
    local_rank = init_distributed_mode()
    if dist.is_initialized():
        LLM_TRAIN_SETTINGS.train.device = f"cuda:{local_rank}"
    setup_seed(LLM_TRAIN_SETTINGS.train.seed + (dist.get_rank() if dist.is_initialized() else 0))

    # ========== 2. 配置目录、模型参数、检查ckp ==========
    os.makedirs(f"{LLM_TRAIN_SETTINGS.save.dir}/output", exist_ok=True)
    lm_config = LLMTrainRuntimeConfig(LLM_TRAIN_SETTINGS)
    ckp_data = (
        lm_checkpoint(LLM_TRAIN_SETTINGS)
        if args.resume == 1
        else None
    )

    # ========== 3. 设置混合精度 ==========
    device_type = "cuda" if "cuda" in LLM_TRAIN_SETTINGS.train.device else "cpu"
    dtype = torch.bfloat16 if LLM_TRAIN_SETTINGS.param.dtype == "bfloat16" else torch.float16
    autocast_ctx = (
        nullcontext() if device_type == "cpu" else torch.amp.autocast(device_type, dtype=dtype)
    )

    # ========== 4. 配wandb可视化， https://wandb.ai/ 注册账号和项目 ==========
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

    # ========== 5. 定义模型、数据、优化器 ==========
    model, tokenizer = init_model(lm_config, LLM_TRAIN_SETTINGS)
    train_ds = PretrainDataset(args.input_data_path, tokenizer, max_length=LLM_TRAIN_SETTINGS.loader.data_item_max_length)
    train_sampler = DistributedSampler(train_ds) if dist.is_initialized() else None
    # GradScaler的作用是什么？
    scaler = torch.amp.GradScaler(device_type, enabled=(LLM_TRAIN_SETTINGS.param.dtype == "float16"))
    optimizer = torch.optim.AdamW(model.parameters(), lr=LLM_TRAIN_SETTINGS.train.learning_rate)

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
        model = DistributedDataParallel(model, device_ids=[local_rank])

    # ========== 8. 开始训练 ==========
    for epoch in range(start_epoch, LLM_TRAIN_SETTINGS.train.epochs):
        train_sampler and train_sampler.set_epoch(epoch)
        setup_seed(LLM_TRAIN_SETTINGS.train.seed + epoch)
        indices = torch.randperm(len(train_ds)).tolist()
        skip = start_step if (epoch == start_epoch and start_step > 0) else 0
        batch_sampler = SkipBatchSampler(
            train_sampler or indices, LLM_TRAIN_SETTINGS.train.batch_size, skip
        )
        loader = DataLoader(
            train_ds,
            batch_sampler=batch_sampler,
            num_workers=LLM_TRAIN_SETTINGS.loader.num_workers,
            pin_memory=True,
        )
        if skip > 0:
            Logger(
                f"Epoch [{epoch + 1}/{LLM_TRAIN_SETTINGS.train.epochs}]: 跳过前{start_step}个step，从step {start_step + 1}开始"
            )
            train_epoch(
                LLM_TRAIN_SETTINGS,
                epoch,
                loader,
                # 因为上面的 SkipBatchSampler 会使得 len(loader) 减去 skip，所以这里要加回来
                len(loader) + skip,
                start_step,
                wandb,
            )
        else:
            train_epoch(LLM_TRAIN_SETTINGS, epoch, loader, len(loader), 0, wandb)

    # ========== 9. 清理分布进程 ==========
    if dist.is_initialized():
        dist.barrier()
        dist.destroy_process_group()
