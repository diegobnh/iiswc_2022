#!/bin/bash

#./collect_percentage_access_DRAM_and_PMEM.hs > percentage_access_DRAM_and_PMEM

APP_DATASET=("bc_kron" "bc_urand" "bfs_kron" "bfs_urand" "cc_kron" "cc_urand")

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do

	dram=$(grep RAM ${APP_DATASET[$j]}/autonuma/perc_access_pmem_dram_${APP_DATASET[$j]}.csv | awk -F, '{print $2}')
        pmem=$(grep PMEM ${APP_DATASET[$j]}/autonuma/perc_access_pmem_dram_${APP_DATASET[$j]}.csv | awk -F, '{print $2}')

	echo ${APP_DATASET[$j]},$dram,$pmem
done
