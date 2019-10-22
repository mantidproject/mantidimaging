import numpy as np


class SVModel:
    def __init__(self):
        pass

    @staticmethod
    def create_averaged_image(images):
        return np.mean(images, axis=0)
