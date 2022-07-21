import subprocess
import argparse
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-noplots', action='store_true')
    args = parser.parse_args()

    test_list=['test_DeakinPortPhilipBay', 'test_haurakiGulf2008',
               'test_laurin', 'test_jilian','test_laurin','test_NZnational',
               'test_SIdataCube', 'test_sounds']

    for test in test_list:
        if args.noplots:
            r = subprocess.call([test + ".py",'-noplot'], shell=True)
        else:
            r = subprocess.call([test + ".py"], shell=True)

        a=1