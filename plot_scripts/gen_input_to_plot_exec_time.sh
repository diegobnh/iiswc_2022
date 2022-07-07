#!/bin/bash
#./collect_exec_time_gain.sh > input_exec_time.csv

APP_DATASET=("bc_kron" "bc_urand" "bfs_kron" "bfs_urand" "cc_kron" "cc_urand")

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do

	start=$(sed -n 2p ${APP_DATASET[$j]}/autonuma/track_info_${APP_DATASET[$j]}.csv | awk -F, '{print $1}')
	end=$(tail -n 1 ${APP_DATASET[$j]}/autonuma/track_info_${APP_DATASET[$j]}.csv | awk -F, '{print $1}')
	exec_time_autonuma=$(echo $start $end | awk '{print ($2-$1)/60}')

	#echo $exec_time_autonuma

	start=$(sed -n 2p ${APP_DATASET[$j]}/static_mapping/track_info_${APP_DATASET[$j]}.csv | awk -F, '{print $1}')
	end=$(tail -n 1 ${APP_DATASET[$j]}/static_mapping/track_info_${APP_DATASET[$j]}.csv | awk -F, '{print $1}')
	exec_time_static_mapping=$(echo $start $end | awk '{print ($2-$1)/60}')

	#echo $exec_time_static_mapping
	echo -n ${APP_DATASET[$j]},$exec_time_autonuma,$exec_time_static_mapping,

	echo $exec_time_static_mapping $exec_time_autonuma | awk '{print (1-($1/$2))*100}'
done
