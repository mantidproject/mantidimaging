import logging
import matplotlib.pyplot as plt
import numpy as np
from mantidimaging.helper import initialise_logging
from mantidimaging.core.io.loader import load
from mantidimaging.core.reconstruct import calculate_cor_and_tilt


initialise_logging(logging.DEBUG)

stack = load(input_path='~/babylon5/DanNixon/PSI_Cylinder/Sample/',
             indices=(0, 943, 50))

roi = (800, 700, 2000, 1600)
# roi = (800, 700, 2000, 1800)

indices = np.arange(roi[3] - 1, roi[1], -50)

tilt, cor, slices, cors = calculate_cor_and_tilt(stack.sample, roi, indices)

# Plot COR fit
plt.subplot(121)
plt.plot(slices, cors)
plt.plot(slices, [tilt * s + cor for s in slices])

# Plot image and tilt
plt.subplot(122)
plt.imshow(stack.sample[0], cmap='Greys_r')
plt.plot([cor, cors[-1]], [indices[0], indices[-1]], lw=2, c='y')

plt.show()
