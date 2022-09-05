#!/bin/bash

source app_dataset.sh

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
    echo "Running:"${APP_DATASET[$j]}
    cd ${APP_DATASET[$j]}/autonuma
    cd ../..
    cd ${APP_DATASET[$j]}/static_mapping/
    time python3 -W ignore ../../mapping.py $(pwd)
    cd ../..
done
