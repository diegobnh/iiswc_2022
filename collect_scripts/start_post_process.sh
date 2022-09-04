#!/bin/bash

source app_dataset.sh

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
    echo "Running:"${APP_DATASET[$j]}

    cd ${APP_DATASET[$j]}/autonuma
    cp ../../post_process.sh .

    sudo ./post_process.sh ${APP[$j]} ${APP_DATASET[$j]}

    rm post_process.sh
    cd ../..
done

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
    echo "Running:"${APP_DATASET[$j]}

    cd ${APP_DATASET[$j]}/static_mapping
    cp ../../post_process.sh .

    sudo ./post_process.sh ${APP[$j]} ${APP_DATASET[$j]}

    rm post_process.sh
    cd ../..
done
