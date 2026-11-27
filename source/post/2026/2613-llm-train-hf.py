"""用 Transformers 训练使用手写 KDA 和 MLA 的小型语言模型，并加载导出的模型生成文本。

准备与设备匹配的 PyTorch，再安装本例依赖：
    python -m pip install "transformers[torch]==5.24.0" "datasets==5.2.0"

将本脚本放入训练工作目录，在 dataset 中准备 MiniMind tokenizer 和 JSONL 语料后运行
    python 2613-llm-train-hf.py pretrain dataset/pretrain_t2t_mini.jsonl
    python 2613-llm-train-hf.py sft dataset/sft_t2t_mini.jsonl
    python 2613-llm-train-hf.py generate "用一句话解释梯度累积。"

pretrain 读取 {"text": "..."}，sft 读取 {"conversations": [{"role": ..., "content": ...}, ...]}。
长期使用的参数统一在 LLM_TRAIN_SETTINGS 中修改。命令行参数可覆盖本次运行的默认值。
预训练默认使用 8 层、宽度 768 的 MoE。小规模试跑可加 --hidden-size 128，稠密模型用 --dense。
保留原数据和训练参数，加 --resume 可恢复本阶段最新的 Trainer 检查点。
SFT 按模板处理原始消息，省去教学版随机添加系统提示和移除空思考块的数据增强。
用 generate --raw --model out/pretrain "开头文字" 可检查预训练模型的续写。

手写混合注意力的试验命令（small-*.jsonl 为自行截取的小份语料）：
    python 2613-llm-train-hf.py pretrain small-text.jsonl --hidden-size 64 --max-length 64 --output out/hybrid
    python 2613-llm-train-hf.py sft small-chat.jsonl --model out/hybrid --output out/hybrid-sft --max-length 64
    python 2613-llm-train-hf.py generate --model out/hybrid-sft "你好"
KDA 逐 token 展开递推以便对照公式，训练时 autograd 会保留中间状态。请从短序列开始试验。
递推公式、3∶1 层排列及 NoPE MLA 见 Kimi Linear 技术报告第 3、4 节：https://arxiv.org/html/2510.26692v1
"""

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import torch
from torch import nn
from torch.nn import functional as F
from datasets import load_dataset
from transformers import (
    AutoConfig, AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq, DynamicCache,
    GenerationConfig, GenerationMixin, PreTrainedConfig, PreTrainedModel, Trainer, TrainingArguments, set_seed,
)
from transformers.modeling_outputs import MoeCausalLMOutputWithPast
from transformers.models.llama.modeling_llama import LlamaMLP
from transformers.models.mixtral.modeling_mixtral import MixtralExperts, MixtralTopKRouter, load_balancing_loss_func
from transformers.trainer_utils import get_last_checkpoint


# ==================== 参数配置 ====================
@dataclass
class ModelSettings:
    hidden_size: int
    num_hidden_layers: int
    num_attention_heads: int
    intermediate_size: int | None
    ffn_multiplier: float
    ffn_multiple_of: int
    rms_norm_eps: float
    max_position_embeddings: int
    tie_word_embeddings: bool
    use_moe: bool
    moe_num_experts: int
    moe_num_experts_per_tok: int
    router_aux_loss_coef: float
    layer_pattern: tuple[Literal["kda", "mla"], ...]
    kda_conv_kernel_size: int
    kda_qk_eps: float
    kda_rate_range: tuple[float, float]
    kda_dt_range: tuple[float, float]
    mla_kv_rank: int | None
    mla_shared_dim: int | None


@dataclass
class TrainSettings:
    seed: int
    epochs: int
    batch_size: int
    accumulation_steps: int
    learning_rate: float
    lr_scheduler_type: str
    lr_scheduler_kwargs: dict
    weight_decay: float
    grad_clip: float
    bf16: bool | None
    logging_steps: int
    report_to: str


@dataclass
class LoaderSettings:
    tokenizer_path: str
    data_item_max_length: int


@dataclass
class SaveSettings:
    dir: str
    step_interval: int
    total_limit: int


@dataclass
class GenerateSettings:
    max_new_tokens: int
    do_sample: bool
    temperature: float
    top_p: float
    use_cache: bool
    device: str | None


@dataclass
class LLMTrainConfigureAll:
    param: ModelSettings
    train: TrainSettings
    loader: LoaderSettings
    save: SaveSettings
    generate: GenerateSettings


