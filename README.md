# Title of Paper #

This directory contains instructions and codes for reproducing experiments submitted to the IEEE International Symposium on Workload Characterization (IISWC 2022).

The execution of the experiments is divided into three major phases:

* **Data collection**
  * In this phase, dynamic memory allocations and memory access samples of the monitored application are collected.
* **Post Process**
  * In this phase we postprocess the generated data (perf.data). This is because perf-script does not generate the data necessary for our analysis in its default mode. At the end, we will have a file formatted and ready for the next phase.
* **Mapping**
  * With the formatted data we carry out the mapping phase. In this phase we try to map each memory sample to its respective allocation using memory address and timestamp information.
 
After that we used shell scripts and python script to generate graphs and extract the results.
