# KDA 分块计算推导

关联文章：[2612.md](../source/post/2026/2612.md)。

KDA 可以沿用 Gated DeltaNet 的残差推导方式：定义实际写入的残差，消去块内中间状态，再把残差方程组织成三角系统。

两条分块公式中的衰减矩阵需要分开定义：状态更新需要“各写入位置到块末”的衰减，输出需要“块起点到各位置”的累计衰减。原论文式 (8)、(9) 也使用了不同的区间上标，不能全部省略成同一个矩阵。参见 [Kimi Linear 论文 §3.1](https://arxiv.org/html/2510.26692v1#S3.SS1)。

以下统一使用原序列位置 $s+u$，块输入状态为 $S_s$，块末状态为 $S_{s+C}$。每个展示公式后都附上对应的 KaTeX 源码，代码块内的内容可以放进双美元符号包围的数学块。

## 向量方向与单步残差

先统一向量方向和维度：

$$
\begin{gathered}
q_{s+u},k_{s+u},\alpha_{s+u}\in\mathbb R^{d_k},
\qquad
v_{s+u},e_{s+u},o_{s+u}\in\mathbb R^{d_v},\\
S_s,S_{s+u}\in\mathbb R^{d_k\times d_v},
\qquad
\beta_{s+u}\in\mathbb R,
\qquad u=1,\ldots,C.
\end{gathered}
$$

```latex
\begin{gathered}
q_{s+u},k_{s+u},\alpha_{s+u}\in\mathbb R^{d_k},
\qquad
v_{s+u},e_{s+u},o_{s+u}\in\mathbb R^{d_v},\\
S_s,S_{s+u}\in\mathbb R^{d_k\times d_v},
\qquad
\beta_{s+u}\in\mathbb R,
\qquad u=1,\ldots,C.
\end{gathered}
```

这里的向量都是列向量，块矩阵按行存放它们的转置。下面先假定各通道门值严格大于零，以便使用逐元素除法；区间衰减本身也可以直接用连乘定义。

把单步更新改写为衰减后的旧状态，加上残差写入：

$$
\begin{aligned}
S_{s+u}
&=\left(I-\beta_{s+u}k_{s+u}k_{s+u}^{\top}\right)
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
+\beta_{s+u}k_{s+u}v_{s+u}^{\top}\\
&=\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
+k_{s+u}e_{s+u}^{\top},\\
e_{s+u}
&:=\beta_{s+u}\left(
v_{s+u}-S_{s+u-1}^{\top}
\operatorname{Diag}(\alpha_{s+u})k_{s+u}
\right),\\
o_{s+u}&=S_{s+u}^{\top}q_{s+u}.
\end{aligned}
$$

```latex
\begin{aligned}
S_{s+u}
&=\left(I-\beta_{s+u}k_{s+u}k_{s+u}^{\top}\right)
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
+\beta_{s+u}k_{s+u}v_{s+u}^{\top}\\
&=\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
+k_{s+u}e_{s+u}^{\top},\\
e_{s+u}
&:=\beta_{s+u}\left(
v_{s+u}-S_{s+u-1}^{\top}
\operatorname{Diag}(\alpha_{s+u})k_{s+u}
\right),\\
o_{s+u}&=S_{s+u}^{\top}q_{s+u}.
\end{aligned}
```

这与 Gated DeltaNet 的处理相同，只是标量衰减变成了按 Key 特征通道衰减。残差已经包含更新强度，所以后面的分块写入不用再额外乘一次更新强度。

## 累计衰减与状态展开

定义当前块的逐通道累计衰减。其中 $\odot$ 表示逐元素乘法，$\oslash$ 表示逐元素除法：

$$
\begin{aligned}
\gamma_{s+u}
&:=\bigodot_{\ell=1}^{u}\alpha_{s+\ell},
&\gamma_s&=\mathbf 1_{d_k},\\
\gamma_{s+u,a}
&=\prod_{\ell=1}^{u}\alpha_{s+\ell,a},
&a&=1,\ldots,d_k,\\
D_{s+u,s+v}
&:=\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
=\operatorname{Diag}\left(
\bigodot_{\ell=v+1}^{u}\alpha_{s+\ell}
\right),
&0&\le v\le u.
\end{aligned}
$$

```latex
\begin{aligned}
\gamma_{s+u}
&:=\bigodot_{\ell=1}^{u}\alpha_{s+\ell},
&\gamma_s&=\mathbf 1_{d_k},\\
\gamma_{s+u,a}
&=\prod_{\ell=1}^{u}\alpha_{s+\ell,a},
&a&=1,\ldots,d_k,\\
D_{s+u,s+v}
&:=\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
=\operatorname{Diag}\left(
\bigodot_{\ell=v+1}^{u}\alpha_{s+\ell}
\right),
&0&\le v\le u.
\end{aligned}
```

与 Gated DeltaNet 不同，这里的累计衰减是一个向量。它在不同 Key 特征通道上可以取不同的值。

将残差形式逐步展开。前两步能直接看出每次写入经过了哪些衰减：

$$
\begin{aligned}
S_{s+1}
&=\operatorname{Diag}(\alpha_{s+1})S_s
+k_{s+1}e_{s+1}^{\top},\\
S_{s+2}
&=\operatorname{Diag}(\alpha_{s+2}\odot\alpha_{s+1})S_s\\
&\quad+\operatorname{Diag}(\alpha_{s+2})
k_{s+1}e_{s+1}^{\top}
+k_{s+2}e_{s+2}^{\top},\\
S_{s+u}
&=\operatorname{Diag}(\gamma_{s+u})S_s\\
&\quad+\sum_{v=1}^{u}
\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
k_{s+v}e_{s+v}^{\top}.
\end{aligned}
$$

```latex
\begin{aligned}
S_{s+1}
&=\operatorname{Diag}(\alpha_{s+1})S_s
+k_{s+1}e_{s+1}^{\top},\\
S_{s+2}
&=\operatorname{Diag}(\alpha_{s+2}\odot\alpha_{s+1})S_s\\
&\quad+\operatorname{Diag}(\alpha_{s+2})
k_{s+1}e_{s+1}^{\top}
+k_{s+2}e_{s+2}^{\top},\\
S_{s+u}
&=\operatorname{Diag}(\gamma_{s+u})S_s\\
&\quad+\sum_{v=1}^{u}
\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
k_{s+v}e_{s+v}^{\top}.
\end{aligned}
```

位置 $s+v$ 的写入，只经过它之后的位置到当前位置的衰减。因而求和中当前位置的写入系数为单位矩阵，不再乘自己的门值。

## 消去块内中间状态

先将状态展开式用于前一个位置，再乘当前门控：

$$
\begin{aligned}
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
&=\operatorname{Diag}(\gamma_{s+u})S_s\\
&\quad+\sum_{v=1}^{u-1}
\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
k_{s+v}e_{s+v}^{\top}.
\end{aligned}
$$

```latex
\begin{aligned}
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}
&=\operatorname{Diag}(\gamma_{s+u})S_s\\
&\quad+\sum_{v=1}^{u-1}
\operatorname{Diag}\left(
\gamma_{s+u}\oslash\gamma_{s+v}
\right)
k_{s+v}e_{s+v}^{\top}.
\end{aligned}
```

把它代入残差的行向量表达式：

$$
\begin{aligned}
e_{s+u}^{\top}
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}k_{s+u}^{\top}
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}\\
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}(\gamma_{s+u}\odot k_{s+u})^{\top}S_s\\
&\quad-\sum_{v=1}^{u-1}\beta_{s+u}
\left[
(\gamma_{s+u}\odot k_{s+u})^{\top}
(k_{s+v}\oslash\gamma_{s+v})
\right]e_{s+v}^{\top}.
\end{aligned}
$$

