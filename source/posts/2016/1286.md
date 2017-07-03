---
title: 对atbus的小数据包的优化
tags:
  - c++11
  - ipc
  - 无锁队列
  - 消息队列
  - 进程间通信
id: 1286
categories:
  - Article
  - Blablabla
  - Work
date: 2016-07-09 14:16:41
---

对atbus的小数据包的优化
======

atbus是我按之前的思路写得服务器消息通信中间件，目标是简化服务器通信的流程，能够自动选择最优路线，自动的断线重连和通信通道维护。能够**跨平台**并且**高效**。

近期优化底层库，完成atapp库的基本功能，顺带优化了一下atbus的一些功能，也是对**高效**的大幅优化。这次的优化起源于某一次的压力测试，先介绍下压力测试的结果吧。

环境
------
+ 环境: CentOS 7.1, GCC 4.8.5
+ CPU: Xeon E3-1230 v2 3.30GHz*8 (sender和receiver都只用一个核心)
+ 内存: 24GB (这是总内存，具体使用数根据配置不同而不同)
+ 网络: 千兆网卡 * 1
+ 编译选项: -O2 -g -DNDEBUG -ggdb -Wall -Werror -Wno-unused-local-typedefs -std=gnu++11 -D_POSIX_MT_
+ 配置选项: 
+ * -DATBUS_MACRO_BUSID_TYPE=uint64_t 
+ * -DATBUS_MACRO_CONNECTION_BACKLOG=128 
+ * -DATBUS_MACRO_CONNECTION_CONFIRM_TIMEOUT=30 
+ * -DATBUS_MACRO_DATA_ALIGN_TYPE=uint64_t 
+ * -DATBUS_MACRO_DATA_NODE_SIZE=128 
+ * -DATBUS_MACRO_DATA_SMALL_SIZE=512 
+ * -DATBUS_MACRO_HUGETLB_SIZE=4194304 
+ * -DATBUS_MACRO_MSG_LIMIT=65536

关于环境方面有一个地方要特别指出的是，由于我的这太测试机还跑了好多其他的服务和两套游戏的服务器环境，所以即便是空闲时候的CPU占用也比较高。不知道对压力测试结果会有多少影响。
空闲的时候的htop大概这个样子。

```
  1  [||||||||||||||||||||                                                           22.1%]   5  [|||||||||||||||                                                                16.6%]
  2  [||||||||||||||||||||                                                           21.6%]   6  [||||||||||||||                                                                 15.4%]
  3  [||||||||||||||||||                                                             20.7%]   7  [|||||||||||||||                                                                16.8%]
  4  [||||||||||||||||||                                                             20.9%]   8  [||||||||||||||                                                                 16.1%]
  Mem[|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||17.0G/23.3G]   Tasks: 178, 215 thr; 3 running
  Swp[                                                                               0K/0K]   Load average: 1.78 1.82 1.79 
                                                                                              Uptime: 142 days(!), 13:03:09
```

优化前的压力测试 - Run On 2016-07-01、
------

测试项                                   |      连接数     |        包长度        |      CPU消耗     |    内存消耗   |    吞吐量     |      QPS
----------------------------------------|----------------|---------------------|-----------------|--------------|--------------|---------------
Linux+本地回环+ipv6+静态缓冲区             |         1      |      8-16384字节     |     93%/100%    |   5.6MB/24MB |    467MB/s   |      80K/s
Linux+本地回环+ipv6+静态缓冲区             |         1      | 8-128字节(模拟ping包) |     97%/100%    |   5.6MB/28MB |    8.67MB/s  |     165K/s
Linux+本地回环+ipv6+动态缓冲区(ptmalloc)   |         1      |      8-16384字节     |     95%/100%    |   5.6MB/28MB |    484MB/s   |    82.6K/s
Linux+本地回环+ipv6+动态缓冲区(ptmalloc)   |         1      | 8-128字节(模拟ping包) |     97%/100%    |   5.6MB/28MB |    8.5MB/s   |     163K/s
Linux+共享内存                           |         1      |      8-16384字节     |      98%/98%    |   74MB/74MB  |    1.56GB/s  |     199K/s
Linux+共享内存                           |         1      | 8-128字节(模拟ping包) |     100%/83%    |   74MB/74MB  |    303MB/s   |    5253K/s

这里面可以看出来，其实使用共享内存通道的时候，性能已经足够不错了，但是对于使用tcp的时候，特别是小数据包其实QPS不是很高。

