import numpy as np
from numba import njit, prange
from timeit import timeit
@njit()
def find_interval_right(data, val):
    # binary search for interval index in sorted data unevenly spaced
    #  data[index] <= val < data[index+1]
    left = 0
    right = data.size-1
    while right - left > 1:
        index = (right+left) // 2
        if val >= data[index]:
            left = index
        elif val < data[index]:
            right= index

    return left


if __name__ == "__main__":
    @njit(parallel=True )
    def test(vals,data, out):

        #for n, v in enumerate(vals):
        for n in prange(vals.size):
            out[n] = find_interval_right(data, vals[n])

    N=10**6
    M=50
    reps=7000
    data = np.random.rand(M)
    data = np.append(0, np.cumsum(data))

    vals=data[-1]*np.random.rand(N)
    out= np.ones((N,),dtype=np.int32)

    t = timeit(lambda: test(vals, data, out), setup=lambda:test(vals, data, out),number=reps)
    print('time',t ,', ms per rep',t*1000/reps)

    ok = np.logical_and( vals >= data[out] , vals < data[out+1] )
    print('bad ' , np.sum(~ok))


    #print(out)
    #print(data)





