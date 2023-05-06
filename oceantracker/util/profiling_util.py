from time import  perf_counter,sleep
from copy import  deepcopy

profile_type = None # no profiling

available_profile_types = ['none','oceantracker','cprofiler','line_profiler','scalene']
func_timings={}
timing_template = {'calls': 0, 'time': 0.,'time_first_call':0.}

def set_profile_mode(name):
    global profile_type
    profile_type = name
    if name =='scalene' :
        # this aviods always having scalene installed
        global scalene_profiler
        from scalene import scalene_profiler
    elif name=='line_profiler':
        pass

# Wrap the profiling decorator in another function that checks the global switch
def function_profiler(modual_name):
    # add file name to tag
    tag = modual_name.rsplit('oceantracker.',1)[-1].replace('.py','').replace('\\','.') # get file name with module

    def profiler_function(func):
        if profile_type is None:
            return func
        elif profile_type =='oceantracker':
            return functions_wrapper(func,tag)

        elif profile_type =='scalene':
            # just use function as is
            #return func
            #print('xxx-scalene', )
            return profile(func) # use scalene profile wrapper
        elif profile_type == 'line_profiler':
            # just use function as is
            # return func
            # print('xxx-scalene', )
            return profile(func)  # use scalene profile wrapper
        else:
            return func

    return profiler_function

def functions_wrapper(func,tag):
    def wrapper(*args, **kwargs):
        name=''
        if tag is not None : name +=' << '+ tag
        name = func.__name__ + name
        if name not in func_timings:
            func_timings[name] = deepcopy(timing_template)
        func_timings[name]['calls'] += 1
        t0 = perf_counter()

        result = func(*args, **kwargs)

        func_timings[name]['time'] += perf_counter() - t0
        if func_timings[name]['calls'] ==1:
            func_timings[name]['time_first_call'] =func_timings[name]['time']
        return result
    return wrapper

def scalene_wrapper(func,tag):
    def wrapper(*args, **kwargs):
        scalene_profiler.start()
        result = func(*args, **kwargs)
        # Turn profiling off
        scalene_profiler.stop()
        return result
    return wrapper

if __name__ == "__main__":
    # testing and timing of above routines

    set_profile_mode('functions')

    @function_profiler(__file__)
    def test_fun(a, b):
        sleep(.1)
        return a + b
    for n in range(10):
        c = test_fun(1,2)
    print(c)
    print(profile_type,func_timings)
