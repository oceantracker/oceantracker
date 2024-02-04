from os import  environ

def config_numba_environment(settings):
    # set numba config via enviroment variables,
    # this must be done before first import of numba
    environ['numba_function_cache_size'] = str(settings['numba_function_cache_size'])

    if settings['debug']:
        environ['NUMBA_BOUNDSCHECK'] = '1'
        environ['NUMBA_FULL_TRACEBACKS'] = '1'