```latex
\begin{aligned}
e_{s+u}^{\top}
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}k_{s+u}^{\top}
\operatorname{Diag}(\alpha_{s+u})S_{s+u-1}\\
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}(\gamma_{s+u}\odot k_{s+u})^{\top}S_s\\
&\quad-\sum_{v=1}^{u-1}\beta_{s+u}
\left[
(\gamma_{s+u}\odot k_{s+u})^{\top}
(k_{s+v}\oslash\gamma_{s+v})
\right]e_{s+v}^{\top}.
\end{aligned}
```

这一步已经去掉了块内中间状态：当前残差只依赖本块输入、传入状态，以及更早位置的残差，因此可以组织成下三角系统。

## 三角系统与伪值项

按行堆叠本块各位置的向量转置，定义本块矩阵：

$$
\begin{aligned}
Q&=
\begin{bmatrix}
q_{s+1}^{\top}\\
\vdots\\
q_{s+C}^{\top}
\end{bmatrix},
&K&=
\begin{bmatrix}
k_{s+1}^{\top}\\
\vdots\\
k_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_k},\\
V&=
\begin{bmatrix}
v_{s+1}^{\top}\\
\vdots\\
v_{s+C}^{\top}
\end{bmatrix},
&E&=
\begin{bmatrix}
e_{s+1}^{\top}\\
\vdots\\
e_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_v},\\
B&=\operatorname{Diag}
(\beta_{s+1},\ldots,\beta_{s+C})
\in\mathbb R^{C\times C},\\
\Gamma_{\mathrm{pre}}
&=
\begin{bmatrix}
\gamma_{s+1}^{\top}\\
\vdots\\
\gamma_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_k}.
\end{aligned}
$$

