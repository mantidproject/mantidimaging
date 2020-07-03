from mantidimaging.core.data import Images
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress


def parallel_move_data(input_data, output_data):
    """
    Forwarded function for parallel loading of data
    :param input_data: shared_data

    :param output_data: second_shared_data

    """
    output_data[:] = input_data[:]


def do_stack_load_seq(data, new_data, img_shape, name, progress):
    """
    Sequential version of loading the data.
    This performs faster locally, but parallel performs faster on SCARF

    :param data: shared array of data
    :param new_data: the new data to be moved into the shared array
    :param img_shape: The shape of the image
    :param name: Name for the loading bar
    :return: the loaded data
    """
    num_images = img_shape[0]
    progress = Progress.ensure_instance(progress, num_steps=num_images, task_name=name)

    with progress:
        for i in range(num_images):
            data[i] = new_data[i]
            progress.update(msg='Image {} of {}'.format(i, num_images))

    return data


def execute(load_func, file_name, dtype, name, indices=None, progress=None):
    """
    Load a single image FILE that is expected to be a stack of images.

    Parallel execution can be slower depending on the storage system.

    On HDD I've found it's about 50% SLOWER, thus not recommended!

    :param file_name: list of image file paths given as strings

    :param load_func: file name extension if fixed (to set the expected image
                      format)

    :param dtype: data type for the output numpy array

    :return: stack of images as a 3-elements tuple: numpy array with sample
             images, white image, and dark image.
    """
    # create shared array
    new_data = load_func(file_name)

    if indices:
        new_data = new_data[indices[0]:indices[1]:indices[2]]

    img_shape = new_data.shape
    data = pu.create_array(img_shape, dtype=dtype, name=f"{file_name}-Stack")

    # we could just move with data[:] = new_data[:] but then we don't get
    # loading bar information, and I doubt there's any performance gain
    data = do_stack_load_seq(data, new_data, img_shape, name, progress)

    # Nexus doesn't load flat/dark images yet, if the functionality is
    # requested it should be changed here
    return Images(data, None, None, file_name)
