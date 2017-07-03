---
title: 理解Raft算法
tags:
  - paxos
  - raft
  - 分布式
  - 去中心化
id: 1226
categories:
  - Article
  - Blablabla
  - Work
date: 2016-03-17 21:29:24
---

# 理解Raft算法

## 前言

最近在分布式系统一致性方面，[Raft](https://raft.github.io/)算法比较火啊。所以就抽时间看了下这个算法。

之前已经有[Paxos算法](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)，用于解决分布式系统最终一致性问题，而且已经有了[zookeeper](http://http://zookeeper.apache.org/)这个成熟的开源实现。那么这个[Raft](https://raft.github.io/)算法有啥用呢？按照[Raft](https://raft.github.io/)官网的说法，这个算法的错误容忍和性能和[Paxos算法](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)类似，但是拥有更加简单易懂的设计。

看过[Paxos算法](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)的童鞋们都知道，这货复杂地和屎一样，为了实现去中心化而考虑了各种复杂的边界条件和时序下的可靠性。而[Raft](https://raft.github.io/)算法则根据实际应用中的需要，简化了设计模型，不采用去中心化设计，而是自动选举中心节点，并且在各种情况和时序下可以保证能够正确的选举出中心节点并保证数据的一致性。而且也正是由于能够选举出唯一的主节点（Leader）使得整个通信流程非常地简单，并且易于理解和维护。

那么它是如何做到这些的呢？

## 基本算法设计

[Raft](https://raft.github.io/)的基本设计可以参照官网介绍 https://raft.github.io/

官方网站上的图例可以点击节点，然后**模拟**节点crash或者超时或者收到请求时的通信流程。其实也是一个javascript的简单实现，有利于我们理解[Raft](https://raft.github.io/)算法的流程。

另外还有一个基本要点的流程有点像PPT的东东也能帮助我们理解 http://thesecretlivesofdata.com/raft/

当然最完整的就是这篇Paper了，[《In Search of an Understandable Consensus Algorithm (Extended Version)》](http://ramcloud.stanford.edu/raft.pdf)。大体翻译提取下这篇论文里的核心内容吧。

基本思路是每个节点分为Leader、Follower、Candidate三个状态。

+ <a href="#leader" name="leader">**Leader**</a>: 主节点
+ <a href="#follower" name="follower">**Follower**</a>: 从节点
+ <a href="#candidate" name="candidate">**Candidate**</a>: 正在竞选主节点（参选节点）

消息状态分为:

1. **Uncommit**: 未提交转态（Client发到主节点，主节点还没有得到大多数从节点的提交回执）
2. **Commited**: 已提交转态（从节点收到主节点的消息提交，还未收到确认报文）
3. **Applied**: 已确认转态（从节点收到主节点的确认报文，或主节点已收到大多数从节点的提交回执）

所有的节点中都要记录以下信息

+ <a href="#term" name="term">**CurrentTerm**</a>: 节点的当前选举版本号（发起竞选主节点时要更新这个值），后面的**Term**指代消息中的选举版本号或者生产[消息](#log)时的选举版本号
+ <a href="#voted_for" name="voted_for">**Voted For**</a>: 主节点投票给谁
+ <a href="#log" name="log">**Log**</a>: log是论文里的描述，其实也就是消息的内容，后面用***消息***指代这里提到的Log
+ <a href="#commit_index" name="commit_index">**Commit Index**</a>: 提交序号（每次收到客户端消息时要更新这个值）
+ <a href="#last_applied" name="last_applied">**LastApplied**</a>: 最后确认的消息序号
+  ***下面是仅主节点需要记录的数据***
+  <a href="#next_index" name="next_index">**NextIndex[]**</a>: 预估的每个从节点下一个的Log的序号（初始化为最后的log索引+1）
+  <a href="#match_index" name="match_index">**MatchIndex[]**</a>: 已经确认的每个从节点的下一个Log的序号（初始化为0）

RPC消息有两种：

### AppendEntries RPC（心跳、消息同步RPC）

#### RPC请求:

参数                             | 描述
--------------------------------|----
Term                            | 主节点的[CurrentTerm](#term)
LeaderId                        | 主节点ID（更新到[Voted For](#voted_for)，用于通知客户端主节点是谁）
PrevLogIndex                    | 先前一次RPC请求的[CommitIndex](#commit_index)
PrevLogTerm                     | 先前一次RPC请求的[Term](#term)
Entries                         | [消息](#log)内容
LeaderCommit                    | 主节点的[CommitIndex](#commit_index)

#### RPC回复:

参数                             | 描述
--------------------------------|----
Term                            | 从节点的**CurrentTerm**
Success(我认为这里用返回码更好)     | 如果从节点的内容匹配**PrevLogIndex**和**PrevLogTerm**则返回成功

#### 接收方判定条件
1. 如果请求包内Term < [CurrentTerm](#term)，回复失败
2. 如果节点内不包含Term等于***PrevLogTerm***但[CommitIndex](#commit_index)不等于***PrevLogIndex***的[消息](#log)，则回复失败
3. 如果存在[消息](#log)和拿到的请求包里的冲突（[CommitIndex](#commit_index)相同但Term不同），则移除所有冲突之后的[消息](#log)，并用新的[消息](#log)覆盖
4. 如果[消息](#log)不在已有[消息](#log)集合中，追加数据
5. 如果***LeaderCommit***大于本地的[CommitIndex](#commit_index)，[CommitIndex](#commit_index)要设置成***LeaderCommit***和最后一条消息（***Entries***）的[CommitIndex](#commit_index)里的最小值

### RequestVote RPC（竞选主节点RPC）

#### RPC请求:

参数                             | 描述
--------------------------------|----
Term                            | 竞选节点的[CurrentTerm](#term)
CandidateId                     | 竞选节点ID（对应从节点[Voted For](#voted_for)）
LastLogIndex                    | 竞选的最后一条[消息](#log)[CommitIndex](#commit_index)
LastLogTerm                     | 竞选的最后一条[消息](#log)[Term](#term)

#### RPC回复:

参数                                 | 描述
------------------------------------|----
Term                                | 从节点的**CurrentTerm**
VoteGranted (同样我认为这里用返回码更好) | 如果收到同意票，返回成功

#### 接收方判定条件
1. 如果请求包内***LastLogTerm*** <= [CurrentTerm](#term)，投否决票
> 论文里写得是*小于*，实际应该是*小于等于*，实际测试也是小于等于。因为等于的情况包含，[从节点](#follower)已经投了一个同期的[参选节点](#candidate)，或者自己是[参选节点](#candidate)，收到一个同期的竞选消息。

2. 如果[Voted For](#voted_for)是空的或者和***CandidateId***相等，则仅[参选节点](#candidate)的**消息最新(up-to-date)**才投同意票
> **消息最新(up-to-date)**的判定方式是: 如果[参选节点](#candidate)的最后的[消息](#log)的[Term](#term)比投票者更大或者[Term](#term)相等且[CommitIndex](#commit_index)大于等于投票节点的最后一个[消息](#log)。那么[参选节点](#candidate)的消息会被投票者认为是最新（只是相对于投票者更新）
>
> *PS: 这里我一开始认为是节点的[Term](#term)和[CommitIndex](#commit_index)，导致后面的协商流程一直理解不了。但是这是实际上应该是最后一条[消息](#log)的[Term](#term)和[CommitIndex](#commit_index)。*

### 服务器逻辑规则

#### 所有服务器
+ 如果[CommitIndex](#commit_index) > [LastApplied](#last_applied)，把所有大于[LastApplied](#last_applied)且未确认的消息转为确认状态，并且更新[LastApplied](#last_applied)到[CommitIndex](#commit_index)
+ 如果RPC的传入的Term大于[CurrentTerm](#term)，更新[CurrentTerm](#term)到传入的Term值，并**强制转为[从节点](#follower)**

####[从节点](#follower)

+ 回应所有来自[主节点](#leader)和[参选节点](#candidate)的RPC消息
+ 如果**竞选超时**时间内没有收到**AppendEntries RPC**或者没有成功的投票（可以是收到**RequestVote RPC**但投反对票），则发起竞选请求（**RequestVote RPC**）

####[参选节点](#candidate)

+ 转变为[参选节点](#candidate)时，开始选举过程
	1. [CurrentTerm](#term) = [CurrentTerm](#term) + 1
	2. 投票给自己
	3. 重设（随机）**竞选超时**定时器
	4. 向所有节点发送竞选请求（**RequestVote RPC**）
+ 如果收到大多数的统一票，转变为[主节点](#leader)
+ 如果收到来自新[主节点](#leader)的**AppendEntries RPC**，转变为[从节点](#follower)
+ 如果再一次**竞选超时**，重新启动一轮选举，发起竞选请求（**RequestVote RPC**）

####[主节点](#leader)

+ 竞选成功时立刻发送空的心跳包给所有其他节点。并且设置心跳定时器（时间间隔较短），重复这个过程
+ 收到来自客户端的消息以后，添加到本地[消息列表](#log)
+ 如果最后一次[消息](#log)的[CommitIndex](#commit_index)大于等于某个[从节点](#follower)的[NextIndex](#next_index)，发送**AppendEntries RPC**，并附带从[从节点](#follower)的[NextIndex](#next_index)开始的所有消息
	+ 如果成功则更新相应[从节点](#follower)的[NextIndex](#next_index)和[MatchIndex](#match_index)
	+ 如果失败则是发生数据不一致，[NextIndex](#next_index) = [NextIndex](#next_index) - 1然后重试
+ 如果存在N，满足N>[CommitIndex](#commit_index)，并且大多数的[MatchIndex[i]](#match_index) >= N，并且Log[N].term == [CurrentTerm](#term)，设置[CurrentTerm](#term)=N

## 未提及的细节和一些思考

前文提到的各种情况和边界都可以使用[Raft](https://raft.github.io/)主页上的工具模拟出来，流程前面已经写得比较清楚了我就不复述了，只提出我认为比较重要的几个地方和论文里没详细说明的一些细节。

1. 最重要的核心是用定时器和心跳包来同步数据和更新状态
2. 主节点只追加数据，不改写
3. 初始所有节点都是[从节点](#follower)，**随机**取一个选举超时时间
> 这样初始状态下很快就会进入竞选节点状态

4. **竞选超时**时间只在初始化和每次发起竞选的时候随机，其他情况都是复用之前的超时时间。
> 这样保证了发生冲突的时候，最终会有一个节点的**竞选超时**比较短，而其他的随机后**竞选超时**较长的节点在触发超时时间之前会收到RequestVote RPC（竞选主节点RPC），从而变为[从节点](#follower)
>
> 但是在节点数量特别多的时候我觉得也会出现一直没办法选举出主节点的情况，我的想法是再区分**竞选超时**的定时器为两种，[从节点](#follower)的**竞选超时**取值区间在一个比较大的值范围，而[参选节点](#candidate)的**竞选超时**取值区间在一个比较小的值范围。这样能保证[参选节点](#candidate)的数量能够收敛，即[参选节点](#candidate)变为[从节点](#follower)后几乎不可能变回[参选节点](#candidate)

5. 不同[从节点](#follower)的心跳定时器是分开计的，但是间隔是一样的（这是为了减少[从节点](#follower)转变为竞选状态的可能性）
6.  [NextIndex](#next_index)和[MatchIndex](#match_index)的区别
	+ [NextIndex](#next_index)记录可能的下一个Log序号，意味着可能不正确，比如新的[主节点](#leader)被选出来以后，会假设所有的[从节点](#follower)的数据最新，然后如果发RPC或者失败回复，才会确认该节点有部分数据未同步
	+ [MatchIndex](#match_index)记录的是已经确认过该[从节点](#follower)已经获得的数据
7. 注意节点数据里的[CommitIndex](#commit_index)指的是主节点已经被大多数从节点确认的消息序号。也就意味着[消息列表](#log)里的提交索引可能高于这个值。（所以[LastApplied](#last_applied)并没什么卵用，完全可以优化掉，你看那个页面上的例子里就没有这个东西）
8. 这里的数据提交有一些比较有意思的细节
	1. 通知[从节点](#follower)确认消息并不需要立刻通知，下一次心跳带回去即可

9. 一个小优化，心跳包失败的时候，可以通过[从节点](#follower)的回包里附带当前的[CommitIndex](#commit_index)，从而减少[主节点](#leader)上[NextIndex](#next_index) - 1的操作，直接设为[从节点](#follower)的[CommitIndex](#commit_index)然后同步所有差异[消息](#log)
> 论文里也有提到这个小优化，但是作者认为很少会出现消息丢失和消息不一致的情况，所以可能这个优化的意义不大。

10. <a href="#my_thk10" name="my_thk10">新的[主节点](#leader)绝不能确认之前未处理完的*已提交转态*但未确认的消息（后面会再说明）</a>
> 即便确保了大部分[从节点](#follower)已经获取到了这些[消息](#log)也不能立即执行确认。必须使用另一种方式确认这些消息。

11. 用快照来减少持续增长的日志数据（Chubby和Zookeeper也是用得快照）
> 实际上我们能按照实际使用场景，使用类似[Redis的AOF](#http://redis.io/topics/persistence)方式做更好的优化

### 主节点切换期间的消息（Log）处理
前面提到[**新的主节点绝不能确认之前未处理完的*已提交转态*但未确认的消息**](#my_thk10)。这些消息主要指没有收到原先的[主节点](#leader)的[CommitIndex](#commit_index)的通知，然后自己成为了新[主节点](#leader)而导致之前的部分[消息](#log)没有被确认的情况。这时候可以确保的就是新选成功[主节点](#leader)之后，当前的[Term](#term)一定大于这些未确认的消息的[Term](#term)。

论文*5.4.2节+图8*有讨论了一种比较恶心的多个主节点的情况（论文*图8-d和图8-e*是两种互斥的情况）。

在这种情况下，*图8-c*中新的[主节点](#leader)即便能够确保大多数[从节点](#follower)都收到了，但是如果自己挂了，仍然可能被其他新的[主节点](#leader)覆盖数据的情况（*图8-d*）。

但是这些**未被确认的[消息](#log)**最终总要被确认掉，所以可以利用上面提到的新选成功[主节点](#leader)之后，当前的[Term](#term)一定大于这些未确认的消息的[Term](#term)这个前提。如果有新的[消息](#log)被大部分[从节点](#follower)收到，并且这条消息的[Term](#term)和当前节点的[CurrentTerm](#term)一致的话，那么确认这条[消息](#log)的同时也确认之前的**未被确认的[消息](#log)**（即[Term](#term)和当前节点的[CurrentTerm](#term)不同的[消息](#log)）。这就是*图8-e*的情况。这种情况下，不会再发生*图8-d*中的消息覆盖，因为那个节点的竞选请求不会被大多数节点投同意票的。

另外，可以在新[主节点](#leader)被选举出来时立刻提交一个空[消息](#log)。用来加快未提交的消息被确认的过程。

## 补充内容

以下内容是补充这个算法的部分，不是最核心的内容。

### 定时器
定时器随机的时间应该远大于估计的通信延迟（避免频繁冲突）。Broadcast Time（RPC交互时间） ≪ Election Timeout（**竞选超时**，同样上面的总结，区分两种**竞选超时**时间比较好）≪ MTBF（平均故障时间）

+ Broadcast Time(广播[心跳]时间): 0.5-20ms
+ Idle Periods(心跳间隔): 并没有给出一个推荐的时间，但是为了防止频繁选举，建议要是**竞选超时**时间的1/N， N>=3 比较好
+ Election Timeout(**竞选超时**): 10-500ms(论文中建议150-300ms，但是我觉得这个心跳有点过于频繁了)
+ MTBF（平均故障时间）: 几个月或更长

上面的时间都可以根据实际项目需要来调整，另外很多冲突通过定时器随机时间不同来解决，让我想起了[跳表](https://zh.wikipedia.org/wiki/%E8%B7%B3%E8%B7%83%E5%88%97%E8%A1%A8)也是利用了随机的特性来实现的低平均时间复杂度。没有一个严格保证，只是利用了随机数的特点做到平均复杂度。

### 扩容、缩容和故障转移
这点[Raft](https://raft.github.io/)并没有做严格限制，不过提供了一个标准的方法。即走两阶段提交。

下面定义**新集群**为扩容、缩容或故障转移后新配置的节点集合，**老集群**为扩容、缩容或故障转移前配置的节点集合。**新老集群**为**新集群**和**老集群**的并集。

#### 两阶段提交

1. 第一阶段，**新老集群**共存
	+ 生成并提交一个同时包含**新老集群**配置的[消息](#log)，并同步到**新老集群**的所有节点
	+ 所有确认了这个配置的节点是立刻使用新的配置（即如果发生新的RPC，要从**新老集群**所有节点里找到大多数同意的回包）

2. 第二阶段，切换到新集群
	+ 生成并提交只包含**新集群**的配置[消息](#log)并同步到**新老集群**的所有节点。
	+ 大部分**新集群**节点确认了新配置后使用**新集群**配置
	+ [主节点](#leader)不在**新集群**中则主节点下线

#### 迁移过程中的几个要点
+ 可以特殊处理加快集群配置的[消息](#log)的传输速度，如果是集群配置变更，立刻发心跳包
+ 新上线的节点数据大幅落后，可以等新上线节点数据第一次同步完成后再计入**新老集群**的大多数节点同意或确认的计数（防止新节点数量过多，copy数据期间集群可能会不可用的问题）
+ 第二阶段结束时，可能原先的主节点不在**新集群**配置内，那么要等**新集群**配置被**新集群**的大部分节点接收后才能下线
+ 即将下线的老节点不会再收到**新集群**的心跳包，所以可能会触发*选举超时*然后向**新集群**发起选举请求，然后导致**新集群**[主节点](#leader)被转变为[从节点](#follower)。并且这是循环一直存在的。论文里说可以通过让节点忽略最小选举超时时间内的选举请求，因为**新集群**的[主节点](#leader)会下发心跳包，而正常的节点触发选举一定大于*选举超时*时间的最小值（随机的下限）。
> 但是我觉得有个更简单且行之有效的方法：因为大部分节点（这里面包括**新集群**的主节点）都会收到集群配置，那么直接忽略新配置里没有的节点的RPC消息就好了；另外如果即将下线的老节点也拿到了这个配置，直接停止定时器，别发起选举就行了。

### 客户端接入
考虑到上面的一些容灾的设计，对客户端的接入其实是有一定要求的。论文里没有太多提及接入的细节，但是也有一些基本的准则。

#### 容错和重发

首先，需要客户端拥有超时机制，并在超时以后能够进行重发操作。因为如果集群节点崩溃，可能会不能正确处理客户端传入的[消息](#log)。

然而，一条[消息](#log)存在着可能被服务器成功保存了，但是给客户端的回执丢失的情况。这就需要客户端给**每个命令生成一个唯一的票据(unique serial numbers)**。无论重发多少次，票据是一样的，并且服务器如果检测到某个客户端的某个票据已经执行过，就不需要再执行一次了。

那么服务器怎么记录票据呢？ 论文里的提供方法是集群要记录每个client的最后处理的消息的序号。如果某个序号的消息被处理过了，那么就不用再处理一遍。但是还是有一些没有提。首先是怎么区分各个client？因为client会尝试连接不同的节点，连接的断开再连接需要区分新的client是不是先前那一个，难道每个client分配一个ID？如果是这样，那么client下线以后这个client的最后处理的消息的序号要保留多久？肯定不可能无限长。

我的想法是，避免掉记录每个客户端信息的复杂因素

+ 首先给客户端分配ID不可避免，然而其实也可以根据需要指定一个不会冲突的ID生成规则。
+ 然后设计一个算法能够给每个命令生成唯一票据，并且由客户端ID保证票据也唯一。
+ 再次，[消息](#log)数据里要附带客户端的ID，所有节点都要索引客户端最后执行序号。
+ 最后服务器和客户端协商一个心跳时间和超时时间。如果网络出现故障，或者服务器挂掉，超出超时时间的客户端执行序列索引就可以清理掉了。


#### 只读订阅
为了降低对[主节点](#log)的负载，只读订阅可以从[从节点](#follower)拿到数据。但是前面提到过，如果发生故障，切换主节点的时候，会导致部分[消息](#log)要等到有新的[主节点](#leader)确认了新[消息](#log)之后才能被确认。

这时候就会存在一定的时间内，某些[消息](#log)已经生效了但得不到确认通知。

那如何尽快确认这些消息呢？方法也很简单，前面也提过[主节点](#leader)被成功选举后，立即发一个空[消息](#log)。这样前面不确定是否会被覆盖的消息就会很快被确认下来了。同时这些[消息](#log)的确认通知也会广播道所有[从节点](#follower)，最终传达到所有的只读订阅的client中。

#### 负载均衡和容灾通知(主节点变更)
通知Client主节点变更可以和[Redis Cluster](http://redis.io/topics/cluster-spec)一样，论文里给出的方法就是和[Redis Cluster](http://redis.io/topics/cluster-spec)的一样。这要求Client需要能处理超时、重发和主节点变更的情况。

具体对接的代码可以参考我之前对[Redis Cluster](http://redis.io/topics/cluster-spec)的接入代码库[hiredis-happ](https://github.com/owt5008137/hiredis-happ)或者Redis作者提供的阻塞的Ruby版本[redis-rb-cluster](https://github.com/antirez/redis-rb-cluster) （不过目前为止这个Redis作者接入的Client还没我这个完整，可能是他并没有话太多精力在Client上吧。另外他只接入了同步API，我只接入了异步API）。

不过我认为可以按我们目前写得聊天服务器的做法：如果客户端发送的目标不是主节点，集群内部做消息转发，然后回带给客户端主节点的地址。下一次客户端直接发给新的主节点。

不过无论用哪种方法，客户端都要处理发送超时和网络失败，然后随机找一个有效的新目标进行发送。

[主节点](#leader)丢失期间，客户端commit的消息会得不到回复。最终会触发前面的超时。

### 压缩数据
前面说到，所有的消息交给[主节点](#leader)必须只能执行追加操作。那么长时间运行以后，数据量必然越来越大。这时候如果发生扩容或者改变节点，那么复制的量将是不可计量的。这时候就需要对集群中的数据进行适当的处理，减少不必要的[Log](#log)。

比如说，先执行了 set a=1,再执行 set a=2。那么其实前一条也就不需要一直保存在集群中了。

## 与[Paxos](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)的差异

[《In Search of an Understandable Consensus Algorithm (Extended Version)》](http://ramcloud.stanford.edu/raft.pdf)里面有很详细的[Raft](https://raft.github.io/)和[Paxos](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)性能比较的实测结果，我就不再参合再测一遍了。但是根据自己对这两算法的差异的理解，我自己也能有一些总结，可能不完全正确。

[Paxos](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)可以同时提交和处理多个提案，但是发生冲突时，理论上会有更高的延时（协商时间），而[Raft](https://raft.github.io/)算法会天生地把消息确定一个先后顺序。大幅减少了冲突的可能性。

但是一般情况下，这种最终一致和带协商的算法都只用作一个用途，而且基本就是用于协商服务器分布（因为它的节点数越多，可靠性越好的同时，延时也比较高，不适合做密集运算）。所以[Paxos](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)的多个不冲突提案可以并行分布到多个节点的特性在实际应用用并不是特别有用。而且看到[etcd](https://github.com/coreos/etcd)已经可以做到每秒数千的请求量已经很够用了。

性能方面，其实无论[Raft](https://raft.github.io/)还是[Paxos](https://zh.wikipedia.org/zh-cn/Paxos%E7%AE%97%E6%B3%95)，每个消息都需要经过大部分节点的投票同意，并且都是每个节点最终会得到最终一致的结果，所以正常情况下，他们的性能一样也比较理解。不同的就是[Raft](https://raft.github.io/)的心跳包比较频繁，所以空跑时负载应该会更高一些。

## 应用层面的思考

[Raft](https://raft.github.io/) 可以用在哪些地方呢？首先想到和我们的项目相关的一些东西。

第一个是**Redis Cluster**自动负载均衡。因为Redis的Cluster的slot和对应主从节点的关系是必须手动配置的。必定要人工感知和手动配置还是比较麻烦，所以如果可以有服务来管理slot的分配和负载均衡就再好不过了。

再或者我们目前的**聊天服务器**。目前的架构是类似**Redis Cluster**的按slot分配订阅通道的，区别就是如果发生故障会自动转移slot到其他可用的节点。然而由于要保证slot分配的最终结果一致，是需要配置一个静态的**控制节点**，并且只能由控制节点来进行slot的故障转移和负载均衡操作，然而控制节点是单点，如果控制节点崩溃，可能聊天的部分功能短时间（控制节点重启前）不可用，并且故障转移和负载均衡也不可用，并且控制节点重启后会强制执行一次负载均衡（保证以控制节点为准）。如果使用[Raft](https://raft.github.io/) 算法，则可以由它来决断出控制节点或者slot分配记录。由于最终结果必定是一致的，可以达到去中心化的效果。

上面提到的两个应用其实都是用于决断服务器集群的分配和配置，这也是我觉得最有意义的地方。而由于[Raft](https://raft.github.io/) 的响应请求的能力并不是非常强，并且节点越多，性能越差。所以最重要的其实是它能够提供一个**强一致性**并且**高可用**的解决方案。而如果一个服务需要很高的性能或能够通过平行扩容来提升承载能力，则需要另外提供*分库分表*或者*hash*或者类似**Redis Cluster**的*槽分配*的方案。这时候[Raft](https://raft.github.io/)就可以用于维护这些*分库分表*或者*hash*或者类似**Redis Cluster**的*槽分配*的配置，并达到最终一个去中兴化的服务集群。

另外，结合上面的应用场景，会需要一个类似时间锁服务的东东。比如，如果redis节点发生故障，可能短时间内有多个监控设施检测到并发起slot转移通知。但是这时候不需要执行很多次，使用任意一次的结果即可。比如：

1. slot[1-128) -> svr1 崩溃
2. 检测服务器A检测到故障，通知slot[1-128) 转移到 svr2 => Raft消息1
3. 检测服务器B检测到故障，通知slot[1-128) 转移到 svr3 => Raft消息2
4. 检测服务器C检测到故障，通知slot[1-128) 转移到 svr2 => Raft消息3
5. 检测服务器D检测到故障，通知slot[1-128) 转移到 svr4 => Raft消息4
6. ...
7. [Raft](https://raft.github.io/)服务器消息1成功Commited
8. [Raft](https://raft.github.io/)服务器消息2成功Commited
9. ...

很显然*Raft消息1-Raft消息N*中任何一个都可以完成估值转移，如果这时候能够带一个时间锁，那么短时间的负载均衡或者故障转移通知只会成功一个，就可以避免频繁转移的问题。


## [Raft](https://raft.github.io/)的实现

[Raft](https://raft.github.io/) 上面列了很多协议的实现的库或者组件，我主要看了下[etcd](https://github.com/coreos/etcd)和[RethinkDB](#https://github.com/rethinkdb/rethinkdb)。

我不喜欢[etcd](https://github.com/coreos/etcd)的http协议的使用方式，不过[RethinkDB](#https://github.com/rethinkdb/rethinkdb)有点太过于庞大了，而且我不喜欢GPL协议。

以后还是有空根据需要自己写[Raft](https://raft.github.io/)的核心部分吧，反正也不难。而且我的需求并不要把它做成完整的数据库，而是做成一个选举主节点的中间层（用主节点来做一些负载均衡方面的决策）。所以一方面可以做成容易嵌入各种实际应用的方式，并且大多数情况下可以忽略Client这一层；另一方面也可以省去很多不必要的协议定制和功能定制。
