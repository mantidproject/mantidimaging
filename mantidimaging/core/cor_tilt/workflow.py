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
    images.properties.update(model.stack_properties)
