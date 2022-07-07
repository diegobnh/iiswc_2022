#!/bin/bash

#./collect_touches_per_page.sh > touches_per_pages.csv

APP_DATASET=("bc_kron" "bfs_kron" "bfs_urand" "cc_kron" "cc_urand")

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do

        one_touch=$(grep "1 touch" ${APP_DATASET[$j]}/autonuma/df_touch_per_page_${APP_DATASET[$j]}.csv | awk -F, '{print $2}')
        two_touches=$(grep "2 touches" ${APP_DATASET[$j]}/autonuma/df_touch_per_page_${APP_DATASET[$j]}.csv | awk -F, '{print $2}')

	echo ${APP_DATASET[$j]},$one_touch,$two_touches
done