LLM_TRAIN_SETTINGS = LLMTrainConfigureAll(
    param=ModelSettings(
        hidden_size=768, num_hidden_layers=8, num_attention_heads=8,
        # 指定 intermediate_size 可直接设定 FFN 宽度。None 时把实际 H 乘以系数，再向上对齐。
        intermediate_size=None, ffn_multiplier=math.pi, ffn_multiple_of=64,
        rms_norm_eps=1e-6, max_position_embeddings=32768, tie_word_embeddings=True,
        use_moe=True, moe_num_experts=8, moe_num_experts_per_tok=2, router_aux_loss_coef=5e-4,
        # Decoder Block 按此顺序重复。默认每四层包含三层 KDA 和一层全局 MLA。
        layer_pattern=("kda", "kda", "kda", "mla"),
        kda_conv_kernel_size=4, kda_qk_eps=1e-6,
        kda_rate_range=(1.0, 16.0), kda_dt_range=(1e-3, 1e-1),  # 衰减率 A 均匀取样，dt 在对数尺度取样
        mla_kv_rank=None, mla_shared_dim=None,  # None 时分别取 2·head_dim 和 ⌊head_dim/2⌋
    ),
    train=TrainSettings(
        seed=42, epochs=2, batch_size=1, accumulation_steps=8, learning_rate=2e-5,
        lr_scheduler_type="cosine_with_min_lr", lr_scheduler_kwargs={"min_lr_rate": 0.1},
        weight_decay=0.01, grad_clip=1.0, bf16=None,  # None 时在支持 BF16 的 CUDA 设备上启用
        logging_steps=10, report_to="none",
    ),
    loader=LoaderSettings(tokenizer_path="dataset/minimind-tokenizer", data_item_max_length=2048),
    save=SaveSettings(dir="out", step_interval=125, total_limit=2),  # 间隔按优化器更新步数计
    generate=GenerateSettings(
        max_new_tokens=128, do_sample=True, temperature=0.85, top_p=0.85, use_cache=True,
        device=None,  # None 时优先 CUDA，其次 CPU，也可指定 "cpu" 或 "cuda:0"
    ),
)


