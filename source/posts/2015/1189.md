---
title: 小记最近踩得两个C++坑
tags:
  - c
  - c++0x/11
  - c++11
  - cpp
  - g++
  - gcc
  - linux
  - STL
  - 内存实现
id: 1189
categories:
  - Article
  - Blablabla
  - Work
date: 2015-07-25 14:53:44
---

小记最近踩得两个C++坑
======

<!-- toc -->

记一下最近踩得两个C++独有的暗坑，其中一个和ABI相关。第二个坑其实之前研究过，但是没有实例，这次算是碰到了个典型的实例。

坑一：常量引用失效
------

在项目中碰到的实例的大致流程是:

1. 获取某个容易的迭代器，迭代器内包含智能指针（std::shared_ptr）
2. 把智能指针通过常量引用方式传入函数
3. 执行过程中智能指针被释放
4. 于是这时候，我们有了一个空悬的智能指针引用了

用代码表示的话，流程如下:
```cpp
std::map<int, std::shared_ptr<T> > outter_map;

void func1(int a) {
    std::map<int, std::shared_ptr<T> >::const_iterator iter = outter_map.find(a);
    if (iter != outter_map.end()) {
        func2(iter->second);
    }
}

void func2(const std::shared_ptr<T>& obj_ptr) {
    if (!obj_ptr) {
        return;
    }
    // 从逻辑隔离的角度，按照正常的语义，这里之后obj_ptr应该一直有效了吧 
    // ... ,执行了茫茫多操作以后,间接调用了outter_map.erase([上一层函数用到的a])
    
    obj_ptr->xxx; // 这里崩溃了，因为智能指针常量不再有效
}
```

如果这两个函数分散在两个模块里，并且是不同人写得话，很难发现这个问题。因为对双方各自的使用来说，似乎都没什么问题（上层不关心下层的内部实现，下层不应该认为常量是不会变化的）。但是放一起的话问题就来了。所以算是C++ 使用上的一个坑。解决办法也很简单，强制造成一次引用计数即可。

以下是对**func1**的改造
```cpp
void func1(int a) {
    std::map<int, std::shared_ptr<T> >::const_iterator iter = outter_map.find(a);
    if (iter != outter_map.end()) {
        // 这意味着调用方要保证被调用方不会出现问题，而间接关心被调用方的实现
        std::shared_ptr<T> cache = iter->second; 
        func2(cache);
    }
}
```

并且这个问题在迭代器内容不是智能指针的时候也存在，不过会导致解决方法更加复杂（因为不应该有对象的拷贝复制）。这里不再列举。

坑二：Linux环境下共享静态库的问题
------

