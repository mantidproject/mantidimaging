GPU Notes
=============

The Median and Remove Outlier filters have the option of being run on the GPU.
This works by having the :code:`cupy` library import the CUDA module so that
Python is able to compile it, run it, and retrieve the results. Transferring
data to and from the GPU is quite time-consuming, so the degree of speed 
improvement you observe (or don't observe) depends on:

- the size of the data
- the float precision
- the number of floating point operations that the algorithm has to perform

Depending on these factors, the cost of data transfer may outweigh the GPU
processing improvement in which case you're better off using the CPU. In the
case of the median and remove outlier filters, using a larger filter size
increases the number of floating point operations required to obtain a result.
This means that if a speed improvement is observed for a filter size of 3,
filter sizes greater than 3 will produce an even larger speed improvement.

Current GPU Configuration / Limitations
-----------------------------------------

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

Median Filter
-------------

.. code-block:: C
 int something = 3;
 float something = 2;


Remove Outlier Filter
---------------------



Creating GPU Algorithms - Tips and Tricks
-----------------------------------------

Warming-up functions
####################

Upon creating a working CUDA function, it is advisable to run it on a smaller
array prior to running it with real data. In the case of the median and remove
outlier filters this takes place in the :code:`_warm_up` function in the
:code:`CudaExecuter` class which is called from the initialiser.

CUDA function example
#####################

Block and grid arguments
************************

Iterating through 2D and 3D arrays
**********************************

Slicing algorithm
#################

Development Pitfalls
--------------------

The filter was only peformed on part of the array or the filter works on small arrays then gets the wrong result for larger arrays.
#########################################################
This may mean that the grid and dimension arguments do not account for the
entire array.

Float parameters become 0 in CUDA
####################################
This indicates the value was not converted to a numpy :code:`float` or
:code:`single` prior to being passed to the kernel.

:code:`cupy` objects appear to forget what they area
#######################################################
If you find calling :code:`stream.sychronize` or some other method results in an
error because this is not part of the Stream class, it may due to having
created an array in CUDA and failing to free it. As the number of un-freed
arrays accumulates, this scrambles the pointer addresses which leads to this
behaviour.

Further Work
------------

Intelligent management of :code:`OutOfMemoryError`
#################################################
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
