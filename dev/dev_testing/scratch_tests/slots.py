from timeit import timeit

class Base(object):
    __slots__ = ['params', 'data','val2']
    s= 1
    def __init__(self):

        self.val1=1.
        self.val2=1.
class A(Base):pass
N=10**7

def F(a):
    return A+1
F(1)
a=A()
t1=timeit(lambda : a.val1,number=N)

a=A()
t2=timeit(lambda : a.val2,number=N)
print(t1,t2,t2/t1)







