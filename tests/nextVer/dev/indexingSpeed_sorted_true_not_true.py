# test uf numb based indexing faster than numpy indexing 
# and effect of meory spread to desice if to make ocean tracker index bassed from primary particle buffers


import numpy as np
import numba
import time 
import timeit


@numba.jit(nopython=True)
def addnumba(x1,x2, xout,ID):
 	for n in ID:
 		xout[n]= x1[n] + x2[n]
 	return xout

@numba.jit(nopython=True)
def true_not_true(x,ID):
	n1 = 0
	n2 = x.shape[0]
	for n in range(x.shape[0]):
		if x[n] < 0.5:
			ID[n1]= n
			n1 += 1
		else:
			n2 -= 1
			ID[n2] = n

	ID_true= ID[:n1]
	ID_false= ID[n2:]

	return ID_true,ID_false

N=10**7


x1=np.random.rand(N)
x2=np.random.rand(N)
xout=np.full_like(x1,np.nan)


id=np.random.choice(np.arange(N),N, replace=False)
id_presorted=np.sort(id)
id_presorted_reverse= id_presorted[-1:0:-1].copy()
t=[ 0., 0.,0.,0.,0.]
nreps=10
id_true_not_true= id_presorted.copy()
ID_true,ID_false =true_not_true(x1,id_true_not_true)

if 1 == 1:
	if np.any(x1[ID_true] >= 0.5): print('Bad trues', np.sum(np.any(x1[ID_true] >= 0.5)))
	if np.any(x1[ID_false] < .5): print('Bad falses', np.sum(np.any(x1[ID_true] < 0.5)))

junk=addnumba(x1,x2,xout,id) # pre complile

for n in range(nreps):

	t0=time.perf_counter()
	xout =addnumba(x1,x2,xout, id)
	t[0] += time.perf_counter()-t0
	if 1==0:
		t0=time.perf_counter()
		id_sorted = np.sort(id)
		xout=addnumba(x1,x2, xout, id_sorted)
		t[1] += time.perf_counter()-t0

	t0=time.perf_counter()
	xout=addnumba(x1,x2, xout, id_presorted)
	t[2] += time.perf_counter()-t0

	t0=time.perf_counter()
	xout=addnumba(x1, x2, xout, id_presorted_reverse)
	t[3] += time.perf_counter()-t0

print('Random',t[0],'\n sort on demand',t[1],
	  '\n pre sorted',t[2],'\n pre sorted reverse' ,t[3])

