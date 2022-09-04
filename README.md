# Performance Characterization of AutoNUMA Memory Tiering on Graph Analytics #

This directory contains instructions and codes for reproducing experimental results presented in "Performance Characterization of AutoNUMA Memory Tiering on Graph Analytics". This paper is accepted for publication at 2022 IEEE International Symposium on Workload Characterization (IISWC 2022). To run these artifacts, a machine with Intel Optane is required.

The execution of the experiments is divided into three major phases:

* **Data collection**
  * In this phase, dynamic memory allocations and memory access samples of the monitored application are collected.
  * This data is collected through the ***run.sh*** script.
* **Post Process**
  * In this phase we postprocess the generated data (perf.data). This is because perf-script does not generate the data necessary for our analysis in its default mode. At the end, we will have a file formatted and ready for the next phase.
  * This second step is performed by executing the ***post_process.sh*** script.
* **Mapping**
  * With the formatted data we carry out the mapping phase. In this phase we try to map each memory sample to its respective allocation using memory address and timestamp information.
  * This step is accomplished by running a python program called ***mapping.py***.
 
After that we used shell scripts and python script to generate graphs and extract the results.

## Requirements

* ***CPU support*** We use Intel(R) Xeon(R) Gold 6240 CPU. But any other CPU supporting Intel Optane is suitable to perform the experiment. Also, intel optane memory is required.
* ***Linux support*** We use Linux Kernel 5.15. The kernel must be greater than or equal to kernel 5.1 as it is from this version that the kernel brings support for the volatile-use of persistent memory as a hotplugged memory region (KMEM DAX). When this feature is enabled, persistent memory is seen as a separate memory-only NUMA node(s).
* ***Utilities*** It is also necessary to install the [syscall-intercept](https://github.com/pmem/syscall_intercept) library responsible for intercepting memory allocations in user space. We also use [ipmctl](https://github.com/intel/ipmctl/releases) and [ndctl](https://github.com/pmem/ndctl) to configure intel optane and instantiate as numa node.

## Installation
* sudo sh -c 'echo 0 >/proc/sys/kernel/perf_event_paranoid'
