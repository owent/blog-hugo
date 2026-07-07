---
title: About
id: 1
type: "page"
date: 2009-09-01
noad: true
---

<style>
/* shields.io 徽章按内联显示，避免被主题默认的 display:block 拆到单独一行 */
img[src*="img.shields.io"] { display: inline-block !important; vertical-align: middle; margin: 0 2px; }
</style>

| 欧文韬 / OWenT |
| ------------------------------------------------------- | --------------------------------------------------------------- |
| Blog：<https://owent.net>                               | Github：<https://github.com/owent>                              |
| 地点： 上海                                             | ORCID：<https://orcid.org/0009-0005-4478-9343>                  |
| E-Mail（主）：[admin@owent.net](mailto:admin@owent.net) | E-Mail（备）：[owt5008137@live.com](mailto:owt5008137@live.com) |

## 关于我

本人主要从事 C++ 后端基础设施、运行时与并发库、游戏服务端开发框架和解决方案、可观测性、构建工具链和跨平台工程也折腾了不少。

[这个博客](https://owent.net)的目的是记录工程里反复出现的问题、踩坑记录和设计复盘，并沉淀成可复用的底层能力。包括但不限也方便有兴趣的小伙伴们一起交流探讨。

## 技术领域

| 领域               | 代表产出 / 关键技术                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 运行时与并发       | [libcopp](https://github.com/owent/libcopp)：跨平台 C++ 协程库（Linux / macOS / Windows / MinGW），从 stackful 到 C++20 stackless，含任务调度、channel、栈池、Intel TSX、Windows Fiber；并附 vs goroutine / libco / libgo / ucontext 的 benchmark                                                                                                                                                                       |
| 后端与分布式架构   | [atframework](https://github.com/atframework) 生态（[libatbus](https://github.com/atframework/libatbus) / [libatapp](https://github.com/atframework/libatapp) / [atsf4g-co](https://github.com/atframework/atsf4g-co)）：全异步游戏服务器框架，含服务端通信系统、CS通信系统和网关服务、etcd 服务发现、拓扑驱动路由与重连、RPC 流量治理、WAL、有状态对象路由、分布式事务、分布式消息队列、以及各种游戏服务端工程解决方案 |
| 可观测性           | [opentelemetry-cpp](https://github.com/open-telemetry/opentelemetry-cpp)（核心贡献者 / Approver）：游戏服务的 metrics / tracing / logs 建设，Prometheus 指标、ELK、基于指标的 HPA 与动态策略                                                                                                                                                                                                                            |
| 构建与工具链       | [cmake-toolset](https://github.com/atframework/cmake-toolset)（兼容 vcpkg、定制能力更强）；长期维护的 [GCC](https://github.com/owent/bash-shell/tree/main/GCC%20Installer) / [Clang+LLVM+libc++](https://github.com/owent/bash-shell/tree/main/LLVM%26Clang%20Installer) 构建脚本；GitHub Actions 与自动分析                                                                                                            |
| 跨平台与客户端底层 | UE / Unity 服务端接入（atgateway 与 C# / 纯 C binding）；ECDH 密钥交换、AEAD、协议协商；protobuf 动态 Message（非反射）；LRU 缓存、bsdiff 差分更新；iOS / Android 交叉编译                                                                                                                                                                                                                                              |
| 数据管线与代码生成 | [xresloader](https://github.com/owent/xresloader)：Excel → Protobuf / Msgpack / Lua / JS / JSON / Xml / UE DataTable；[xres-code-generator](https://github.com/owent/xres-code-generator) 读表代码生成                                                                                                                                                                                                                  |
| 多语言生态         | Rust（[wxwork_robotd](https://github.com/owent/wxwork_robotd)、[ddns-cli](https://github.com/owent/ddns-cli)）、Go（[coredns-filter](https://github.com/owent/coredns-filter)、[coredns-nftables](https://github.com/owent/coredns-nftables)）、Java（xresloader）                                                                                                                                                      |

## 开源贡献

我主要维护或长期参与的开源项目：

- **[OpenTelemetry C++](https://github.com/open-telemetry/opentelemetry-cpp)（CNCF 项目）**：核心贡献者 / Approver，2021 年至今。
- **[libcopp](https://github.com/owent/libcopp)** ![GitHub stars](https://img.shields.io/github/stars/owent/libcopp?style=social) ![release](https://img.shields.io/github/v/release/owent/libcopp?style=flat)：跨平台 C++ 协程库，已收录 [vcpkg](https://github.com/microsoft/vcpkg/tree/master/ports/libcopp)。
- **[xresloader](https://github.com/owent/xresloader)** ![GitHub stars](https://img.shields.io/github/stars/owent/xresloader?style=social) ![downloads](https://img.shields.io/github/downloads/owent/xresloader/total)：一套跨平台的 Excel 转表**工具链**（[文档站](https://xresloader.atframe.work)），核心引擎可把 Excel 导出为 Protobuf / Msgpack / Lua / JS / JSON / Xml / UE DataTable。其它组件：
    - [xresconv-cli](https://github.com/owent/xresconv-cli) — 跨平台批量转表 CLI
    - [xresconv-gui](https://github.com/owent/xresconv-gui) ![downloads](https://img.shields.io/github/downloads/owent/xresconv-gui/total) — 跨平台批量转表 GUI
    - [xres-code-generator](https://github.com/owent/xres-code-generator) — 读表代码生成器
    - [xresloader-dump-bin](https://github.com/owent/xresloader-dump-bin) — 二进制 dump 工具
- **[atframework](https://github.com/atframework)**：高性能、全异步、跨平台、去中心化的游戏服务器框架生态，包含 [Utility 库](https://github.com/atframework/atframe_utils)、[libatbus 高性能进程间通信](https://github.com/atframework/libatbus)\(小包单线程百万级QPS，大包单线程12Gbps/5Gbps吞吐\)、[libatapp 应用框架](https://github.com/atframework/libatapp)、[atsf4g-co 完整解决方案](https://github.com/atframework/atsf4g-co)、[cmake-toolset 构建系统](https://github.com/atframework/cmake-toolset)、[atgateway 的 C# 适配（可用于 Unity）](https://github.com/atframework/AtgwInnerCli-CSharp) 等等。
- **[AICodeReviewer](https://github.com/atframework/AICodeReviewer)（AICR）**：自托管的多 VCS AI 代码审查编排服务。把 GitHub / Gitea / GitLab / P4 / SVN 等触发统一成一条 review 流水线，在沙箱里跑自选 agent（Kilo Code、Claude Code、opencode、Zoo Code、Copilot CLI），产出结构化结论回写到 PR 评论、issue 或 IM 机器人；带密钥脱敏、Prometheus 指标和 LLM 成本看板。[文档站](https://aicr.atframe.work)。
- **[hiredis-happ](https://github.com/owent/hiredis-happ)**：Redis 高可用接入，较早支持 redis cluster，带自动重试、断线重连、按需连接。
- **[upload-to-github-release](https://github.com/xresloader/upload-to-github-release)**：GitHub Action，已上架 [Marketplace](https://github.com/marketplace/actions/upload-to-github-release)。

其它还有 [ddns-cli](https://github.com/owent/ddns-cli)、[wxwork_robotd](https://github.com/owent/wxwork_robotd)（企业微信机器人）、[coredns-filter](https://github.com/owent/coredns-filter) / [coredns-nftables](https://github.com/owent/coredns-nftables)、[WP-Code-Highlight.js](https://wordpress.org/plugins/wp-code-highlightjs/)，以及这个博客的主题 [hugo-theme-distinctionpp](https://github.com/owent/hugo-theme-distinctionpp)。生命不息，折腾不止，平常写的小玩具就不一一列举了。

## 工作经历与项目代号

只列时间线和代号，具体业务实现就不展开了。

| 时间              | 公司 / 组织                      | 角色                                        | 参与项目（代号）                                                                                                                            |
| ----------------- | -------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026.07 – 至今    | \*\*\*                           | —                                           | —                                                                                                                                           |
| 2025.09 – 2026.06 | 游幻科技（上海）（追觅科技旗下） | 服务端技术负责人                            | UE / Unity 多语言生态游戏服务器、跨平台构建与研发工具、云原生与运维体系                                                                     |
| 2017.09 – 2025.08 | 腾讯科技（上海）· 北极光工作室   | 后台组 · 专家工程师，部分项目的服务端主程序 | Maple，UE 搜打撤、TGF，UE 搜打撤，Pix（UE 大乱斗）、《钢之炼金术师》《疯狂动物城》手游；云观（可观测性 OTeam）、TDXA（分布式事务 OTeam）PMC |
| 2016.10 – 2017.07 | 上海格奕网络科技                 | 后端技术负责人                              | 酋长万岁（手游 MMORPG）                                                                                                                     |
| 2014.10 – 2016.10 | 上海莫游网络科技                 | 联合创始人、CTO                             | 战将天下（手游 卡牌）                                                                                                                       |
| 2012.06 – 2014.10 | 腾讯科技（上海）· 北极光工作室   | 后台开发                                    | Paradise Life（Facebook 页游 SLG）、QQ 天堂岛、Lutos、Milan、Pluto、Polar、Chuzzle                                                          |
| 2011.06 – 2012.06 | 腾讯科技（上海）· 北极光工作室   | 实习                                        | —                                                                                                                                           |

> 很多早期维护的工具（比如：自动构建与发布平台、公共库、自动化自测和压测工具）基本都沉淀进了 atframework 和相关工具链。
> 但是由于精力有限，很多周边小工具可能不会很活跃。

## 教育

- 华东理工大学，计算机科学与技术，本科（2008.09 – 2012.06）
- 在校项目：集成 GIS 与 OSG 的虚拟应急救援系统（国家级大学生创新项目，组长）；基于 WebService 的高校教学科研管理平台（校 USRP 项目，组长）

## 获奖与专利

- 2010.10 第 35 届 ACM-ICPC 亚洲区预选赛（天津赛区）银奖
- 2009.12 “中国电机工程学会杯”全国大学生电工数学建模竞赛 三等奖
- 2009.12 / 2012.09 国家励志奖学金 / 校一等奖学金（华东理工大学）
- 专利 ZL 2021 1 0187616.4 《一种远程过程调用 RPC 服务调用方法和相关装置》
- 专利 ZL 2019 1 0193906.2 《应用复盘校验处理方法及系统》
