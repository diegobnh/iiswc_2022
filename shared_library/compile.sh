#!/bin/bash

gcc -fno-pie mmap_intercept_to_static_bind.c -rdynamic -fpic -shared -o mmap_intercept_to_static_bind.so -lnuma -lsyscall_intercept
gcc -fno-pie mmap_intercept_only_to_trace.c -rdynamic -fpic -shared -o mmap_intercept_only_to_trace.so -lnuma -lsyscall_intercept