```latex
\begin{aligned}
Q&=
\begin{bmatrix}
q_{s+1}^{\top}\\
\vdots\\
q_{s+C}^{\top}
\end{bmatrix},
&K&=
\begin{bmatrix}
k_{s+1}^{\top}\\
\vdots\\
k_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_k},\\
V&=
\begin{bmatrix}
v_{s+1}^{\top}\\
\vdots\\
v_{s+C}^{\top}
\end{bmatrix},
&E&=
\begin{bmatrix}
e_{s+1}^{\top}\\
\vdots\\
e_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_v},\\
B&=\operatorname{Diag}
(\beta_{s+1},\ldots,\beta_{s+C})
\in\mathbb R^{C\times C},\\
\Gamma_{\mathrm{pre}}
&=
\begin{bmatrix}
\gamma_{s+1}^{\top}\\
\vdots\\
\gamma_{s+C}^{\top}
\end{bmatrix}
\in\mathbb R^{C\times d_k}.
\end{aligned}
```

这里特意写成 $\Gamma_{\mathrm{pre}}$，表示块起点到各位置的累计衰减，也避免与关联文章中 Gated DeltaNet 那个按位置对组织的方阵混淆。

残差之间的依赖系数构成严格下三角矩阵。$\operatorname{strictLower}$ 只保留主对角线以下的元素：

$$
\begin{aligned}
H_\gamma
&:=\operatorname{strictLower}\left(
B(\Gamma_{\mathrm{pre}}\odot K)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
\in\mathbb R^{C\times C},\\
(H_\gamma)_{uv}
&=
\begin{cases}
\displaystyle
\beta_{s+u}\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
k_{s+u,a}k_{s+v,a},
&v<u,\\
0,&v\ge u.
\end{cases}
\end{aligned}
$$

```latex
\begin{aligned}
H_\gamma
&:=\operatorname{strictLower}\left(
B(\Gamma_{\mathrm{pre}}\odot K)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
\in\mathbb R^{C\times C},\\
(H_\gamma)_{uv}
&=
\begin{cases}
\displaystyle
\beta_{s+u}\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
k_{s+u,a}k_{s+v,a},
&v<u,\\
0,&v\ge u.
\end{cases}
\end{aligned}
```

这里对 $a$ 的求和发生在 Key 特征维度上。逐通道衰减比例留在特征求和内部，因此一般不能像标量门控那样，从整个点积外面提出一个衰减比例。

将此前残差项移到左侧，再将各行堆起来：

$$
\begin{aligned}
e_{s+u}^{\top}
+\sum_{v=1}^{u-1}(H_\gamma)_{uv}e_{s+v}^{\top}
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}
(\gamma_{s+u}\odot k_{s+u})^{\top}S_s,\\
(I_C+H_\gamma)E
&=BV-B(\Gamma_{\mathrm{pre}}\odot K)S_s.
\end{aligned}
$$

```latex
\begin{aligned}
e_{s+u}^{\top}
+\sum_{v=1}^{u-1}(H_\gamma)_{uv}e_{s+v}^{\top}
&=\beta_{s+u}v_{s+u}^{\top}
-\beta_{s+u}
(\gamma_{s+u}\odot k_{s+u})^{\top}S_s,\\
(I_C+H_\gamma)E
&=BV-B(\Gamma_{\mathrm{pre}}\odot K)S_s.
\end{aligned}
```

