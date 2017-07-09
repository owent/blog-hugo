---
title: About
id: 1
type: "page"
date: 2009-09-01
---

| 欧文韬 | TEL. 18601690140 |
| --- | --- |
| 性别： 男 | E-Mail\(主\): [admin@owent.net](mailto:admin@owent.net) |
| Blog: [https://owent.net](https://owent.net) | E-Mail\(备\): [owt5008137@live.com](mailto:owt5008137@live.com) |

# 工作学习经历

* 2008.09-2012.06: 华东理工大学 - **计算机科学与技术**专业 - **本科**
* 2011.06-2012.06: 腾讯科技\(上海\)有限公司 - 北极光工作室后台组 - 实习
* 2012.06-2014.10: 腾讯科技\(上海\)有限公司 - 北极光工作室后台组 - 成员
* 2014.10-2016.10: 上海莫游网络科技有限公司 - 联合创始人、CTO
* 2016.10-至今: 上海格奕网络科技有限公司 - 后端技术负责人

# 项目经历

## 2016年10月 — 至今：上海格奕网络科技有限公司

* &lt;保密&gt; - 手游 - MMORPG
  > * 服务器框架维护和优化（包含负载均衡、故障转移等，主要是[atframework](https://github.com/atframework)）
  > * 游戏服务器架构设计和开发，系统方案设计和部分实现
  >   * 跨平台转表工具及加载
  >     * 系统支持 linux、macOS、Windows、Android、iOS
  >     * 语言支持: c++、lua和c\#\(unity+mono,.net core, .net framework\)
  >   * 自研协程系统和相应的调度器和RPC系统及协程栈池
  >   * 自研redis cluster高可用接入方案
  >   * 各项服务器系统接入的Unity 3D适配
  > * 内部devops工具、发布工具的开发和维护（包含自研开发发布工具、jenkins等）
  > * 客户端部分底层模块的适配和优化
  > * 服务器部分逻辑和性能分析及优化
  > * 参与程序组项目团队管理和质量控制
  > * 周边工具的开发与维护

## 2014年10月 — 2016年10月：上海莫游网络科技有限公司

* 战将天下 - 手游 - 卡牌
  > * 服务器框架维护和优化（包含负载均衡、故障转移等）
  > * 游戏服务器架构设计和开发，系统方案设计和部分实现
  >   * 包含不停服更新、加密和反作弊、断线重连、（灰度）多平台更新策略等
  >   * 跨平台转表工具及加载
  >     * 系统支持: linux、macOS、Windows、Android和iOS
  >     * 语言支持: lua和c++
  >   * 自研协程系统和响应的调度器和RPC系统
  >   * 自研redis cluster高可用接入方案
  > * 内部devops工具、发布工具和运维系统的开发和维护（包含自研开发发布工具、jenkins、仓库管理、运维系统等）
  > * 客户端底层模块的设计、性能分析和优化（如：自适应LRU内存缓存系统、资源加密方案、基于bsdiff的差分更新等）
  > * 服务器部分逻辑和性能分析及优化
  > * 程序组项目进度管理，质量控制和团队管理
  > * 参与产品方向性讨论、系统设计和功能设计
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

# 主要开源活动

* Github-主站: [https://github.com/owt5008137](https://github.com/owt5008137)

* Github-个人Utility工具集: [https://github.com/owent-utils](https://github.com/owent-utils)

* Github-参与的开源项目: [https://github.com/owent-contrib](https://github.com/owent-contrib)

* Excel转表工具集（Excel -&gt; Protobuf、Lua、Msgpack、Json、Xml）

  > xresloader – [https://github.com/xresloader](https://github.com/xresloader)
  >
  > 1. 转表核心引擎: [xresloader](https://github.com/xresloader/xresloader)
  > 2. 批量转表规范: [xresconv-conf](https://github.com/xresloader/xresconv-conf)
  > 3. 跨平台批量转表CLI工具: [xresconv-cli](https://github.com/xresloader/xresconv-cli)
  > 4. 跨平台批量转表GUI工具: [xresconv-gui](https://github.com/xresloader/xresconv-gui)

* 高性能、全异步、跨平台、去中心化游戏服务器框架\([atframework](https://atframe.work/)\): [https://github.com/atframework](https://github.com/atframework)

  > * [Utility](https://github.com/atframework/atframe_utils)
  > * [libatbus - 高性能进程间通信和管理](https://github.com/atframework/libatbus) 
  >   * 单进程单线程+TCP通道: 2800+K/QPS和600+MB/s吞吐量
  >   * 单进程单线程+共享内存通道: 5000+K/QPS和1.5+GB/s吞吐量
  >   * 无锁队列支持多（进程/线程）写单（线程）读
  > * [libatapp - 服务器应用框架](https://github.com/atframework/libatapp)
  > * [atsf4g-co - 完整游戏服务器解决方案](https://github.com/atframework/atsf4g-co)
  >   * 包含服务器代理进程atproxy（使用etcd实现去中心化）
  >   * 包含客户端网关层进程atgateway
  >     * 自有协议、动态密钥加密、断线重连管理、网络优化、资源控制、纯C客户端API
  >   * 示例的echosvr、loginsvr和gamesvr
  >   * 示例的协程RPC和任务管理
  > * [AtgwInnerCli-CSharp - atgateway的C\#适配](https://github.com/atframework/AtgwInnerCli-CSharp)（纯C客户端API的包装，可用于Unity 3D）

* 高性能、跨平台C++协程框架: [libcopp – https://github.com/owt5008137/libcopp](https://github.com/owt5008137/libcopp)

* cmake 的一些扩展模块和C++版本适配方案: [https://github.com/owent-utils/cmake](https://github.com/owent-utils/cmake)

* 编译器构建脚本

  > GCC:  [https://github.com/owent-utils/bash-shell/tree/master/GCC%20Installer](https://github.com/owent-utils/bash-shell/tree/master/GCC Installer)
  >
  > Clang+LLVM+Libc++: [https://github.com/owent-utils/bash-shell/tree/master/LLVM%26Clang%20Installer](https://github.com/owent-utils/bash-shell/tree/master/LLVM%26Clang Installer)

* WordPress代码高亮插件: WP-Code-Highlight.js

  > 仓库地址: [https://github.com/owt5008137/WP-Code-Highlight.js](https://github.com/owt5008137/WP-Code-Highlight.js)
  >
  > WordPress官方下载地址: [https://wordpress.org/plugins/wp-code-highlightjs/](https://wordpress.org/plugins/wp-code-highlightjs/)

* 极简单且带扩展语法的ini读取工具: [libiniloader – https://github.com/owt5008137/libiniloader](https://github.com/owt5008137/libiniloader)

* 命令绑定和程序选项解决方案: [CmdOption – https://github.com/owt5008137/CmdOption](https://github.com/owt5008137/CmdOption)

* redis高可用解决方案: hiredis-happ – [https://github.com/owt5008137/hiredis-happ](https://github.com/owt5008137/hiredis-happ)

  > 首先支持redis cluster集群，支持自动重试、断线重连、按需连接

其他的开源仓库没有严格控制代码质量，有些只是自己平常使用，还有些个人的代码记录，所以都不列举了

# 获奖经历

1. 2009年12月 华东理工大学，国家励志奖学金
2. 2009年12月 “中国电机工程学会杯”全国大学生电工数学建模竞赛，三等奖
3. 2010年10月 ACM（Association for Computing Machinery,国际计算机协会） 第35届 ACM-ICPC 亚洲区预选赛-天津赛区，银奖
4. 2012年09月 华东理工大学，校一等奖学金
5. 2014年8月 腾讯科技（上海）有限公司，年中考评：5星（优秀）

# 技术栈/关键字

```
编程语言: bash,cmake,c/c++(11/14/17),lua,php,python,javascript,typescript,c#,html,java,less,php,sql,markdown
库: jemalloc/ptmalloc/tcmalloc,libuv/libevent,boost,bootstrap,jquery,v8,.net,angularjs,vue.js,nodejs,zend framework,websocket,qt
应用和框架: redis,msgpack,protobuf,flatbuffers,ci,jenkins,travis,appveyor,unity,cocos2d-x,cap’n proto,gRPC
主题: 计算机算法,分布式系统,游戏服务器架构设计和开发,linux环境编程,操作系统,编译原理,设计模式,vscode插件开发,wordpress插件及主题开发
工具: svn,git,p4,pandoc,graphviz,valgrind,gdb/lldb,perf,gperf,binutils/readelf/tcpdump等,mingw,msys,wsl,qemu,kvm,docker
```
