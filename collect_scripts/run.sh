#!/bin/bash

if [ $# -eq 3 ] ; then
    echo "You must passed three arguments!"
    echo "e.g.  sudo ./run.sh bc kron autonuma"
    echo "e.g.  sudo ./run.sh bc kron static_mapping"
    exit
fi

rm -f *.csv *.txt
rm -f perf.data*

export OMP_NUM_THREADS=18
export OMP_PLACES={0}:18:2 #bind this script to run in only one socket . In our case, node 0!
export OMP_PROC_BIND=true


function setup_static_mapping_parameters {
    sudo sysctl -w kernel.perf_event_max_sample_rate=10000 1> /dev/null
    sudo sysctl -w kernel.numa_balancing=0 >  /dev/null
    sudo sh -c "echo false > /sys/kernel/mm/numa/demotion_enabled"
    sudo sh -c "echo 65536 > /proc/sys/kernel/numa_balancing_rate_limit_mbps"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_wake_up_kswapd_early"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_scan_demoted"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_demoted_threshold"
    sudo sysctl -w vm.vfs_cache_pressure=100 > /dev/null
    sudo sysctl -w vm.drop_caches=3 > /dev/null
}

function setup_autonuma_parameters {
    sudo sysctl -w kernel.perf_event_max_sample_rate=10000 1> /dev/null
    sudo sysctl -w kernel.numa_balancing=2 >  /dev/null
    sudo sh -c "echo true > /sys/kernel/mm/numa/demotion_enabled"
    sudo sh -c "echo 65536 > /proc/sys/kernel/numa_balancing_rate_limit_mbps"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_wake_up_kswapd_early"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_scan_demoted"
    sudo sh -c "echo 0 > /proc/sys/kernel/numa_balancing_demoted_threshold"
    sudo sysctl -w vm.vfs_cache_pressure=100 > /dev/null
    sudo sysctl -w vm.drop_caches=3 > /dev/null
}

function track_info {
    rm -rf track_info*
    #While application dosen't exist, we continue in this loop
    while true
    do
        app_pid=$(pidof $1)
        if ps -p $app_pid > /dev/null 2> /dev/null
        then
            break
        fi
    done

    track_info="track_info_"$2".csv"
    rm -f $track_info

    echo "timestamp,dram_app,pmem_app,dram_page_cache_active,dram_page_cache_inactive,pmem_page_cache_active,pmem_page_cache_inactive,pgdemote_kswapd,promote_threshold,pgpromote_candidate,pgpromote_success,pgpromote_demoted,cpu_usage"  >> $track_info
    while true
    do
    if ps -p $app_pid > /dev/null
    then
        sec=$(date +%s)
        nanosec=$(date +%s)
        timestamp=$(awk '{print $1}' /proc/uptime)
        memory=$(numastat -p $app_pid -c | grep Private | awk '{printf "%s,%s\n", $2,$4}')
        dram_page_cache=$(grep "Active(file)\|Inactive(file)" /sys/devices/system/node/node0/meminfo | awk '{print $(NF-1)}' | datamash transpose | awk '{printf "%s,%s\n", $1, $2}')
        pmem_page_cache=$(grep "Active(file)\|Inactive(file)" /sys/devices/system/node/node2/meminfo | awk '{print $(NF-1)}' | datamash transpose | awk '{printf "%s,%s\n", $1, $2}')
        counters=$(grep -E 'pgdemote_kswapd|promote_threshold|pgpromote_candidate|pgpromote_success|pgpromote_demoted' /proc/vmstat | awk '{print $2}' | datamash transpose | awk '{printf "%s,%s,%s,%s,%s\n", $1, $2, $3, $4, $5}')
        cpu_idle=`top -b -n 1 | grep Cpu | awk '{print $8}'| cut -f 1 -d "."`
        cpu_use=`expr 100 - $cpu_idle` 
        cpu_use=$(($cpu_use * 2))
        echo $timestamp","$memory","$dram_page_cache","$pmem_page_cache","$counters","$cpu_use >> $track_info
    else
        break
    fi
        sleep 1
    done
}

perf mem -D --phys-data record -k CLOCK_MONOTONIC --all-user 2> /dev/null &
track_info $1 "${1}_${2}" &

if [[ $3 == "autonuma" ]]; then
    setup_autonuma_parameters
    export APP="${1}["    #if you dont put [, sometimes we will collect wrong things for example libc.so[ and ./bc[ both has "bc" string
    if [[ $1 == "bc" ]]; then
        LD_PRELOAD=./mmap_intercept_only_to_trace.so /scratch/gapbs/./$1 -f /scratch/gapbs/benchmark/graphs/$2".sg" 1> /dev/null 2> "allocations_"$1"_"$2".csv"
    else
        LD_PRELOAD=./mmap_intercept_only_to_trace.so /scratch/gapbs/./$1 -f /scratch/gapbs/benchmark/graphs/$2".sg" -n128 1> /dev/null 2> "allocations_"$1"_"$2".csv"
    fi
elif [[ $3 == "static_mapping" ]] ; then
    setup_static_mapping_parameters
    export APP="${1}["    #if you dont put [, sometimes we will collect wrong things for example libc.so[ and ./bc[ both has "bc" string
    if [[ $1 == "bc" ]]; then
        LD_PRELOAD=./mmap_intercept_to_static_bind.so /scratch/gapbs/./$1 -f /scratch/gapbs/benchmark/graphs/$2".sg" 1> /dev/null 2> "allocations_"$1"_"$2".csv"
    else
        LD_PRELOAD=./mmap_intercept_to_static_bind.so /scratch/gapbs/./$1 -f /scratch/gapbs/benchmark/graphs/$2".sg" -n128 1> /dev/null 2> "allocations_"$1"_"$2".csv"
    fi
else
    echo "Invalid parameter!"
fi;

pkill perf &> /dev/null