左侧系数矩阵是单位下三角矩阵，可以进行三角求解。将本节的三角变换记为 $T_\gamma$：

$$
\begin{aligned}
(I_C+H_\gamma)T_\gamma&=B,
&T_\gamma&=(I_C+H_\gamma)^{-1}B,\\
U_\gamma&:=T_\gamma V
\in\mathbb R^{C\times d_v},
&W_\gamma&:=T_\gamma(\Gamma_{\mathrm{pre}}\odot K)
\in\mathbb R^{C\times d_k},\\
E&=T_\gamma\left(
V-(\Gamma_{\mathrm{pre}}\odot K)S_s
\right)\\
&=U_\gamma-W_\gamma S_s.
\end{aligned}
$$

```latex
\begin{aligned}
(I_C+H_\gamma)T_\gamma&=B,
&T_\gamma&=(I_C+H_\gamma)^{-1}B,\\
U_\gamma&:=T_\gamma V
\in\mathbb R^{C\times d_v},
&W_\gamma&:=T_\gamma(\Gamma_{\mathrm{pre}}\odot K)
\in\mathbb R^{C\times d_k},\\
E&=T_\gamma\left(
V-(\Gamma_{\mathrm{pre}}\odot K)S_s
\right)\\
&=U_\gamma-W_\gamma S_s.
\end{aligned}
```

这就得到了目标公式中的“伪值”项：它正是整块实际写入的残差。两个辅助矩阵只依赖本块输入；传入状态到达后，就能求出残差矩阵。逆矩阵写法用于表达代数关系，实现时可以直接做三角求解。

## 块末状态更新

为表示“各写入位置到块末”的衰减，单独定义另一个矩阵：

$$
\begin{aligned}
(\Gamma_{\mathrm{end}})_{u,:}
&:=\left(
\gamma_{s+C}\oslash\gamma_{s+u}
\right)^{\top}\\
&=\left(
\bigodot_{\ell=u+1}^{C}\alpha_{s+\ell}
\right)^{\top},
\qquad
\Gamma_{\mathrm{end}}\in\mathbb R^{C\times d_k},\\
(\Gamma_{\mathrm{end}})_{C,:}
&=\mathbf1_{d_k}^{\top}.
\end{aligned}
$$

```latex
\begin{aligned}
(\Gamma_{\mathrm{end}})_{u,:}
&:=\left(
\gamma_{s+C}\oslash\gamma_{s+u}
\right)^{\top}\\
&=\left(
\bigodot_{\ell=u+1}^{C}\alpha_{s+\ell}
\right)^{\top},
\qquad
\Gamma_{\mathrm{end}}\in\mathbb R^{C\times d_k},\\
(\Gamma_{\mathrm{end}})_{C,:}
&=\mathbf1_{d_k}^{\top}.
\end{aligned}
```

最后一行全为 1，因为最后一个位置的写入已经位于块末，不再经历后续衰减。

将状态展开式取到块末，并将各次外积相加写成矩阵乘法：

$$
\begin{aligned}
S_{s+C}
&=\operatorname{Diag}(\gamma_{s+C})S_s\\
&\quad+\sum_{u=1}^{C}
\left[
(\gamma_{s+C}\oslash\gamma_{s+u})
\odot k_{s+u}
\right]e_{s+u}^{\top}\\
&=\operatorname{Diag}(\gamma_{s+C})S_s
+(\Gamma_{\mathrm{end}}\odot K)^{\top}E.
\end{aligned}
$$

```latex
\begin{aligned}
S_{s+C}
&=\operatorname{Diag}(\gamma_{s+C})S_s\\
&\quad+\sum_{u=1}^{C}
\left[
(\gamma_{s+C}\oslash\gamma_{s+u})
\odot k_{s+u}
\right]e_{s+u}^{\top}\\
&=\operatorname{Diag}(\gamma_{s+C})S_s
+(\Gamma_{\mathrm{end}}\odot K)^{\top}E.
\end{aligned}
```

转置后的加权 Key 矩阵按列存放各位置的 Key；与残差矩阵相乘，就是沿块内位置求和，将这些外积累加起来。

## 整块输出

