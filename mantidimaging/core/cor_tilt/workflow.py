from .auto import auto_find_cors


def run_auto_finding_on_images(
        images,
        model,
        roi,
        projections=None,
        cores=None,
        progress=None):
    """
    Performs automatic COR/Tilt finding on an image stack.
    """
    auto_find_cors(images.sample, roi, model, projections, cores, progress)
    model.linear_regression()
    update_image_operations(images, model)


def update_image_operations(images, model):
    """
    Updates the image operation history with the results in the given model.
    """
    images.record_parameters_in_metadata('cor_tilt_finding', **model.stack_properties)
