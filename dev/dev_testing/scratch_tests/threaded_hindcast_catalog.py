import glob
# C:\data\gulf
import threading
from netCDF4 import Dataset
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter, sleep

def worker_read_vars(file_name):
   nc = Dataset(file_name, 'r')
   variables = {}
   for var_name, var in nc.variables.items():
       variables[var_name] = {
           'datatype': str(var.dtype),
           'dimensions': var.dimensions,
           'shape': var.shape,
           'attributes': {attr: var.getncattr(attr) for attr in var.ncattrs()}
       }
   nc.close()
   #sleep(.01)

   return variables

def variables_catalog(file_list):
    # Create a thread pool executor
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks and create a list of Future objects
        futures = [executor.submit(worker_read_vars, fn) for fn in file_list]

        # 3. Retrieve the dictionaries as they complete

        for future in as_completed(futures):
            try:
                thread_dict = future.result()  # This holds the returned dict
                results.append(thread_dict)
            except Exception as e:
                print(f"Thread generated an exception: {e}")

    return results

if __name__ == "__main__":
    file_mask=r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\**\NZ*.nc'
    #file_mask = r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\2010\**\NZ*.nc'
    file_list = glob.glob(file_mask, recursive=True)
    print('files' , len(file_list), len(set(file_list)))

    t0 = perf_counter()
    v1=[]
    for fn in file_list:
        v1.append(worker_read_vars(fn))
    print('no thread time', perf_counter() - t0)

    t0 = perf_counter()
    v2 = variables_catalog(file_list)
    print('thread time',perf_counter()-t0)



    #print(v)
