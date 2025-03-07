---
title: About
id: 2
type: "page"
date: 2025-01-01
noad: true
---

| 欧文韬                    | TEL. 18601690140                                                |
| ------------------------- | --------------------------------------------------------------- |
| 性别： 男                 | E-Mail\(主\): [admin@owent.net](mailto:admin@owent.net)         |
| Blog: <https://owent.net> | E-Mail\(备\): [owt5008137@live.com](mailto:owt5008137@live.com) |

# 工作学习经历

* 2017.09-至今: 腾讯科技\(上海\)有限公司 - 北极光工作室后台组
* 2016.10-2017.07: 上海格奕网络科技有限公司 - 后端技术负责人
* 2014.10-2016.10: 上海莫游网络科技有限公司 - 联合创始人、CTO
* 2012.06-2014.10: 腾讯科技\(上海\)有限公司 - 北极光工作室后台组
* 2011.06-2012.06: 腾讯科技\(上海\)有限公司 - 北极光工作室后台组 - 实习
* 2008.09-2012.06: 华东理工大学 - 计算机科学与技术 - 本科

# 主要开源活动

* Github-主站: <https://github.com/owent>
* Github-【CNCF云原生计算基金会-可观测性领域-opentelemetry-cpp核心贡献者】: <https://github.com/open-telemetry/opentelemetry-cpp>
* Excel转表工具集（Excel -&gt; Protobuf、Lua、Msgpack、Json、Xml\Javascript、UnrealEngine DataTable）: <https://github.com/xresloader>

