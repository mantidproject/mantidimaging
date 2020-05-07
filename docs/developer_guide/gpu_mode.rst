Current GPU Configuration / Limitations
---------------------------------------

To minimise the occurence of memory problems, the
:code:`MAX_CUPY_MEMORY_FRACTION` has been sent to 0.8. This means that
:code:`cupy` will assume it has access to no more than 80% of the GPU memory.

The :code:`MAX_GPU_SLICES` variable determines how many images are stored on
the GPU at any one time. This is currently set to 100 and does not take image
size or precision into account.

The median and outlier GPU operations only work for input arrays of type float32
or float64 in numpy. If you want to change this, you can start by editing the
:code:`_load_cuda_kernel` function to enable the CUDA code to recognise other
data types.

CUDA Filter Overview
--------------------

Both the median and remove outlier filters work by using an insertion sort
to obtain the median value of the neighbouring pixels in a 2D image. They can
only be used on a stack of 2D images with each image being passed to the
functions individually.

2D Median Filter
################

.. code-block:: C

    __global__ void two_dimensional_median_filter(float *data_array,
                                                  const float *padded_array,
                                                  const int X, const int Y,
                                                  const int filter_size) {


The arguments passed to the median filter are the original 2D image array, the
padded data array, the X and Y dimensions of the original image array, and the
filter size. All arguments besides the original data array are required to be
constant.

The :code:`__global__` header indicates that this function can be called from
the CPU.

.. code-block:: C

      unsigned int id_x = blockIdx.x * blockDim.x + threadIdx.x;
      unsigned int id_y = blockIdx.y * blockDim.y + threadIdx.y;

      if ((id_x >= X) || (id_y >= Y))
        return;

The program begins by obtaining the :code:`id_x` and :code:`id_y` values that
determine pixel for which the median will be found. If this is outside the
boundaries of the array then the function returns without doing anything.

The block and grid sizes are set in the Python code. This is discussed `here`.

.. code-block:: C

      unsigned int index = (id_x * Y) + id_y;
      unsigned int padded_img_width = Y + filter_size - 1;

If the :code:`id_x` and :code:`id_y` values are valid, then the program
translates this to an index in the unravelled array and calculates the width of
the padded image.

.. code-block:: C

      data_array[index] = find_neighbour_median(padded_array, padded_img_width,
                                                id_x, id_y, filter_size);

Finally, a helper method is called for finding the median value of a pixel in a
2D image. The result overwrites one of the pixels in the array. The helper
methods have the `__device__` keyword in their header as they are called solely
from the GPU.

The complete function is shown below:

.. code-block:: C

    __global__ void two_dimensional_median_filter(float *data_array,
                                                  const float *padded_array,
                                                  const int X, const int Y,
                                                  const int filter_size) {
      unsigned int id_x = blockIdx.x * blockDim.x + threadIdx.x;
      unsigned int id_y = blockIdx.y * blockDim.y + threadIdx.y;

      if ((id_x >= X) || (id_y >= Y))
        return;

      unsigned int index = (id_x * Y) + id_y;
      unsigned int padded_img_width = Y + filter_size - 1;

      data_array[index] = find_neighbour_median(padded_array, padded_img_width,
                                                id_x, id_y, filter_size);
    }

2D Remove Outlier Filter
########################

The remove outlier filters work in a similar way to the median filters. Upon
finding the median, rather than place this in the array right away, a check is
carried out to see if the original value is much higher or much lower than the
median based on the value of the :code:`diff` argument. The original value is
only overwritten if the condition is true.

.. code-block:: C

      if (data_array[index] - median >= diff)
        data_array[index] = median;

Slicing Algorithm
-----------------

The Python code determines how many images will be on the GPU at once. Upon
finding the "slice limit" L, the program sends the first L images from the stack
to the GPU and sends the first L padded images to the GPU. If the number of
images in the stack falls below the hard-coded :code:`GPU_SLICE_LIMIT` then the
entire image stack is sent to the GPU.

In the case where L is smaller than the size of the stack, the following
algorithm is performed:

.. code-block::

    **Function** ImagingFilter(ImageStack[][][], FilterSize, Args)

        N = |ImageStack|
        L = GetSliceLimit(N)

        Streams[] = CreateStreams(N)

        PaddedImageStack = CreatePaddedImages(ImageStack, FilterSize)

        GPUImages[][][] = SendDataToGPU(First L Elements of ImageStack, Streams)
        GPUPaddedImages[][][] = SendDataToGPU(First L Elements of
        PaddedImageStack, Streams)

        BlockSize, GridSize = GetBlockAndGridSizes(N)

        **For** i in N:

            **Use** Streams[i]

                **If** i >= L:
                    Overwrite GPUImages[i][][] with ImageStack[i][][]
                    Overwrite GPUPaddedImages[i][][] with
                    PaddedImageStack[i][][]

                **Synchronise** Streams[i]


Creating GPU Algorithms - Tips and Tricks
-----------------------------------------

Warming-up functions
####################

Upon creating a working CUDA function, it is advisable to run it on a smaller
array prior to running it with real data. In the case of the median and remove
outlier filters this takes place in the :code:`_warm_up` function in the
:code:`CudaExecuter` class which is called from the initialiser.

Block and grid arguments
************************


Development Pitfalls
--------------------

The filter was only peformed on part of the array or the filter works on small arrays then gets the wrong result for larger arrays.
###################################################################################################################################
This may mean that the grid and dimension arguments do not account for the
entire array.

Float parameters become 0 in CUDA
#################################
This indicates the value was not converted to a numpy :code:`float` or
:code:`single` prior to being passed to the kernel.

:code:`cupy` objects appear to forget what they are
###################################################
If you find calling :code:`stream.sychronize` or some other method results in an
error because this is not part of the Stream class, it may due to having
created an array in CUDA and failing to free it. As the number of un-freed
arrays accumulates, this scrambles the pointer addresses which leads to this
behaviour.

Further Work
------------

Intelligent management of :code:`OutOfMemoryError`
##################################################
Presently, the median and remove outlier GPU filters give up when this
error is encoutered. In the future, it may be worth finding a way to
reattempt the operation under different conditions so as to not fill the
GPU.

Avoid repeated warm-up compilation
##################################
The program works by creating a :code:`CudaExecuter` each time one of the
GPU-compatible filters is performed which required repeated warm-up compilation
even when the filters are run for different images with the same float
precision.

Intelligent management of maximum number of GPU slices
######################################################
Ideally, the number of images on a stack that are transferred to a GPU would
depend on their size and the capacity of the GPU being used
rather than simply being a fixed number. This may be a more suitable long-term
solution for avoiding memory problems and would also be better suited for
running the algorithms on different hardware with minimal manual tinkering.