如果说对比大部分其他开源的类似的库，这个QPS应该还算还可以。虽然现在忘记了那些个框架的名字，我以前接触过的一些用于游戏的通信中间件，QPS在10w-20w/s之间已经算是比较高的了。
而且这个中间件主要是面向游戏服务器的通信，而在一个游戏服务器进程中，一般不会有这么高的请求频次。而且游戏服务器一般是逻辑比较复杂，CPU和内存比较容易成为瓶颈。
所以也是这些原因，要不是看了一下以前跑的腾讯的tbus的压力测试，还真没优化的计划。

tbus的性能 - Run On 2014-01-14
------

+ 环境: tlinux 1.0.7 (based on CentOS 6.2), GCC 4.8.2, gperftools 2.1(启用tcmalloc和cpu profile)
+ CPU: Xeon X3440 2.53GHz*8
+ 内存: 8GB (这是总内存，具体使用数根据配置不同而不同)
+ 网络: 千兆网卡 * 1
+ 编译选项: -O2 -g -DNDEBUG -ggdb -Wall -Werror -Wno-unused-local-typedefs -std=gnu++11 -D_POSIX_MT_
+ 配置选项: 无

测试项                                   |      连接数         |        包长度        |      CPU消耗     |    内存消耗   |    吞吐量     |      QPS
----------------------------------------|--------------------|---------------------|-----------------|--------------|--------------|---------------
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |        16KB         |    13%/100%     |     280MB    |   86.4MB/s   |    5.4K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |         8KB         |    13%/100%     |     280MB    |     96MB/s   |    12K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |         4KB         |    13%/100%     |     280MB    |     92MB/s   |    23K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |         2KB         |    15%/100%     |     280MB    |     88MB/s   |    44K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |         1KB         |    16%/100%     |     280MB    |     82MB/s   |    82K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |        512字节       |    22%/100%     |     280MB    |    79.5MB/s  |    159K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |        256字节       |    33%/100%     |     280MB    |    73.5MB/s  |    294K/s
Linux+跨机器转发+ipv4                     | 2(仅一个连接压力测试) |        128字节       |    50%/100%     |     280MB    |    65.75MB/s |    526K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |         32KB         |    100%/100%    |     280MB    |    3.06GB/s  |    98K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |         16KB         |    61%/71%      |     280MB    |    1.59GB/s  |    102K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |          8KB         |    36%/70%      |     280MB    |    1.27GB/s  |    163K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |          4KB         |    40%/73%      |     280MB    |    1.30MB/s  |    333K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |          2KB         |    43%/93%      |     280MB    |    1.08GB/s  |    556K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |          1KB         |    54%/100%     |     280MB    |    977MB/s   |    1000K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |         512字节       |    44%/100%     |     280MB    |    610MB/s   |    1250K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |         256字节       |    42%/100%     |     280MB    |    305MB/s   |    1250K/s
Linux+共享内存                           | 3(仅一个连接压力测试) |         128字节       |    42%/100%     |     280MB    |    174MB/s   |    1429K/s

由于测试tbus的时候有跨机器的，所以某些进程CPU跑不满也是正常情况。算上CPU的消耗比例，atbus的读性能和tbus对比的话，主要是