由于输出矩阵按行存放，先写单个位置输出的转置：

$$
\begin{aligned}
o_{s+u}^{\top}
&=q_{s+u}^{\top}S_{s+u}\\
&=(\gamma_{s+u}\odot q_{s+u})^{\top}S_s\\
&\quad+\sum_{v=1}^{u}
\left[
(\gamma_{s+u}\odot q_{s+u})^{\top}
(k_{s+v}\oslash\gamma_{s+v})
\right]e_{s+v}^{\top}.
\end{aligned}
$$

```latex
\begin{aligned}
o_{s+u}^{\top}
&=q_{s+u}^{\top}S_{s+u}\\
&=(\gamma_{s+u}\odot q_{s+u})^{\top}S_s\\
&\quad+\sum_{v=1}^{u}
\left[
(\gamma_{s+u}\odot q_{s+u})^{\top}
(k_{s+v}\oslash\gamma_{s+v})
\right]e_{s+v}^{\top}.
\end{aligned}
```

方括号内是一个标量，表示当前 Query 对某次残差写入的读出权重。将这些权重组成矩阵，再保留包含对角线的下三角部分：

$$
\begin{aligned}
A_\gamma
&:=\operatorname{Tril}\left(
(\Gamma_{\mathrm{pre}}\odot Q)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
\in\mathbb R^{C\times C},\\
(A_\gamma)_{uv}
&=
\begin{cases}
\displaystyle
\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
q_{s+u,a}k_{s+v,a},
&v\le u,\\
0,&v>u,
\end{cases}\\
O_{\rm chunk}
&:=
\begin{bmatrix}
o_{s+1}^{\top}\\
\vdots\\
o_{s+C}^{\top}
\end{bmatrix}\\
&=(\Gamma_{\mathrm{pre}}\odot Q)S_s+A_\gamma E
\in\mathbb R^{C\times d_v}.
\end{aligned}
$$

```latex
\begin{aligned}
A_\gamma
&:=\operatorname{Tril}\left(
(\Gamma_{\mathrm{pre}}\odot Q)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
\in\mathbb R^{C\times C},\\
(A_\gamma)_{uv}
&=
\begin{cases}
\displaystyle
\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
q_{s+u,a}k_{s+v,a},
&v\le u,\\
0,&v>u,
\end{cases}\\
O_{\rm chunk}
&:=
\begin{bmatrix}
o_{s+1}^{\top}\\
\vdots\\
o_{s+C}^{\top}
\end{bmatrix}\\
&=(\Gamma_{\mathrm{pre}}\odot Q)S_s+A_\gamma E
\in\mathbb R^{C\times d_v}.
\end{aligned}
```

这里保留对角线，是因为单步读出使用的是完成当前写入后的状态，所以当前位置也要读到自己的残差。

进一步展开到单个输出分量，可以直接看到两层求和：

$$
\begin{aligned}
o_{s+u,j}
&=\sum_{a=1}^{d_k}
\gamma_{s+u,a}q_{s+u,a}(S_s)_{a,j}\\
&\quad+\sum_{v=1}^{u}\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
q_{s+u,a}k_{s+v,a}e_{s+v,j},
\qquad j=1,\ldots,d_v.
\end{aligned}
$$

```latex
\begin{aligned}
o_{s+u,j}
&=\sum_{a=1}^{d_k}
\gamma_{s+u,a}q_{s+u,a}(S_s)_{a,j}\\
&\quad+\sum_{v=1}^{u}\sum_{a=1}^{d_k}
\frac{\gamma_{s+u,a}}{\gamma_{s+v,a}}
q_{s+u,a}k_{s+v,a}e_{s+v,j},
\qquad j=1,\ldots,d_v.
\end{aligned}
```

其中，内层对 Key/Query 特征维度求和，外层对可见的块内位置求和。输出分量固定为 $j$，这里没有对 Value 维度求和。

## 最终分块公式

将残差矩阵代回，得到块末状态更新：

$$
\boxed{
S_{s+C}
=\operatorname{Diag}(\gamma_{s+C})S_s
+(\Gamma_{\mathrm{end}}\odot K)^{\top}
(U_\gamma-W_\gamma S_s)
}
$$

```latex
\boxed{
S_{s+C}
=\operatorname{Diag}(\gamma_{s+C})S_s
+(\Gamma_{\mathrm{end}}\odot K)^{\top}
(U_\gamma-W_\gamma S_s)
}
```

整块输出为：

$$
\boxed{
\begin{aligned}
O_{\rm chunk}
&=\underbrace{
(\Gamma_{\mathrm{pre}}\odot Q)S_s
}_{\text{前块状态的直接读出}}\\
&\quad+
\underbrace{
\operatorname{Tril}\left(
(\Gamma_{\mathrm{pre}}\odot Q)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
}_{\text{块内读出权重}}
\underbrace{
(U_\gamma-W_\gamma S_s)
}_{\text{残差，即伪值项}}.
\end{aligned}
}
$$

```latex
\boxed{
\begin{aligned}
O_{\rm chunk}
&=\underbrace{
(\Gamma_{\mathrm{pre}}\odot Q)S_s
}_{\text{前块状态的直接读出}}\\
&\quad+
\underbrace{
\operatorname{Tril}\left(
(\Gamma_{\mathrm{pre}}\odot Q)
(K\oslash\Gamma_{\mathrm{pre}})^{\top}
\right)
}_{\text{块内读出权重}}
\underbrace{
(U_\gamma-W_\gamma S_s)
}_{\text{残差，即伪值项}}.
\end{aligned}
}
```

块末状态的单个元素也可以写成下面的形式，确认矩阵乘法确实是在累加各位置的写入：

$$
\begin{aligned}
(S_{s+C})_{a,j}
&=\gamma_{s+C,a}(S_s)_{a,j}\\
&\quad+\sum_{u=1}^{C}
\frac{\gamma_{s+C,a}}{\gamma_{s+u,a}}
k_{s+u,a}(U_\gamma-W_\gamma S_s)_{u,j}.
\end{aligned}
$$

```latex
\begin{aligned}
(S_{s+C})_{a,j}
&=\gamma_{s+C,a}(S_s)_{a,j}\\
&\quad+\sum_{u=1}^{C}
\frac{\gamma_{s+C,a}}{\gamma_{s+u,a}}
k_{s+u,a}(U_\gamma-W_\gamma S_s)_{u,j}.
\end{aligned}
```

## 矩阵定义与维度汇总

| 符号 | 形状 | 含义 |
| --- | --- | --- |
| $Q,K$ | $C\times d_k$ | 第 $u$ 行分别为原序列位置 $s+u$ 的 Query、Key 的转置 |
| $V$ | $C\times d_v$ | 本块目标 Value，按行堆叠 |
| $S_s$ | $d_k\times d_v$ | 传入本块的状态 |
| $\gamma_{s+C}$ | $d_k$ | 块起点到块末的逐通道累计衰减 |
| $\Gamma_{\mathrm{pre}}$ | $C\times d_k$ | 每行存放块起点到对应位置的累计衰减 |
| $\Gamma_{\mathrm{end}}$ | $C\times d_k$ | 每行存放对应位置写入后到块末的剩余衰减 |
| $B$ | $C\times C$ | 各位置更新强度构成的对角矩阵 |
| $H_\gamma$ | $C\times C$ | 严格下三角的残差依赖系数 |
| $T_\gamma$ | $C\times C$ | 由单位下三角系统求得的变换 |
| $U_\gamma$ | $C\times d_v$ | 残差中由本块 Value 决定的部分 |
| $W_\gamma$ | $C\times d_k$ | 前块状态对本块残差的预测修正系数 |
| $E$ | $C\times d_v$ | 实际写入的残差，等于最终公式中的伪值项 |
| $A_\gamma$ | $C\times C$ | 含区间衰减和因果掩码的块内读出权重 |
| $O_{\rm chunk}$ | $C\times d_v$ | 按行存放本块输出 |

伪值项本身也依赖传入状态。因此最终输出式的两项描述的是“直接读取前块状态”和“读取本块残差”两条计算路径；若严格按信息来源划分，第二项也包含前块状态带来的预测修正。

## 数值核对记录

本次对话中的数值核对使用 JavaScript 双精度计算，将上述分块结果与原始逐 token 递推进行对照。360 组样例覆盖逐通道衰减、各通道相同的衰减和无衰减情形；状态、残差和输出的最大绝对误差小于 $9\times10^{-16}$。
