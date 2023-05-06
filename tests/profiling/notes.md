
# line_profiler

kernprof -l -v profileOT.py -test

kernprof -l -v profileOT.py -test > output.txt


# scalene

python -m scalene --profile-all profileOT.py --d 2 --pr 2