# ==================== 手写混合注意力 ====================
class HybridConfig(PreTrainedConfig):
    model_type = "owent_kda_mla"
    attribute_map = {"num_experts": "num_local_experts"}
    vocab_size: int
    bos_token_id: int
    eos_token_id: int | list[int]
    pad_token_id: int
    tie_word_embeddings: bool
    hidden_size: int
    intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    rms_norm_eps: float
    max_position_embeddings: int
    num_local_experts: int
    num_experts_per_tok: int
    router_aux_loss_coef: float
    hidden_act: str = "silu"
    initializer_range: float = 0.02
    use_cache: bool = True
    dense_ffn: bool = False
    mlp_bias: bool = False  # LlamaMLP 的投影配置
    layer_types: list[str] | None = None
    # 旧版 config.json 只记录了 layer_types。以下缺省值还原旧权重的结构与数值行为。
    # 新建模型时由 LLM_TRAIN_SETTINGS 传入实际参数，随模型一起保存。
    kda_conv_kernel_size: int = 4
    kda_qk_eps: float = 1e-6
    kda_rate_range: list[float] | tuple[float, float] = (1.0, 16.0)
    kda_dt_range: list[float] | tuple[float, float] = (1e-3, 1e-1)
    mla_kv_rank: int | None = None
    mla_shared_dim: int | None = None

    def __post_init__(self, **kwargs):
        # 早期的混合模型借用 Mixtral 配置类；这些旧字段从未参与手写层的计算。
        for name in ("num_key_value_heads", "rope_parameters", "head_dim", "sliding_window",
                     "attention_dropout", "router_jitter_noise"):
            kwargs.pop(name, None)
        # 旧训练检查点会把收集路由分数的临时开关写入配置。现在由本次前向的标签或显式请求决定。
        kwargs.pop("output_router_logits", None)
        if self.layer_types is None:
            names = {"kda": "linear_attention", "mla": "full_attention"}
            layers = LLM_TRAIN_SETTINGS.param.layer_pattern
            if "mla" not in layers or any(kind not in names for kind in layers):
                raise ValueError("layer_pattern 可包含 kda 和 mla，缓存需要至少一层 mla 记录历史长度")
            pattern = [names[kind] for kind in layers]
            if self.num_hidden_layers % len(pattern):
                raise ValueError("层数必须是混合注意力周期的整数倍")
            self.layer_types = pattern * (self.num_hidden_layers // len(pattern))
        if self.num_attention_heads <= 0 or self.hidden_size <= 0 or self.hidden_size % self.num_attention_heads:
            raise ValueError("hidden_size 必须能均分给正数个注意力头")
        head_dim = self.hidden_size // self.num_attention_heads
        if self.mla_kv_rank is None:
            self.mla_kv_rank = 2 * head_dim
        if self.mla_shared_dim is None:
            self.mla_shared_dim = head_dim // 2
        if min(self.kda_conv_kernel_size, self.mla_kv_rank, self.mla_shared_dim) < 1 or self.kda_qk_eps <= 0:
            raise ValueError("KDA 卷积宽度、Q/K 归一化 ε 和 MLA 维度必须为正数")
        for bounds in (self.kda_rate_range, self.kda_dt_range):
            if len(bounds) != 2 or not 0 < bounds[0] <= bounds[1]:
                raise ValueError("KDA 初始化区间必须满足 0 < 下界 ≤ 上界")
        super().__post_init__(**kwargs)


class KimiLinearDeltaAttention(nn.Module):
    """逐 token 的 KDA，S 的最后两维分别是 Key 维度和 Value 维度。"""

    def __init__(self, config, layer_idx):
        super().__init__()
        width = config.hidden_size
        self.heads = config.num_attention_heads
        self.dim = width // self.heads
        self.layer_idx = layer_idx
        self.qkv = nn.Linear(width, 3 * width, bias=False)
        # 每个 Q/K/V 通道独立卷积。宽度为 K 的窗口包含当前输入与前 K−1 个有效位置。
        self.conv = nn.Conv1d(3 * width, 3 * width, config.kda_conv_kernel_size, groups=3 * width, bias=False)
        self.qk_eps = config.kda_qk_eps
        self.forget = nn.Sequential(nn.Linear(width, self.dim, bias=False), nn.Linear(self.dim, width))
        self.log_rate = nn.Parameter(torch.zeros(self.heads, 1))
        self.write = nn.Linear(width, self.heads, bias=False)
        self.gate = nn.Sequential(nn.Linear(width, self.dim, bias=False), nn.Linear(self.dim, width, bias=False))
        self.norm = nn.RMSNorm(self.dim, eps=config.rms_norm_eps)
        self.out = nn.Linear(width, width, bias=False)

    def forward(self, x, attention_mask, cache):
        batch, length, width = x.shape
        qkv = self.qkv(x)
        # 每个头一个写入强度 β，每个 Key 分量一个保留率 α。沿 Value 维广播 α 即可逐行衰减 S。
        shape = (batch, length, self.heads, self.dim)
        decay = F.softplus(self.forget(x).reshape(shape).float()) * self.log_rate.float().exp()
        alpha = (-decay).exp()
        beta = self.write(x).float().sigmoid().unsqueeze(-1)
        valid = attention_mask[:, -length:]
        history = cache.get_conv_state(self.layer_idx) if cache is not None else None
        state = cache.get_recurrent_state(self.layer_idx) if cache is not None else None
        if history is None:
            # 通常只存下次还会用到的 K−1 项。K=1 时保留一个槽位供 DynamicCache 标记状态已初始化。
            history = qkv.new_zeros(batch, 3 * width, max(1, self.conv.kernel_size[0] - 1))
        if state is None:
            state = x.new_zeros(batch, self.heads, self.dim, self.dim, dtype=torch.float32)

        outputs = []
        kernel = self.conv.weight[:, 0].to(qkv.dtype)
        for t in range(length):
            # 丢弃最老的位置并放入当前输入。K=1 时窗口只含当前输入，PAD 保留原窗口和递归状态。
            active = valid[:, t, None, None]
            window = torch.cat((history, qkv[:, t, :, None]), dim=-1)[..., -kernel.shape[-1]:]
            filtered = (window * kernel).sum(-1)
            history = torch.where(active, window[..., -history.shape[-1]:], history)
            q, k, v = F.silu(filtered.float()).reshape(batch, 3, self.heads, self.dim).unbind(1)
            # 每个头用 z / √(Σ z² + ε) 归一化 Q、K，再给 Query 乘 1/√d。
            q = q * torch.rsqrt(q.square().sum(-1, keepdim=True) + self.qk_eps) * self.dim**-0.5
            k = k * torch.rsqrt(k.square().sum(-1, keepdim=True) + self.qk_eps)

            # 状态 S 为 [B,H,Dk,Dv]，用 FP32 做递推。用已经衰减的 S 预测 v，写回预测误差：
            # D = Diag(α) S，e = β(v − Dᵀk)，S_new = D + k eᵀ，o = S_newᵀq。
            decayed = alpha[:, t, :, :, None] * state
            predicted = (k.unsqueeze(-1) * decayed).sum(-2)
            error = beta[:, t] * (v - predicted)
            updated = decayed + k.unsqueeze(-1) * error.unsqueeze(-2)
            state = torch.where(active.unsqueeze(-1), updated, state)
            outputs.append((q.unsqueeze(-1) * state).sum(-2))

        if cache is not None:
            cache.update_conv_state(history, self.layer_idx, conv_kernel_size=history.shape[-1])
            cache.update_recurrent_state(state, self.layer_idx)
        # 每个头按 Value 维做 RMSNorm，sigmoid 输出门决定哪些分量传给下一层。
        heads = self.norm(torch.stack(outputs, dim=1))
        gated = heads.flatten(2) * self.gate(x).float().sigmoid()
        return self.out(gated.to(qkv.dtype)) * valid.unsqueeze(-1)


class MultiHeadLatentAttention(nn.Module):
    """NoPE MLA。缓存每个位置的一份潜向量和各头共享的 Key 分量。"""

    def __init__(self, config, layer_idx):
        super().__init__()
        width = config.hidden_size
        self.heads = config.num_attention_heads
        self.dim = width // self.heads
        self.rank = config.mla_kv_rank
        self.shared_dim = config.mla_shared_dim
        self.layer_idx = layer_idx
        self.q = nn.Linear(width, self.heads * (self.dim + self.shared_dim), bias=False)
        self.down = nn.Linear(width, self.rank + self.shared_dim, bias=False)
        self.norm = nn.RMSNorm(self.rank, eps=config.rms_norm_eps)
        self.up = nn.Linear(self.rank, self.heads * 2 * self.dim, bias=False)
        self.out = nn.Linear(width, width, bias=False)

    def forward(self, x, attention_mask, cache):
        batch, length, width = x.shape
        q = self.q(x).reshape(batch, length, self.heads, -1).transpose(1, 2)
        # W_down·x 切成潜向量和共享 Key。c=RMSNorm(潜向量)，s 是所有头共用且不做位置旋转的 Key。
        latent, shared = self.down(x).split((self.rank, self.shared_dim), dim=-1)
        # RMS 的平方和用 FP32 计算，缓存按投影的 dtype 存放。添加的单头维度供所有头共享。
        latent = self.norm(latent.float()).to(latent.dtype).unsqueeze(1)
        shared = shared.unsqueeze(1)
        if cache is not None:
            # 在展开多头 Key 和 Value 之前追加缓存。两份张量的形状都是 [B,1,历史长度,压缩维度]。
            latent, shared = cache.update(latent, shared, self.layer_idx)
        total = latent.shape[2]
        # 各头分别从同一个 c 恢复 (k_h, v_h)。完整 Key 为 [k_h; s]，Value 为 v_h。
        kv = self.up(latent.squeeze(1)).reshape(batch, total, self.heads, 2 * self.dim).transpose(1, 2)
        key, value = kv.chunk(2, dim=-1)
        key = torch.cat((key, shared.expand(-1, self.heads, -1, -1)), dim=-1)

        # 查询 t 可以读到包含自身的位置 past+t。这样整段训练、单 token 解码和多 token 续写共用一个掩码。
        positions = torch.arange(total, device=x.device)
        allowed = (positions[None, :] <= positions[-length:, None]) & attention_mask[:, None, :]
        # 分数为 q_t·[k_j; s_j]/√(d+shared_dim)，每个头按可见位置做 softmax 后对 v_j 加权求和。
        scores = (q @ key.transpose(-2, -1)).float() * q.shape[-1]**-0.5
        allowed = allowed[:, None, :, :]
        scores = scores.masked_fill(~allowed, torch.finfo(scores.dtype).min)
        # 左侧全为 PAD 的查询没有可见 Key，把这一行的权重置零，避免全负无穷的 softmax 产生 NaN。
        weights = scores.softmax(-1).masked_fill(~allowed, 0).to(value.dtype)
        heads = (weights @ value).transpose(1, 2).reshape(batch, length, width)
        return self.out(heads) * attention_mask[:, -length:, None]


class HybridBlock(nn.Module):
    def __init__(self, config, layer_idx):
        super().__init__()
        attention = {"linear_attention": KimiLinearDeltaAttention, "full_attention": MultiHeadLatentAttention}
        self.attention = attention[config.layer_types[layer_idx]](config, layer_idx)
        self.attn_norm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.ffn_norm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.dense = config.dense_ffn
        if self.dense:
            self.mlp = LlamaMLP(config)
        else:
            self.router = MixtralTopKRouter(config)
            self.experts = MixtralExperts(config)

    def forward(self, x, mask, cache):
        x = x + self.attention(self.attn_norm(x), mask, cache)
        h = self.ffn_norm(x)
        if self.dense:
            return x + self.mlp(h), None
        # 沿用基线的 Top-k 路由与专家。保留所有专家的 logits 供训练端计算相同的辅助损失。
        flat = h.flatten(0, 1)
        logits, weights, indices = self.router(flat)
        return x + self.experts(flat, indices, weights).reshape_as(x), logits


class HybridForCausalLM(PreTrainedModel, GenerationMixin):
    config_class = HybridConfig
    _tied_weights_keys = {"lm_head.weight": "embed_tokens.weight"}

    def __init__(self, config):
        super().__init__(config)
        if config.tie_word_embeddings:
            # 词表投影与输入嵌入共享同一参数。保存一份即可，Trainer 续训时会重新绑定。
            self._keys_to_ignore_on_save = ["lm_head.weight"]
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, config.pad_token_id)
        self.layers = nn.ModuleList(HybridBlock(config, i) for i in range(config.num_hidden_layers))
        self.norm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.post_init()

    def _init_weights(self, module):
        super()._init_weights(module)
        # 这两种 Mixtral 模块把多个权重放在裸 Parameter 中，使用与基线相同的初始化。
        if isinstance(module, MixtralExperts):
            nn.init.normal_(module.gate_up_proj, std=self.config.initializer_range)
            nn.init.normal_(module.down_proj, std=self.config.initializer_range)
        elif isinstance(module, MixtralTopKRouter):
            nn.init.normal_(module.weight, std=self.config.initializer_range)
        elif isinstance(module, KimiLinearDeltaAttention):
            # 在零输入下让各通道从不同的衰减速度开始。A 均匀取样，dt 在对数尺度取样。
            module.log_rate.copy_(torch.empty_like(module.log_rate).uniform_(*self.config.kda_rate_range).log())
            bias = module.forget[-1].bias
            lo, hi = self.config.kda_dt_range
            dt = torch.empty_like(bias).uniform_(math.log(lo), math.log(hi)).exp()
            bias.copy_(dt + torch.log(-torch.expm1(-dt)))  # softplus 的反函数，使 softplus(bias)=dt

    def forward(self, input_ids, attention_mask=None, labels=None, cache=None, use_cache=None,
                logits_to_keep=0, num_items_in_batch=None, output_router_logits=False, **kwargs):
        x = self.embed_tokens(input_ids)
        if use_cache is None:
            use_cache = self.config.use_cache and not self.training and labels is None
        if use_cache and cache is None:
            cache = DynamicCache(config=self.config)
        # DynamicCache 从第一个 MLA 层读取已处理长度。KDA 的状态矩阵不含时间轴。
        past = cache.get_seq_length() if cache is not None else 0
        batch, length = input_ids.shape
        if attention_mask is None:
            attention_mask = input_ids.new_ones((batch, past + length))
        mask = attention_mask.bool()
        if mask.shape != (batch, past + length):
            raise ValueError("attention_mask 应覆盖历史和当前 token")
        router_logits = []
        for layer in self.layers:
            x, routes = layer(x, mask, cache)
            if routes is not None and (labels is not None or output_router_logits):
                router_logits.append(routes)
        positions = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
        logits = self.lm_head(self.norm(x[:, positions]))
        aux = loss = None
        if router_logits:
            # M 是所有层的非 PAD 位置数。f_e=专家 e 入选 Top-k 的次数/M，p̄_e 是其平均路由概率。
            # 辅助损失 A_i=E·Σ_e(f_e·p̄_e)。路由均衡时 A_i=k，默认 E=8、k=2，乘系数 0.0005 后为 0.001。
            aux = load_balancing_loss_func(tuple(router_logits), self.config.num_local_experts,
                                           self.config.num_experts_per_tok, mask[:, -length:])
        if labels is not None:
            # 位置 t 的 logits 预测标签 t+1。loss_function 完成移位并忽略 -100，得到交叉熵 C_i/N。
            # N 是 Trainer 传入的整个累积窗口的监督 token 数；独立调用时默认用本批的有效数 n_i。
            loss = self.loss_function(logits, labels, self.config.vocab_size, num_items_in_batch=num_items_in_batch)
            if aux is not None:
                # 本批的总贡献为 (C_i + λ·n_i·A_i)/N。两批各有 2 和 6 个目标时，辅助损失权重为 1/4 和 3/4。
                weight = 1 if num_items_in_batch is None else labels[:, 1:].ne(-100).sum() / num_items_in_batch
                loss = loss + self.config.router_aux_loss_coef * aux * weight
        return MoeCausalLMOutputWithPast(
            logits=logits, loss=loss, aux_loss=aux, cache=cache,
            router_logits=tuple(router_logits) if output_router_logits and router_logits else None,
        )