> 1. 文档: <https://xresloader.atframe.work>
> 3. 转表核心引擎: [xresloader](https://github.com/xresloader/xresloader)
> 4. 批量转表规范: [xresconv-conf](https://github.com/xresloader/xresconv-conf)
> 5. 跨平台批量转表CLI工具: [xresconv-cli](https://github.com/xresloader/xresconv-cli)
> 6. 跨平台批量转表GUI工具: [xresconv-gui](https://github.com/xresloader/xresconv-gui)
> 7. 读表代码生成器: [xres-code-generator](https://github.com/xresloader/xres-code-generator)
>   * 支持 C\+\+ 、Lua（裸Lua,lua-protobuf,upb-lua,pbc-lua）、C\#\(Unity\)
>   * 支持多版本并存、多级索引、多重索引
> 8. 二进制Dump工具: [xresloader-dump-bin](https://github.com/xresloader/xresloader-dump-bin)

* 高性能、全异步、跨平台、去中心化游戏服务器框架\([atframework](https://atframe.work/)\): https://github.com/atframework

> * [Utility库](https://github.com/atframework/atframe_utils)
>   * 单元测试框架
>   * C++17、20、23、26部分能力适配下放
>   * 常见容器和算法：jiffies_timer、LRUMap、混合LRU资源池、AC自动机、CLI和命令行工具、字符串算法、随机数算法、状态机、无锁容器、内存管理模块、通用WAL模块等等
>   * 常见开源库跨版本适配封装: 加密和Hash算法类（openssl,libressl,mbedtls,libsodiom）、网络类（curl，query string标准算法）、protobuf适配层、GSL适配等
> * [libatbus - 高性能进程间通信和管理](https://github.com/atframework/libatbus)
>   * 单进程单线程+TCP通道: 2800+K/QPS和600+MB/s吞吐量
>   * 单进程单线程+共享内存通道: 5000+K/QPS和1.5+GB/s吞吐量
>   * 无锁队列支持多（进程/线程）写单（线程）读
> * [libatapp - 服务器应用框架](https://github.com/atframework/libatapp)
>   * 动态Worker（线程）池
>   * 服务发现，基于标签集合的策略路由（类似K8S微服务框架流量治理，支持一致性Hash、RoundRobin、随机、顺序等）
>   * 端点管理、IO能力抽象。支持自定义协议IO层。
> * [atsf4g-co - 完整游戏服务器解决方案](https://github.com/atframework/atsf4g-co)
>   * 包含服务器代理进程atproxy（使用etcd实现去中心化）
>   * 包含客户端网关层进程atgateway
>     * 自有协议、动态密钥加密、断线重连管理、网络优化、资源控制、纯C客户端API
>   * 示例的echosvr、loginsvr、gamesvr、分布式事务解决方案、异步队列（一致性问题）方案等
>   * 示例的协程RPC框架和任务管理
>   * 可观测性接入，通用动态策略能力
>   * 基于指标的适用于所有长状态、短状态和无状态服务的HPA能力支持和云原生支持
> * [cmake-toolset - 跨平台构建系统](https://github.com/atframework/cmake-toolset)
>   * 支持 Windows,Linux,macOS,Android,iOS
>   * 适配 UnrealEngine UBT 和 Unity 支持
> * [AtgwInnerCli-CSharp - atgateway的C\#适配](https://github.com/atframework/AtgwInnerCli-CSharp)（纯C客户端API的包装，可用于Unity 3D）

* Redis高可用解决方案:  [hiredis-happ](https://github.com/owent/hiredis-happ)\(首先支持redis cluster集群，支持自动重试、断线重连、按需连接\)
* 高性能、跨平台C++协程框架: [libcopp][1]
  * 跨平台支持 Windows,macOS,Linux
  * 多种栈管理方式（malloc,mmap,VirtualAlloc,动态分割栈）、自适应动态栈池等
  * C++20协程支持
  * 支持任务编排，channel组件等
* Github release集成工具: [Upload To Github Release][3] , 商店地址: <https://github.com/marketplace/actions/upload-to-github-release>
* DDNS工具(Rust lang): [ddns-cli](https://github.com/owent/ddns-cli)
* 企业微信机器人服务(Rust lang): [wxwork_robotd](https://github.com/owent/wxwork_robotd)
* coredns插件-返回记录过滤(golang): [coredns-filter](https://github.com/owent/coredns-filter)
* coredns插件-nftables集成(golang): [coredns-nftables](https://github.com/owent/coredns-nftables)
* Github-个人Utility工具集: <https://github.com/owent-utils>
* 编译器构建脚本(最新版本 [GCC](https://github.com/owent/bash-shell/tree/main/GCC%20Installer)和[Clang+LLVM+Libc++](https://github.com/owent/bash-shell/tree/main/LLVM%26Clang%20Installer))
* WordPress代码高亮插件: [WP-Code-Highlight.js](https://wordpress.org/plugins/wp-code-highlightjs/)
* 静态化博客系统主题 [hexo-theme-distinctionpp](https://github.com/owent/hexo-theme-distinctionpp)、[hugo-theme-distinctionpp](https://github.com/owent/hugo-theme-distinctionpp)

生命不息，折腾不止，平常写的小玩具和小工具就不列举了。

# 项目

## 2017年09月 — 至今：腾讯科技（上海）有限公司

* TGF - UE - PC,搜撤(国服版本主程序)
* Pix - UE - PC+手机,大乱斗(主程序)
* 《钢之炼金术师》 - 手游
* 《疯狂动物城》 - 手游 - 三消+养成

---

> * 游戏服务器架构建设、优化，系统方案设计和部分实现
>   * 基于 [libcopp][1] 的统一RPC框架，相关的监控、容灾体系。
>     * DAG能力
>     * C++20协程支持
>     * 传统有栈协程和C++20协程差异性抽象和一键切换
>   * 公共组件和解决方案:
>     * 分布式消息队列
>     * 分布式事务
>     * 通用动态策略系统框架
>     * 上云和HPA能力（基于指标，适用于各类长状态、短状态和无状态服务）
>     * 可观测性能力建设
>     * 通用公会服务、好友服务、异步队列、邮件系统、交易行系统（拍卖+证券交易类）等等
> * 模板引擎和代码生器
> * 转表工具链 [xresloader][2] 和相关编辑器(UnrealEngine)支持。支持各类数据交叉校验
> * 跨平台开发支持（客户端、服务器共享模块）
> * 开发CI和CD流程优化，自动分析工具，LLM集成
> * 基于nodejs,webpack和websocket的GM工具

## 2016年10月 — 2017年07月：上海格奕网络科技有限公司

* 酋长万岁 - 手游 - MMORPG

> * 服务器框架维护和优化（包含负载均衡、故障转移等，主要是[atframework](https://github.com/atframework)）
> * 游戏服务器架构设计和开发，系统方案设计和部分实现
>   * 跨平台转表工具及加载
>     * 系统支持 linux、macOS、Windows、Android、iOS
>     * 语言支持: c++、lua和c\#\(unity+mono,.net core, .net framework\)、javascript、python等
>   * 自研协程系统和相应的调度器和RPC系统及协程栈池
>   * 自研redis cluster高可用接入方案
>   * 各项服务器系统接入的Unity 3D适配（atframework的网关层接入、断线重连、客户端加密和密钥交换和网络层优化，转表工具支持）
>   * 服务器框架的跨语言支持（实现了纯C binding和C# binding）
> * 内部devops工具、发布工具的开发和维护（包含自研开发发布工具、jenkins等）
> * 客户端部分底层模块的适配和优化(主要是接入Protobuf v3的动态Message的非反射实现)
> * 客户端脚本化打包流程和持续集成
> * 服务器部分逻辑和性能分析及优化
> * 程序组项目团队管理和质量控制
> * 周边工具的开发与维护

## 2014年10月 — 2016年10月：上海莫游网络科技有限公司

* 战将天下 - 手游 - 卡牌

> * 服务器框架维护和优化（包含负载均衡、故障转移等）
> * 游戏服务器架构设计和开发，系统方案设计和部分实现
>   * 包含不停服更新、加密和反作弊、断线重连、（灰度）多平台更新策略等
>   * 跨平台转表工具及加载
>     * 系统支持: linux、macOS、Windows、Android和iOS
>     * 语言支持: lua、c++、javascript、python等
>   * 自研协程系统和响应的调度器和RPC系统
>   * 自研redis cluster高可用接入方案
>   * 实现不停服更新
> * 内部devops工具、发布工具和运维系统的开发和维护（包含自研开发发布工具、jenkins、仓库管理、运维系统等）
> * 客户端底层模块的设计、性能分析和优化（如：自适应LRU内存缓存系统、资源加密方案、基于bsdiff的差分更新等）
> * 服务器部分逻辑和性能分析及优化
> * 程序组项目进度管理，质量控制和团队管理
> * 产品方向性讨论、系统设计和功能设计
> * 程序组人才培养
> * 周边工具的开发与维护

## 2011年06月 — 2014年10月：腾讯科技（上海）有限公司

* Paradise Life项目后台开发 - Facebook - 页游 - SLG
* QQ天堂岛页面开发 - 页游 - SLG
* Lutos项目后台开发 - 页游 - RPG
* Milan项目后台开发 - 页游 - 养成类
* Pluto项目后台开发 - 页游 - RPG
* Polar项目后台开发 - 手游 - 休闲类
* Chuzzle项目后台开发 - 手游 - 休闲类
* 北极光Seed&手游项目组自动构建&发布平台开发维护
* 北极光Seed&手游项目组公共库开发及维护
* 北极光Seed&手游项目组后台自动化自测、压测工具开发及维护

## 2010年09月 — 2012年06月：华东理工大学

* 集成GIS与OSG的虚拟应急救援系统关键技术研究和实现 - 国家级大学生创新项目，项目编号：101025126，项目组组长
* 基于WebService的高校教学科研管理平台设计与开发 - 校USRP项目，项目编号：20100732，项目组组长

# 获奖经历

1. 2009年12月 华东理工大学，国家励志奖学金
2. 2009年12月 “中国电机工程学会杯”全国大学生电工数学建模竞赛，三等奖
3. 2010年10月 ACM（Association for Computing Machinery,国际计算机协会） 第35届 ACM-ICPC 亚洲区预选赛-天津赛区，银奖
4. 2012年09月 华东理工大学，校一等奖学金
5. 2014年8月 腾讯科技（上海）有限公司，年中考评：5星（优秀）

# 技术栈/关键字

编程语言: c/c++(11/14/17/20/23/26),bash,cmake,lua,python,javascript,typescript,c#,html,java,less,sass,php,sql,rust,go,markdown,restructuredtext

框架和服务: redis,msgpack,protobuf,flatbuffers,ci,unity,cocos2d-x,cap’n proto,gRPC,mono/.net core,elasticsearch,logstash,kibana,nodejs,webpack,next.js,k8s,kubernates,prometheus,opentelemetry,litellm,lobechat

主题: 计算机算法,分布式系统,计算机网络,游戏服务器架构设计和开发,分布式事务,可观测性,linux环境编程,操作系统,编译原理,设计模式,协程,coroutine,vscode插件开发,wordpress插件及主题开发,github action

工具: git,svn,p4,pandoc,graphviz,valgrind,gdb/lldb,perf,gperf,binutils/readelf/tcpdump等,mingw,msys,wsl,qemu,kvm,docker,podman,coredns

[1]: https://github.com/owent/libcopp
[2]: https://xresloader.atframe.work/
[3]: https://github.com/xresloader/upload-to-github-release
