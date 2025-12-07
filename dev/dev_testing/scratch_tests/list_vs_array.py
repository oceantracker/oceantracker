from numba import njit, types,typed
import numpy as np
from timeit import timeit, repeat
from time import perf_counter


#@njit
def build_array(n_items,block_size=10):
    result = np.full((n_items.size,block_size),0,dtype=np.int32)

    for n in range(n_items.size):
        if n_items[n] >  result.shape[1]:
            b = int((n_items[n]-result.shape[1]))
            result= np.concat((result,-np.ones((n_items.size,b),dtype=result.dtype)),axis=1)
        for m in range(n_items[n]):
            result[n,m] = 10

    return result[:,:n_items.max()].copy()

@njit
def build_list(n_items):
    #result =  typed.List()
    #result= typed.List.empty_list(types.ListType(types.int32))
    #
    #typed.List[]
    #result= []
    #result=typed.List()
    result = typed.List.empty_list( types.int32[:])
    for n in range(n_items.size):
        b = n_items[n]*[10]
        result.append(np.asarray(b).astype(np.int32))

    return result

def build_list(n_items):
    #result =  typed.List()
    #result= typed.List.empty_list(types.ListType(types.int32))
    #
    #typed.List[]
    #result= []
    #result=np.zeros((n_items.size),dtype= types.int32[:])
    result = typed.List.empty_list( types.int32[:])
    for n in range(n_items.size):
        b = n_items[n]*[10]
        result.append(np.asarray(b).astype(np.int32))

    return result

@njit
def array_lookup(array_map,n_items):
    s= 0
    for n in range(array_map.shape[0]):
        for m in range(n_items[n]):
            s += array_map[n,m]
    return s

@njit
def list_lookup(list_map):
    s= 0
    for l in list_map:
        for m in range(l.size):
            s += l[m]
    return s

reps = 1000
N = 10**5
max_items = 50
n_items = np.random.randint(0,max_items,size=N)

t0 = perf_counter()
array_map= build_array(n_items)
print('array build',perf_counter()-t0)

t0 = perf_counter()
list_map= build_list(n_items)
print('list build',perf_counter()-t0)

ta= np.asarray(repeat(lambda: array_lookup(array_map,n_items),
          setup=lambda: array_lookup(array_map,n_items), number=1, repeat=reps))
print(f'array lookup min {ta.mean():5.4f}  sec, std { ta.std()/ta.mean():5.2%} ', ta.mean()*1000/reps, ' ms/loop')

t= np.asarray(repeat(lambda: list_lookup(list_map),
          setup=lambda: list_lookup(list_map), number=1, repeat=reps))
print(f'list lookup min {t.mean():5.4f} sec, std { t.std()/t.mean():5.2%} ', ta.mean()*1000/reps, ' ms/loop')
print('check', array_lookup(array_map,n_items),list_lookup(list_map),'relative',  t.mean()/ta.mean())
