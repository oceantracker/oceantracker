from time import sleep, perf_counter
import pickle
class C():

    def __init__(self):
        a=1

    def run(self):
        t0 = perf_counter()

        for n in range(100000):
            print(n)
            if (perf_counter()-t0) > 10:
                pickle
            sleep(.2)




if __name__ == "__main__":
    dir = r'D:\temp\pickle_test'
    c= C()

    c.run()


