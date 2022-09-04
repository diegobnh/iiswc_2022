#!/bin/bash

source app_dataset.sh

for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
    echo "Running:"${APP_DATASET[$j]}

    sudo -u dmoura mkdir -p ${APP_DATASET[$j]}
    sudo -u dmoura mkdir -p ${APP_DATASET[$j]}/autonuma
    sudo -u dmoura chmod +777 ${APP_DATASET[$j]}/autonuma

    cd ${APP_DATASET[$j]}/autonuma
    rm -f *

    cp ../../run.sh .
    cp ../../../shared_library/mmap_intercept_only_to_trace.so .

    sudo ./run.sh ${APP[$j]} ${DATASET[$j]} autonuma

    rm run.sh *.so call_stack.txt
    cd ../..
done


for ((j = 0; j < ${#APP_DATASET[@]}; j++)); do
    echo "Running:"${APP_DATASET[$j]}

    sudo -u dmoura mkdir -p ${APP_DATASET[$j]}/static_mapping
    sudo -u dmoura chmod +777 ${APP_DATASET[$j]}/static_mapping

    cd ${APP_DATASET[$j]}/static_mapping
    rm -f *

    cp ../../run.sh .
    cp ../../../shared_library/mmap_intercept_to_static_bind.so .

    sudo ./run.sh ${APP[$j]} ${DATASET[$j]} static_mapping

    rm run.sh *.so call_stack.txt
    cd ../..
done