这个问题之前就提及过[《C++又一坑:动态链接库中的全局变量》](https://www.owent.net/?p=962)现在则是碰到了更有代表性的实例。

我们的程序框架和逻辑模块的关系是。逻辑服务器编译成一个动态链接库，由框架执行**dlopen**加载。框架之间通信是采用[protobuf](https://github.com/google/protobuf),逻辑服务器和哭护短通信也采用的是[protobuf](https://github.com/google/protobuf)。那么问题就来了，两个模块都使用了[protobuf](https://github.com/google/protobuf)并且都是**静态链接**，而[protobuf](https://github.com/google/protobuf)里的协议描述信息又是全局的（我们这里体现在了**google::protobuf::FileDescriptorTables**这个类上，并且它在常量区），并且存在多种协议集合。

按照Linux的ABI的实现逻辑，这个全局的对象在框架层面会进行一次初始化构造，在动态链接库里又会执行一次初始化构造。并且次执行构造函数的this指针地址一样，成员（特别是STL）的构造数据地址不一样。

这些导致少量的内存泄露都还是其次，最重要的问题是，在析构的时候，dlclose会进行析构的内存回收，主框架也会。这就导致了回收了两遍，并且回收不完全。

我们这里检测到是在**google::protobuf::FileDescriptorTables**析构时hash table的析构的时候内存错误。而且由于现在的内存分配器都有容错，意味着**这个崩溃不是必现**的。使用debug版本的jemalloc可以100%复现这个问题，而使用release版的jemalloc或者ptmalloc或者tcmalloc的时候都不能及时发现。valgrind的检测信息大致如下：

```
==29910== Invalid read of size 8
==29910==    at 0x4F75F0: _M_deallocate_nodes (hashtable.h:467)
==29910==    by 0x4F75F0: clear (hashtable.h:1121)
==29910==    by 0x4F75F0: ~_Hashtable (hashtable.h:640)
==29910==    by 0x4F75F0: ~__unordered_map (unordered_map.h:43)
==29910==    by 0x4F75F0: ~unordered_map (unordered_map.h:180)
==29910==    by 0x4F75F0: ~hash_map (hash.h:172)
==29910==    by 0x4F75F0: google::protobuf::FileDescriptorTables::~FileDescriptorTables() (descriptor.cc:606)
==29910==    by 0x6212E48: __run_exit_handlers (in /usr/lib64/libc-2.17.so)
==29910==    by 0x6212E94: exit (in /usr/lib64/libc-2.17.so)
==29910==    by 0x61FBAFB: (below main) (in /usr/lib64/libc-2.17.so)
==29910==  Address 0x702f020 is 0 bytes inside a block of size 96 free'd
==29910==    at 0x4C2B131: operator delete(void*) (in /usr/lib64/valgrind/vgpreload_memcheck-amd64-linux.so)
==29910==    by 0x4F7650: deallocate (new_allocator.h:110)
==29910==    by 0x4F7650: _M_deallocate_buckets (hashtable.h:509)
==29910==    by 0x4F7650: ~_Hashtable (hashtable.h:641)
==29910==    by 0x4F7650: ~__unordered_map (unordered_map.h:43)
==29910==    by 0x4F7650: ~unordered_map (unordered_map.h:180)
==29910==    by 0x4F7650: ~hash_map (hash.h:172)
==29910==    by 0x4F7650: google::protobuf::FileDescriptorTables::~FileDescriptorTables() (descriptor.cc:606)
==29910==    by 0x62131B9: __cxa_finalize (in /usr/lib64/libc-2.17.so)
==29910==    by 0xF4C44E2: ???
==29910==    by 0x40146F0: _dl_close_worker (in /usr/lib64/ld-2.17.so)
==29910==    by 0x401525B: _dl_close (in /usr/lib64/ld-2.17.so)
==29910==    by 0x400F2F3: _dl_catch_error (in /usr/lib64/ld-2.17.so)
==29910==    by 0x52AA62C: _dlerror_run (in /usr/lib64/libdl-2.17.so)
==29910==    by 0x52AA10E: dlclose (in /usr/lib64/libdl-2.17.so)
```

结论
------
对于前一个问题，属于纯C++坑，对于第二个问题，虽然Windows环境下不会出现问题，但是要开发跨平台代码的话，势必要对开发过程做出规范。

如果要编写一个可以供其他多个模块使用的库（即不保证一个应用程序及其所依赖的动态链接库里链接这个库的次数总和<=1的情况下），应该符合下面的条件：

1. 编译成库的时候尽量使用动态链接库(带-fPIC)
2. 如果一定要使用静态库，则库里不能使用全局变量或静态局部变量
3. 如果实在不能避免使用全局或静态变量，这些变量必须是**POD类型**且一定不能有构造初始化
4. 因为**条件2**的原因，所以也基本和**单例模式**说ByeBye了

**条件1**的目的是，每个程序载入动态链接库之后再程序中只有一份地址空间，并且不会被重复载入。所以不会有问题。而是用静态库时，数据只有一份，代码却有多份。

**条件3**的原因在于，很有可能程序在执行一段时间之后再加载动态链接库，如果存在构造初始化，那么在加载这个动态链接库的时候还是会把之前初始化正常的数据给冲刷掉。

不过由于纯C没有构造初始化一说，所以语言层面就已经避免了**条件2**和**条件3**带来的问题。但是对**条件2**纯C仍然需要小心，特别是对于那些声明为启动main前执行的函数和退出后执行的函数。

> Written with [StackEdit](https://stackedit.io/).