# 每次启动脚本都注册类型。预训练导出的 config.json 在 SFT、续训和生成进程中都能还原手写模型。
AutoConfig.register(HybridConfig.model_type, HybridConfig)
AutoModelForCausalLM.register(HybridConfig, HybridForCausalLM)


# ==================== 模型结构 ====================
def new_model(tokenizer, width=None, dense=None):
    param = LLM_TRAIN_SETTINGS.param
    width = param.hidden_size if width is None else width
    dense = not param.use_moe if dense is None else dense
    ffn_width = param.intermediate_size
    if ffn_width is None:
        if param.ffn_multiplier <= 0 or param.ffn_multiple_of <= 0:
            raise ValueError("自动计算 FFN 宽度时，倍率与对齐倍数必须为正数")
        ffn_width = math.ceil(width * param.ffn_multiplier / param.ffn_multiple_of) * param.ffn_multiple_of
    if param.num_hidden_layers <= 0 or ffn_width <= 0:
        raise ValueError("层数与 FFN 中间宽度必须为正数")
    # 稠密层让每个 token 经过同一个前馈网络。Mixtral 每层配置 E 个前馈网络（专家），默认 E=8。
    # 对单个 token 的向量 x，路由概率 p=softmax(W_router x)，取概率最大的 k 个专家组成集合 S，默认 k=2。
    # 层内的前馈输出为 Σ[e∈S] p_e·FFN_e(x) / Σ[j∈S] p_j，入选专家的权重之和为 1。
    if not dense and not 1 <= param.moe_num_experts_per_tok <= param.moe_num_experts:
        raise ValueError("每个 token 激活的专家数应在 1 与总专家数之间")
    config = HybridConfig(
        # 词表大小 V 直接取自 tokenizer。形状为 [B,T] 的 token ID 查表后得到 [B,T,H]，
        # B 是 batch 大小，T 是当前序列长度。这些向量依次经过 num_hidden_layers 个 Decoder Block。
        vocab_size=len(tokenizer), hidden_size=width, num_hidden_layers=param.num_hidden_layers,
        # 稠密 FFN 和单个专家都使用 SwiGLU，FFN(x)=W_down(SiLU(W_gate x) ⊙ (W_up x))。
        # ⊙ 表示逐元素乘法。gate 和 up 的输出宽度按原脚本取 64·⌈πH/64⌉，默认 2432，down 再投影回 H。
        intermediate_size=ffn_width, dense_ffn=dense, num_local_experts=param.moe_num_experts,
        num_experts_per_tok=param.moe_num_experts_per_tok, router_aux_loss_coef=param.router_aux_loss_coef,
        # H 维隐藏向量分给 N 个头，每头 d=H/N 维。KDA 按头维护状态，MLA 从共享潜向量展开各头的 Key 和 Value。
        num_attention_heads=param.num_attention_heads, mla_kv_rank=param.mla_kv_rank, mla_shared_dim=param.mla_shared_dim,
        kda_conv_kernel_size=param.kda_conv_kernel_size, kda_qk_eps=param.kda_qk_eps,
        kda_rate_range=param.kda_rate_range, kda_dt_range=param.kda_dt_range,
        # tie_word_embeddings 让输入词表矩阵 E_tok 同时承担输出投影。最终隐藏向量 h 的词表分数为 E_tok·h。
        tie_word_embeddings=param.tie_word_embeddings,
        # 每个 Block 先做 u=x+Attention(RMSNorm(x))，再做 y=u+FFN(RMSNorm(u))，MoE 使用上面的专家加权输出。
        # RMSNorm(x)=g⊙x/√(mean(x²)+ε)，均值沿隐藏维度计算，g 可学习，ε 取 rms_norm_eps。
        rms_norm_eps=param.rms_norm_eps, max_position_embeddings=param.max_position_embeddings,
        # 数据编码、模型和生成器共用起始符 BOS、结束符 EOS 和补齐符 PAD 的 ID。
        bos_token_id=tokenizer.bos_token_id, eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    return HybridForCausalLM(config)


def load_model(path, *, resume=False, **kwargs):
    # 在读取权重前核对模型类型，防止训练或生成时误用其他架构的目录。
    config = AutoConfig.from_pretrained(path)
    if not isinstance(config, HybridConfig):
        raise ValueError(f"{path} 的模型类型为 {config.model_type}，本脚本需要 {HybridConfig.model_type}")
    if resume:
        # train(resume_from_checkpoint=...) 会同时恢复权重与优化器，这里只按检查点的结构和精度建模。
        model = AutoModelForCausalLM.from_config(config)
        if (Path(path) / "generation_config.json").is_file():
            model.generation_config = GenerationConfig.from_pretrained(path)
        return model
    return HybridForCausalLM.from_pretrained(path, config=config, **kwargs)


# ==================== 对话模板与训练样本 ====================
def assistant_template(tokenizer):
    # SFT 需要两份位置对齐的信息，一份记录模型读到的 token，另一份标出哪些位置参与回答的交叉熵。
    # tokenizer 借助 Jinja 的 generation 区间生成第二份信息，模板已经标出区间时直接沿用。
    template = tokenizer.get_chat_template()
    if "{% generation" in template or "{%- generation" in template:
        return template
    # 给文章使用的 MiniMind 模板标出回答范围，保留角色前缀、思考内容、工具调用和结束符的原有排版。
    assistant = '{%- elif message.role == "assistant" %}'
    header = r"'<|im_start|>' + message.role + '\n<think>\n'"
    tool_branch = '{%- elif message.role == "tool" %}'
    if any(template.count(marker) != 1 for marker in (assistant, header, tool_branch)):
        raise ValueError("SFT 需要文章的 MiniMind 模板，或带有 {% generation %} 的模板")
    # 在 assistant 角色前缀之后打开区间，在其结束符和换行之后关闭。用户正文即使引用了
    # 相同的角色标记，也仍由 user 分支渲染。三个替换只调整模板边界，渲染出的对话文本保持一致。
    start = assistant + r"{{- '<|im_start|>assistant\n' }}{% generation %}"
    return template.replace(assistant, start).replace(header, r"'<think>\n'").replace(
        tool_branch, "{%- endgeneration %}" + tool_branch
    )


def encode_chat(sample, tokenizer, template, max_length):
    messages = sample["conversations"]
    tools = None
    for message in messages:
        # system 中的 tools 是可用工具的定义，要作为整段对话的模板参数传入。
        # assistant 的 tool_calls 是该轮实际发出的调用，留在消息里。兼容语料将两者存成 JSON 字符串的写法。
        if message["role"] == "system" and message.get("tools"):
            tools = message["tools"]
            if isinstance(tools, str):
                tools = json.loads(tools)
        if isinstance(message.get("tool_calls"), str) and message["tool_calls"]:
            message["tool_calls"] = json.loads(message["tool_calls"])
    # 一次渲染并编码完整对话。input_ids 和 assistant_masks 经同一次截断后逐位置对应。
    chat = tokenizer.apply_chat_template(
        messages, tools=tools, chat_template=template, return_dict=True,
        return_assistant_tokens_mask=True, truncation=True, max_length=max_length,
    )
    ids = chat["input_ids"]
    # input_ids 保留问题、角色前缀和工具返回值，让后面的回答可以关注它们。labels 在这些位置填 -100，
    # 交叉熵会忽略它们。MiniMind 模板标出的思考内容、回答、工具调用和回答结束符均保留真实 ID。
    return ids, [t if active else -100 for t, active in zip(ids, chat["assistant_masks"], strict=True)]


def training_data(path, stage, max_length, tokenizer):
    # 按 JSONL 行读取，工具定义和调用参数可以是 JSON 字符串或嵌套对象。
    rows = load_dataset("text", data_files=path, split="train")
    template = assistant_template(tokenizer) if stage == "sft" else None

    def encode(batch):
        # 此处的 batch 是 Datasets 一次送来预处理的一批文本行。训练时如何组 batch 由 Trainer 决定。
        samples = [json.loads(line) for line in batch["text"]]
        if template is None:
            # 预留首尾两个位置，手工加一次 BOS 和 EOS。这样长文截断后仍有结束符可学。
            bodies = tokenizer(
                [s["text"] for s in samples], add_special_tokens=False,
                truncation=True, max_length=max_length - 2,
            )["input_ids"]
            ids = [[tokenizer.bos_token_id, *body, tokenizer.eos_token_id] for body in bodies]
            # 例如输入 [BOS, 我, 来, EOS]（假定每个字各占一个 token），标签是 [-100, 我, 来, EOS]。
            # 模型内部把 logits 的第 t 个位置与第 t+1 个标签对齐，实际预测为 BOS→我、我→来、来→EOS。
            return {"input_ids": ids, "labels": [[-100, *seq[1:]] for seq in ids]}
        inputs, labels = [], []
        for sample in samples:
            ids, targets = encode_chat(sample, tokenizer, template, max_length)
            # 第 0 个标签没有对应的前一位置。只保留移位后至少有一个监督目标的对话。
            if any(t != -100 for t in targets[1:]):  # 长提示词可能把所有回答截掉
                inputs.append(ids)
                labels.append(targets)
        return {"input_ids": inputs, "labels": labels}

    # map 把原始行转换为变长的 input_ids 和 labels 两列。补齐推迟到组训练 batch 时进行。
    data = rows.map(encode, batched=True, remove_columns=rows.column_names)
    if not len(data):
        raise ValueError("没有可训练的 token，请检查数据和 --max-length")
    return data


# ==================== 训练与检查点 ====================
def train(args):
    train_config = LLM_TRAIN_SETTINGS.train
    # 1. 确定训练起点。--resume 读取本阶段输出目录中编号最大的 checkpoint-*。
    # 新一轮 SFT 默认从 out/pretrain 的模型权重开始，使用自己的优化器和学习率进度。
    output = Path(args.output)
    checkpoint = get_last_checkpoint(str(output)) if args.resume and output.is_dir() else None
    if args.resume and not checkpoint:
        raise ValueError(f"{output} 中没有可恢复的 Trainer 检查点")
    if not args.resume and output.exists() and any(output.iterdir()):
        raise ValueError(f"{output} 已有文件，请指定新的 --output 或使用 --resume")
    source = checkpoint or args.model
    # 加载权重时同时从其目录读取 tokenizer，保证相同的 ID 仍对应原来的词表项。
    # 从头预训练时由 --tokenizer 提供词表。向右补齐可保持每条输入和标签的起始位置对齐。
    tokenizer = AutoTokenizer.from_pretrained(source or args.tokenizer, padding_side="right")
    if None in (tokenizer.bos_token_id, tokenizer.eos_token_id, tokenizer.pad_token_id):
        raise ValueError("tokenizer 需要定义 BOS、EOS 和 PAD")
    # 2. 在构造模型前设置随机种子，使相同设置下从头训练的初始权重可复现。
    set_seed(train_config.seed)
    if source:
        # 按导出目录记录的层排列和尺寸加载混合模型。
        # 续训也走这一步，随后由 Trainer 恢复优化器、调度器、步数和随机数状态。
        model = load_model(source, resume=args.resume)
    else:
        model = new_model(tokenizer, args.hidden_size, args.dense)
    if not 3 <= args.max_length <= model.config.max_position_embeddings:
        raise ValueError("--max-length 必须在 3 与模型的上下文长度之间")
    # 3. 配置一次参数更新如何取样、如何调整学习率，以及多久保存训练状态。
    options = TrainingArguments(
        output_dir=args.output, num_train_epochs=args.epochs, seed=train_config.seed,
        # 单设备一次前向/反向读 b 条样本（一个 microbatch），累积 G 次后尝试一次更新。
        # 在 W 个普通数据并行进程上，完整窗口共处理 b·G·W 条样本，最后一个窗口可能较短。
        per_device_train_batch_size=args.batch_size, gradient_accumulation_steps=args.accumulation_steps,
        # 默认余弦调度无预热。S 是计划更新步数，s 是已推进步数，r=min_lr_rate。
        # η(s)=η_max·[r+(1−r)·(1+cos(πs/S))/2]。首次更新取 η_max，s=S 时得到下限 r·η_max。
        learning_rate=args.learning_rate, lr_scheduler_type=train_config.lr_scheduler_type,
        lr_scheduler_kwargs=train_config.lr_scheduler_kwargs, weight_decay=train_config.weight_decay,
        max_grad_norm=train_config.grad_clip,
        # bf16=None 时按设备能力选择混合精度。因果交叉熵仍将 logits 转成 FP32 计算。
        bf16=(torch.cuda.is_available() and torch.cuda.is_bf16_supported()) if train_config.bf16 is None else train_config.bf16,
        # 日志和检查点间隔按 Trainer 的 global_step 计数，一个梯度累积窗口结束后计一步。
        # 默认每 125 步保存，最多保留最近两个检查点。report_to 关闭外部实验跟踪服务。
        save_steps=args.save_steps, save_total_limit=LLM_TRAIN_SETTINGS.save.total_limit,
        logging_steps=train_config.logging_steps, report_to=train_config.report_to,
        average_tokens_across_devices=True,
    )
    # 4. 准备训练集。分布式启动时让本机主进程先做预处理，其余进程随后可复用 Datasets 缓存。
    with options.main_process_first():
        data = training_data(args.data, args.stage, args.max_length, tokenizer)

    # 5. 组 batch 并运行训练循环。DataCollatorForSeq2Seq 将较短样本右侧补齐到本批最长序列的长度，
    # 输入补 PAD，labels 补 -100，attention_mask 对真实输入取 1、对补齐位置取 0。
    # Trainer 将 labels 和监督 token 总数传给模型，直接使用 forward 返回的损失做反向传播。
    trainer = Trainer(
        model=model, args=options, train_dataset=data, processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer),
    )
    # Trainer 对各 microbatch 做前向和反向传播并累积梯度，在更新前裁剪所有参数的总梯度范数。
    # 阈值 c=grad_clip，启用裁剪时相当于 g ← g·min(1, c/‖g‖₂)（g 非零，忽略数值保护项）。
    # AdamW 对需要衰减的参数按 θ ← (1−η·weight_decay)θ − η·m̂/(√v̂+ε_opt) 更新。
    # m̂、v̂ 是裁剪后梯度的一阶矩和二阶原始矩经偏差修正后的估计。随后推进学习率并清空梯度。
    trainer.train(resume_from_checkpoint=checkpoint)
    # 6. 导出供下一阶段或推理加载的模型、配置和 tokenizer。旧训练检查点可能把缓存默认值保存为 False。
    model.config.use_cache = True
    trainer.save_model()


