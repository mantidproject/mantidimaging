import numpy as np

HISTOGRAM_BIN_SIZE = 2048


def generate_histogram_from_image(image_data, bin_size=HISTOGRAM_BIN_SIZE):
    histogram, bins = np.histogram(image_data.flatten(), bin_size)
    center = (bins[:-1] + bins[1:]) / 2
    return (center, histogram, bins)
