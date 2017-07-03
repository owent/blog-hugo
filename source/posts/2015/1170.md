---
title: Vim常用命令
tags:
  - vim
id: 1170
categories:
  - Article
  - Blablabla
  - Work
date: 2015-05-08 11:21:17
---

Vim常用命令
======
<!-- toc -->

之前有搜集过一些常用的命令脚本，其中有vim的部分。但是vim内置的很多功能那些个命令显然是不够的，而且那些记录的很多也不常用，于是想到专门开一个页面记录vim常用的命令集。

常用配置
------
见 https://github.com/owent-utils/vim 

基本命令
------

### 编辑和查看

```vim
/                      # 向下搜索
?                      # 向上搜索 
v                      # 进入可视化模式
Ctrl+v                 # 列编辑模式
    Shift+i            # 多列插入
d[d/w]                 # 剪切[行/单词]
y[y/w]                 # 复制[行/单词]
=[=]                   # 自动缩进[行]
p                      # （查看模式）粘贴
u                      # Undo
Ctrl+r                 # （查看模式）Redo
Ctrl+r Ctrl+"          # （命令行模式/编辑模式）粘贴
:e                     # 更新缓冲区   
```

### 查找和替换

```vim
# 和正则表达式不同的的一个地方在于，用于全字匹配的\b在vim里是 \<\>
:s/src/dst/     # 文本替换(当前行第一个src替换为dst)
:s/src/dst/g    # 文本替换(当前行所有src替换为dst)
:%s/src/dst/g   # 文本替换(所有行第一个src替换为dst)
:%s/src/dst/g   # 文本替换(所有行所有src替换为dst)

:n,$s/          # 从第n行到结尾，类似正则表达式
:%s/            # 全文搜索

*/#             # 在当前文件中搜索当前光标的单词
```

### 分屏和tab
```vim
:tabnew         # 新tab打开
g(t/T)         # (下/上)一个tab

:He[!]          # 上[下]分屏浏览 
:Ve[!]          # 左[右]分屏浏览
Ctrl+w Ctrl+w   # 分屏切换
:set scb[!]     # 开启[关闭]分屏同步移动
:(s/v)plit      # (水平/垂直)分屏打开

```

### 缓冲区和文件系统
```vim
:e . # 打开目录
:E   # 目录导航
:ls  # 列举缓冲区
N Ctrl+^ # 切换缓冲区
```

### 关键字导航
```vim
Ctrl+N               # 向下查找关键字关键字[插入模式下]， Ctrl+P 向上查找关键字[插入模式下]
Ctrl + X 和 Ctrl + D # 宏定义补齐
Ctrl + X 和 Ctrl + ] # 是 Tag 补齐
Ctrl + X 和 Ctrl + F # 是文件名补齐
Ctrl + X 和 Ctrl + I # 也是关键词补齐，但是关键后会有个文件名，告诉你这个关键词在哪个文件中
Ctrl + X 和 Ctrl +V  # 是表达式补齐
Ctrl + X 和 Ctrl +L  # 对整行补齐。
```

常用指令
------
```vim
:%!python -m json.tool  # jsom 格式化
:%!xxd[ -r]             # 转入[转出]为16进制查看
gg=G                    # 全文自动缩进
:set encoding=utf8      # 设置显示编码
:set fileencoding=utf-8 # 文件编码转换
:help encoding-values   # 列举支持得编码
:setl ff=[dos/unix/mac] # 行尾格式转换
```
