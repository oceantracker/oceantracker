import numpy as np
from numba import cuda, njit
import math
from time import  perf_counter


@njit()
def cpu_add(x, y, out, n):
        for m in range(n):
          out[m] = x[m] + y[m] + np.sin(y[m] )


# Define the CUDA kernel function
@cuda.jit
def vector_add_kernel(x, y, out, n):
    """
    Kernel function to add two vectors on the GPU.
    Each thread handles a single element.
    """
    # Calculate the unique thread index
    idx = cuda.grid(1)

    # Ensure the thread index is within the array bounds
    if idx < n:
        out[idx] = x[idx] + y[idx] + np.sin(y[idx] )


# Host function to manage data and kernel launch
def main():
    # 1. Define array size and create sample data on the CPU
    N = 1_000_000
    x_host = np.arange(N, dtype=np.float32)
    y_host = np.arange(N, dtype=np.float32)
    out_host = np.zeros(N, dtype=np.float32)  # Output array on CPU

    # 2. Transfer data from CPU memory (host) to GPU memory (device)
    x_device = cuda.to_device(x_host)
    y_device = cuda.to_device(y_host)
    out_device = cuda.to_device(out_host)

    # 3. Configure kernel launch parameters (threads per block, blocks per grid)
    threads_per_block = 1024
    # Calculate required blocks to cover N elements
    blocks_per_grid = (N + (threads_per_block - 1)) // threads_per_block

    print(f"Launching kernel with {blocks_per_grid} blocks and {threads_per_block} threads per block.")

    # 4. Launch the kernel on the GPU
    # The [blocks_per_grid, threads_per_block] syntax invokes the kernel
    reps=1000
    vector_add_kernel[blocks_per_grid, threads_per_block](x_device, y_device, out_device, N)
    t0 = perf_counter()
    for r in range(reps):
        vector_add_kernel[blocks_per_grid, threads_per_block](x_device, y_device, out_device, N)
    cuda.synchronize()
    print('cuda', perf_counter()-t0)
    # Wait for the GPU to finish (implicit synchronization here with copy_to_host)
    cuda.synchronize()

    # 5. Copy the results back to the CPU
    out_host_results = out_device.copy_to_host()

    # 6. Verify results
    cpu_add(x_host, y_host, out_host, N)
    t0 = perf_counter()
    for r in range(reps):
        cpu_add(x_host, y_host, out_host, N)
    print('numba', perf_counter() - t0)

    #assert np.allclose(out_host_results, x_host + y_host)
    print("Verification successful!")


if __name__ == "__main__":

    cuda.detect()
    print('uda',  cuda.is_available(),cuda.detect())

    main()