#!/bin/bash

source ../collect_scripts/app_dataset.sh

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
        echo "Running:"${APP_DATASET[$j]}
        #cd ${APP_DATASET[$j]}/autonuma
        cd ${APP_DATASET[$j]}/static_mapping/

        time python3 -W ignore /ix/dmosse/dmoura/iiswc_2022/plots.py
        mkdir plots
        mv *.pdf plots

        cd ../..
done
