#!/bin/bash

allThreads=(64 32 16 8 4 2 1)
numTasks=64
for i in ${allThreads[@]};
do
	echo $i 'threads in parallel. Total Tasks:' $numTasks
	python3 test_oceantracker.py --hindcastpattern demoHindcast.nc --num_processors $i --num_case_copies $numTasks --hindcastdir ../demos/ | grep -e "Total Run Time"
done

