from os import  environ, path, mkdir

def config_numba_environment(settings):
    # set numba config via enviroment variables,
    # this must be done before first import of numba
    environ['numba_function_cache_size'] = str(settings['numba_function_cache_size'])

    if settings['numba_cache_code']:
       environ['OCEANTRACKER_NUMBA_CACHING'] = '1'
       environ['NUMBA_CACHE_DIR'] = path.join(settings['root_output_dir'], 'numba_cache')
    else:
        environ['OCEANTRACKER_NUMBA_CACHING'] = '0'


    if settings['debug']:
        environ['NUMBA_BOUNDSCHECK'] = '1'
        environ['NUMBA_FULL_TRACEBACKS'] = '1'