# ==================== 自回归推理 ====================
@torch.inference_mode()  # 整个生成过程无需记录用于反向传播的计算图
def generate(args):
    sampling = LLM_TRAIN_SETTINGS.generate
    # 1. 从同一导出目录读取词表、模型配置和权重，按权重配置选择 dtype。eval() 切换到推理模式。
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = load_model(args.model, dtype="auto")
    device = sampling.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()
    if args.raw:
        # 原文续写按预训练的输入格式，从 BOS 和提示正文开始，末尾留给模型继续写。
        ids = [tokenizer.bos_token_id, *tokenizer.encode(args.prompt, add_special_tokens=False)]
    else:
        # 对话按 SFT 时的模板组织。add_generation_prompt=True 在用户消息之后补上助手的开头，
        # MiniMind 模板默认还会填入空思考块，接下来采样的第一个 token 就从这个位置续写。
        ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": args.prompt}], add_generation_prompt=True, return_dict=False,
        )
    # 2. 单条提示组成形状为 [1,P] 的输入，P 包含角色标记等特殊 token。
    # --max-new-tokens 只计新增 token，模型的上下文上限要用 P 加上这个数来检查。
    inputs = torch.tensor([ids], device=model.device)
    if len(ids) + args.max_new_tokens > model.config.max_position_embeddings:
        raise ValueError("提示词与 --max-new-tokens 之和超过模型的上下文长度")
    # 3. 首次前向读入 P 个 token（prefill）。KDA 保留卷积窗口和状态矩阵，MLA 按位置保存潜向量与共享 Key。
    # 此后每步只输入刚生成的 token，各层基于自己的缓存计算这个新位置。
    # 单个未补齐的提示可用全 1 的 attention_mask，模型内部仍使用因果掩码。
    # 采样时，设最后一个位置的词表分数是 z，温度 τ 将概率调整为 softmax(z/τ)。
    # 若生成配置启用了 Top-k，会先限制候选集合。Top-p 再按剩余概率从高到低保留
    # 累计达到 top_p 的最短前缀，重新归一化后随机抽一个 token，遇 EOS 或用完新增长度时结束。
    sampling_args = {"temperature": sampling.temperature, "top_p": sampling.top_p} if sampling.do_sample else {}
    result = model.generate(
        input_ids=inputs, attention_mask=torch.ones_like(inputs), max_new_tokens=args.max_new_tokens,
        do_sample=sampling.do_sample, use_cache=sampling.use_cache, **sampling_args,
    )
    # 4. 解码器模型返回 [提示的 P 个 ID | 新生成的 ID]。取第 0 条的 P 之后部分，
    # 解码时略过 EOS 等特殊 token，终端就只显示本次生成的文本。
    print(tokenizer.decode(result[0, len(ids):], skip_special_tokens=True))


