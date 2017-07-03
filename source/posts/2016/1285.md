---
title: Android和IOS的TLS问题
tags:
  - c++0x/11
  - c++11
  - g++
  - gcc
  - 多线程
id: 1285
categories:
  - Article
  - Blablabla
  - Work
date: 2016-07-09 14:15:14
---

Android和IOS的TLS问题
======

这个问题起源于以前给客户端写的一个log模块，然后里面为了线程安全且多线程下不互相写乱，并且因为这些系统基本都用比较高版本的编译器，都支持C++11了，所以就用了C++11的TLS功能。

但是Android的默认std库并不是libstdc++或者libc++，而是[Bionic](http://en.wikipedia.org/wiki/Bionic_%28software%29#cite_note-Gentry-6)。IOS不知道是什么版本的标准库都不支持thread_local的关键字。
这个之前写过一个记录提到过 [Android NDK undefined reference to ___tls_get_addr 错误](https://www.owent.net/41UTL)。如果使用这个关键字，链接的时候会报错说找不到符号。

当时梅花太多时间，而是在这两个环境下直接用了加锁的方式。但是我们开发在Windows上，实际发布产品的时候是在Android和IOS上，这么做也就意味着开发时性能高过发布的代码。这显然不够美好，所以这两天做底层优化就顺带解决了一下。

解决方法也很简单，这两种系统虽然不支持C++11的TLS关键字，但是它们支持pthread规范啊。那么就可以这种情况直接用pthread来处理。（如果以后需要适配Windows Phone系统，并且又不支持的话再想其他办法吧）。
简化的代码如下:
```cpp
#if defined(THREAD_TLS_ENABLED) && 1 == THREAD_TLS_ENABLED
namespace util {
    namespace log {
        namespace detail {
            char *get_log_tls_buffer() {
                static THREAD_TLS char ret[LOG_WRAPPER_MAX_SIZE_PER_LINE];
                return ret;
            }
        }
    }
}
#else

#include <pthread.h>
namespace util {
    namespace log {
        namespace detail {
            static pthread_once_t gt_get_log_tls_once = PTHREAD_ONCE_INIT;
            static pthread_key_t gt_get_log_tls_key;

            static void dtor_pthread_get_log_tls(void *p) {
                char *buffer_block = reinterpret_cast<char *>(p);
                if (NULL != buffer_block) {
                    delete[] buffer_block;
                }
            }

            static void init_pthread_get_log_tls() { (void)pthread_key_create(&gt_get_log_tls_key, dtor_pthread_get_log_tls); }

            char *get_log_tls_buffer() {
                (void)pthread_once(&gt_get_log_tls_once, init_pthread_get_log_tls);
                char *buffer_block = reinterpret_cast<char *>(pthread_getspecific(gt_get_log_tls_key));
                if (NULL == buffer_block) {
                    buffer_block = new char[LOG_WRAPPER_MAX_SIZE_PER_LINE];
                    pthread_setspecific(gt_get_log_tls_key, buffer_block);
                }
                return buffer_block;
            }
        }
    }
}

#endif

// 然后后面需要用缓冲区的时候用get_log_tls_buffer()函数获取
```

完整代码见： https://github.com/atframework/atframe_utils/blob/master/src/log/log_wrapper.cpp