+ 使用**共享内存通道**的时候，读性能是差不多的，写性能atbus要高过tbus大约不到一倍。
+ atbus能够**收敛共享内存通道数量**，能大幅减少不必要的内存消耗。这个设计详见：[关于BUS通信系统的一些思考（二）](https://owent.net/gCsOx) 或 https://github.com/atframework/libatbus/tree/master/doc
+ 对于**网络通道的大数据包**，读性能仍然是差不多。但是atbus的写性能大约是tbus的4-5倍，QPS大约是6-7倍。
+ 但是对于**网络通道的小数据包**，读写都落后tbus很多

优化分析
------

然后因为我看不到tbus的源码，就只能是分析tbus的压力测试结果了。可以很明显的看到从大数据包到小数据包，tbus的整个吞吐量变化非常小，所以猜测tbus可能做了小包合并。

而且很明显在atbus里出现小包时，QPS上升的同时对uv_write调用的次数也变多了。我看了下libuv的源码，虽然它内部有做发送队列，但是每次pop front的时候还是会调用**sendmsg**函数或**write**函数，而这两个都是系统调用消耗很高的。

libuv内的代码大致如下:

```c
start:

  assert(uv__stream_fd(stream) >= 0);

  if (QUEUE_EMPTY(&stream->write_queue))
    return;

  // 每次pop front一个发送项目
  q = QUEUE_HEAD(&stream->write_queue);
  req = QUEUE_DATA(q, uv_write_t, queue);
  assert(req->handle == stream);

  // blablabla 好多代码 ...

    /* silence aliasing warning */
    {
      void* pv = CMSG_DATA(cmsg);
      int* pi = pv;
      *pi = fd_to_send;
    }

    do {
      n = sendmsg(uv__stream_fd(stream), &msg, 0);
    }
#if defined(__APPLE__)
    /*
     * Due to a possible kernel bug at least in OS X 10.10 "Yosemite",
     * EPROTOTYPE can be returned while trying to write to a socket that is
     * shutting down. If we retry the write, we should get the expected EPIPE
     * instead.
     */
    while (n == -1 && (errno == EINTR || errno == EPROTOTYPE));
#else
    while (n == -1 && errno == EINTR);
#endif
  } else {
    do {
      if (iovcnt == 1) {
        n = write(uv__stream_fd(stream), iov[0].iov_base, iov[0].iov_len);
      } else {
        n = writev(uv__stream_fd(stream), iov, iovcnt);
      }
    }
#if defined(__APPLE__)
    /*
     * Due to a possible kernel bug at least in OS X 10.10 "Yosemite",
     * EPROTOTYPE can be returned while trying to write to a socket that is
     * shutting down. If we retry the write, we should get the expected EPIPE
     * instead.
     */
    while (n == -1 && (errno == EINTR || errno == EPROTOTYPE));
#else
    while (n == -1 && errno == EINTR);
#endif
  }

  // blablabla 好多代码 ...
  // 如果还有带发送数据并且fd处于writable状态，goto start
```
那么优化方向就很明了了。合并小数据包呗。

优化实现
------
合包的话最简单的就是在**io_stream_send**里坐点手脚。原先这个函数每调用一次都会调用**uv_write**。现在如果某个连接有数据正在发送，则需要先把要发送的数据保存下来，直接返回成功，然后发送完毕后对保存的数据做合包，然后再一起发送。
然后如果发送时发现不能发送了，或者write失败，都要走以前的契约，那就是调用发送失败的回调。

起先我给atbus里的buffer_manager模块加了个merge_front和merge_back功能。实现非常复杂，但是写完之后转念一想，如果每次调用都使用merge的话，那岂不是如果要merge N个包，第一个包要copy N次？因为每次都要扩充缓冲区。
我觉得这个消耗也是没有必要的，所以最终没用这个merge功能，而是采用了一个更简单的方法，定一个**合包缓冲区**。

那么这个**合包缓冲区**该是多大呢？也很简单，因为现在的每个connection的write队列里的数据块结构是write_req_t+4字节hash+动态长度int+数据包长度。
那么缓冲区太大也没意义，我就设成了: 包大小限制(默认64K)-sizeof(write_req_t)-一个对齐大小（以防数据写乱，目前64位系统是8字节）。

缓冲区也没必要每个connection一个，可以每个线程一个。这个可以用TLS机制实现，方法上一篇文章（Android和IOS的TLS问题）里提到过了，这里不再复述。

然后每次写出时给connection加***WRITING***标记，写完的回调之后移除，如果调用**io_stream_send**的时候有***WRITING***标记，则往write队列里加，但不执行实际写操作，如果没有就执行实际写操作。
执行实际写操作的时候先合包，再写。这样就能保证正在写出的永远是write队列里的第一个数据块。

**write队列怎么合包呢？**
对于每个数据块而言，因为都包含了write_req_t，而且这个就是拿来放临时放数据的，并不会通过网络发送，所以可以移除被合包的数据块的这一部分，然后剩下的copy到一起即可。
由于write队列的缓冲区有静态和动态两种模式，对于动态模式很容易处理，把可以合包的数据全部pop front，copy到**合包缓冲区**，然后合并后的数据push front即可。如果push失败，那必然是内存不足了，这时候肯定就跪了，没啥好说的。整个逻辑都会出问题，不差这一块。
而对于静态缓冲区而言就多一步操作，因为静态缓冲区是环形队列，那么头部和尾部的数据是不能合并的，否则可能缓冲区剩余空间不足。而因为先前pop front的总长度必然大于最后push front的合包后的数据长度，所以这个push一定成功。

再就是接收端，原先设置了512字节的接收缓冲区，也就是TCP发过来后会随机拆包黏包，所以接收队列空时，第一次一次性最多接收512字节。
目前一个connection消耗大约480字节，再加上接收合包缓冲区。额外还会消耗一个智能指针的header block和一些额外的开销，原先大约每个connection占用1K多一点。
我希望能多一些这个第一个包接收的量，因为在游戏服务器中，虽然大多数情况是小数据包，但是超过512字节还是比较容易的。我想总消耗控制在4K，这样的话这个接收缓冲区就设在了3K，当然这个是可以随时辩护调整的。
每个连接4K意味着如果有2M的连接，会消耗8GB在这上面。当然如果真要搞到2M的连接数，连内核底层的tcp窗口的缓冲区也得改。这个缓冲区默认情况都远大于4K。

最后加的一个东西就是：**write队列什么时候合包？**

目前策略是当第一个包小于接收端的缓冲区的时候（也就是3KB）尝试合包，一方面考虑是再大合包的效果也不明显（我们前面大数据包的性能本身不差，瓶颈不是在系统调用上）。另一方面3KB也覆盖大多数数据包大小了。
如果说这个参数不够好或者在一些特别的机器上需要大量连接且内存吃紧，也可以缩减这个值。


优化的成果 - Run On 2016-07-07
------

配置选项有所变更:（变更项已经标出） 

+ -DATBUS_MACRO_BUSID_TYPE=uint64_t 
+ -DATBUS_MACRO_CONNECTION_BACKLOG=128 
+ -DATBUS_MACRO_CONNECTION_CONFIRM_TIMEOUT=30 
+ -DATBUS_MACRO_DATA_ALIGN_TYPE=uint64_t 
+ -DATBUS_MACRO_DATA_NODE_SIZE=128 
+ **-DATBUS_MACRO_DATA_SMALL_SIZE=3072** 
+ -DATBUS_MACRO_HUGETLB_SIZE=4194304 
+ -DATBUS_MACRO_MSG_LIMIT=65536


测试项                                   |      连接数     |        包长度        |      CPU消耗     |    内存消耗   |    吞吐量     |      QPS
----------------------------------------|----------------|---------------------|-----------------|--------------|--------------|---------------
Linux+本地回环+ipv6+静态缓冲区             |         1      |      8-16384字节     |     90%/100%    |   5.8MB/24MB |    601MB/s   |      95K/s
Linux+本地回环+ipv6+静态缓冲区             |         1      | 8-128字节(模拟ping包) |     48%/100%    |   5.8MB/27MB |    163MB/s   |    2822K/s
Linux+本地回环+ipv6+动态缓冲区(ptmalloc)   |         1      |      8-16384字节     |     90%/100%    |   5.8MB/24MB |    607MB/s   |      96K/s
Linux+本地回环+ipv6+动态缓冲区(ptmalloc)   |         1      | 8-128字节(模拟ping包) |     48%/100%    |   5.8MB/27MB |    165MB/s   |    2857K/s
Linux+共享内存                           |         1      |      8-16384字节     |      98%/98%    |   74MB/74MB  |    1.56GB/s  |     199K/s
Linux+共享内存                           |         1      | 8-128字节(模拟ping包) |     100%/83%    |   74MB/74MB  |    303MB/s   |    5253K/s

由于没改动共享内存通道的任何代码，所以共享内存的后两项性能测试没有重新跑。
这个结果可以看到，成果也相当明显，现在对小数据包也能有相当不错的QPS（282w/s）。接收性能和tbus类似，发送性能已经各方面远超tbus了。

这次的优化也就到此结束。最终的Benchmark见： https://github.com/atframework/libatbus/blob/master/doc/Benchmark.md

另一个小优化
------
其实这次单元测试之前有几次测试，但是感觉性能很有问题。即便共享内存的吞吐量也只有300MB/s。这显然很不正常，后来用valgrind做了下cpu profile，发现90%的CPU耗费在计算数据块的hash值上。
因为atbus里所有类型的通道都会有催数据做hash而后校验。而这个hash最早是我自己乱搞的一个很简单的算法，很容易碰撞，后来为了严谨一些则换成了CRC32和CRC64。而替换之前是没有这个问题的。
问题就在于这里，使用map方式实现的**CRC32和CRC64性能太差了**。我还不清楚具体的原因，不过猜测可能和CPU命中率有关。

后来看了下[jemalloc][1]的源码，里面用了[MurmurHash][2] V3算法。所以我也去这里copy了这个算法过来。性能瞬间的提上来了。这个改动很小就不详细说明了，具体可以看这个: https://github.com/atframework/atframe_utils/blob/master/src/algorithm/murmur_hash.cpp



[1]: http://www.canonware.com/jemalloc/
[2]: https://github.com/aappleby/smhasher