# ==================== 命令行入口 ====================
def main():
    settings = LLM_TRAIN_SETTINGS
    output_root = Path(settings.save.dir)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="stage", required=True)
    for stage in ("pretrain", "sft"):
        # 两个训练阶段共用优化器参数和检查点格式。阶段名同时决定样本编码方式与默认输出目录。
        p = commands.add_parser(stage)
        p.add_argument("data", help="本地 JSONL 文件或通配路径")
        p.add_argument("--output", default=str(output_root / stage))
        p.add_argument("--model", default=str(output_root / "pretrain") if stage == "sft" else None,
                       help="从已有 KDA/MLA 模型目录的权重开始新一轮训练")
        if stage == "pretrain":
            # 从头训练才需要单独给出词表和网络尺寸。加载已有模型时，网络结构随权重目录的 config.json 读取。
            p.add_argument("--tokenizer", default=settings.loader.tokenizer_path)
            p.add_argument("--hidden-size", type=int, default=settings.param.hidden_size)
            p.add_argument("--dense", action=argparse.BooleanOptionalAction, default=not settings.param.use_moe,
                           help="使用稠密前馈层，--no-dense 使用 MoE")
        p.add_argument("--max-length", type=int, default=settings.loader.data_item_max_length)
        p.add_argument("--epochs", type=int, default=settings.train.epochs)
        p.add_argument("--batch-size", type=int, default=settings.train.batch_size)
        p.add_argument("--accumulation-steps", type=int, default=settings.train.accumulation_steps)
        p.add_argument("--learning-rate", type=float, default=settings.train.learning_rate)
        p.add_argument("--save-steps", type=int, default=settings.save.step_interval, help="按优化器更新步数保存")
        p.add_argument("--resume", action="store_true")
    p = commands.add_parser("generate")
    p.add_argument("prompt")
    p.add_argument("--model", default=str(output_root / "sft"))
    p.add_argument("--raw", action="store_true", help="按原始文本续写")
    p.add_argument("--max-new-tokens", type=int, default=settings.generate.max_new_tokens)
    args = parser.parse_args()
    # pretrain → out/pretrain → sft → out/sft，generate 默认加载最后一项。
    # 也可单独调用任一阶段，通过 --model 指定它的输入目录。
    if args.stage == "generate":
        generate(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
