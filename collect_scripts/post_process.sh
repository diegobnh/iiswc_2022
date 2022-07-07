#!/bin/bash
#sudo ./post_process.sh bfs bfs_kron'

if [[ $# -eq 0 ]] ; then
    echo 'you should pass two arguments. E.g. sudo ./post_process.sh bfs bfs_kron '
    exit 1
fi


cat "allocations_"$2".csv" | grep munmap > munmap_trace_$2.csv
cat "allocations_"$2".csv" | grep mmap > mmap_trace_$2.csv


#report
#perf mem report -f --stdio --sort=mem > report_$2 2> /dev/null

#loads
perf script -f --comms=$1 | sed 's/cpu\/mem-loads,ldlat=30\/P:/loads/g' | sed 's/cpu\/mem-stores\/P:/stores/g' | grep -w "loads" | sed 's/Local RAM or RAM/Ram_hit/g' | sed 's/LFB or LFB hit/LFB_hit/g' | sed 's/L1 or L1 hit/L1_hit/g' | sed 's/L2 or L2 hit/L2_hit/g' | sed 's/L3 or L3 hit/L3_hit/g' | sed 's/L3 miss/L3_miss/g' | sed 's/PMEM hit/PMEM_hit/g' | tr -d ":" | sed 's/|SNP//g' | awk '{OFS=","}{print $4,"0x"$7,$9}' > loads.txt

#second we get time, thread, event (the event column is only to use as an filter)
#perf script -f --comms=$1 -Ftid,time,weight,event | sed 's/cpu\/mem-loads,ldlat=30\/P:/loads/g' | sed 's/cpu\/mem-stores\/P:/stores/g' | grep -w "loads" | awk '{OFS=","}{print $4,$1}' | tr -d ":" > latency.txt
perf script -f --comms=$1 -Ftid,time,weight,event,phys_addr | sed 's/cpu\/mem-loads,ldlat=30\/P:/loads/g' | sed 's/cpu\/mem-stores\/P:/stores/g' | grep -w "loads" | awk '{OFS=","}{print $1,$4,"0x"$5}' | tr -d ":" > tid_weight_phys_addr.txt

#now we merge side by side
#paste loads.txt latency.txt -d "," > temp
paste loads.txt tid_weight_phys_addr.txt -d "," > temp
mv temp loads.txt

#get tlb information (available only to loads)
perf script -f --comms=$1 | sed 's/cpu\/mem-loads,ldlat=30\/P:/loads/g' | sed 's/cpu\/mem-stores\/P:/stores/g' | grep -w "loads" | sed 's/TLB L1 or L2 hit/TLB_hit/g' | sed 's/TLB L2 miss/TLB_miss/g' | awk -F'|' '{print $3}' > tlb.txt
paste loads.txt tlb.txt -d "," > temp
mv temp loads.txt
#insert new column with caracter r
sed -i "s/$/,r/" loads.txt

#stores
#perf script -f --comms=$1 | sed 's/cpu\/mem-loads,ldlat=30\/P:/loads/g' | sed 's/cpu\/mem-stores\/P:/stores/g' | grep -w "stores" | sed 's/L1 hit/L1_hit/g' | sed 's/L1 miss/L1_miss/g' | awk '{OFS=","}{print $4,"0x"$7,$9,0,$2,"TLB_null,w"}' | tr -d ":" | sed 's/|SNP//g' >  stores.txt

#merge loads and stores
#cat loads.txt stores.txt > "memory_trace_"$2".csv"
mv loads.txt "memory_trace_"$2".csv"

#delete files
rm -f *.txt



