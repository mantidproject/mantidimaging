# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os

import matplotlib
import numpy as np
from matplotlib import pyplot

import astra
import SharedArray as sa

os.environ["DISPLAY"] = ":1"
matplotlib.use("Qt5Agg")

sinos = sa.attach('54a12d99-9ed2-4f23-963a-3fa4ac47ba7d')

cor = 0.0014
proj_angles = np.deg2rad(np.linspace(0, 360, sinos.shape[1]))


def rotation_matrix2D(theta):
    return np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])


# astra = safe_import('astra')
def vec_geom_init2D(angles_rad, DetectorSpacingX, CenterRotOffset):
    s0 = [0.0, -1.0]  # source
    u0 = [DetectorSpacingX, 0.0]  # detector coordinates
    vectors = np.zeros([angles_rad.size, 6])
    for i, theta in enumerate(angles_rad):
        if np.ndim(CenterRotOffset) == 0:
            d0 = [CenterRotOffset, 0.0]  # detector
        else:
            d0 = [CenterRotOffset[i], 0.0]  # detector
        vectors[i, 0:2] = np.dot(rotation_matrix2D(theta), s0)  # ray position
        vectors[i, 2:4] = np.dot(rotation_matrix2D(theta), d0)  # center of detector position
        vectors[i, 4:6] = np.dot(rotation_matrix2D(theta), u0)  # detector pixel (0,0) to (0,1).
    return vectors


def vec(cor, slice_idx=1300):
    sino = sinos[slice_idx]
    vectors = vec_geom_init2D(proj_angles, 1.0, cor)
    vol_geom = astra.create_vol_geom(sinos.shape[0], sinos.shape[2])
    proj_geom = astra.create_proj_geom('parallel_vec', sino.shape[1], vectors)
    # proj_geom = astra.create_proj_geom('parallel', 1.0, sample.shape[1], proj_angles)
    proj_id = astra.create_projector('cuda', proj_geom, vol_geom)
    sino_id = astra.data2d.create('-sino', proj_geom, sino)
    rec_id = astra.data2d.create('-vol', vol_geom)
    cfg = astra.astra_dict('FBP_CUDA')
    cfg['ReconstructionDataId'] = rec_id
    cfg['ProjectionDataId'] = sino_id
    cfg['FilterType'] = 'ram-lak'
    cfg['ProjectorId'] = proj_id
    alg_id = astra.algorithm.create(cfg)
    astra.algorithm.run(alg_id)
    recon = astra.data2d.get(rec_id)
    astra.data2d.delete(sino_id)
    astra.data2d.delete(rec_id)
    pyplot.imshow(recon, cmap="Greys_r")
    pyplot.show()


cor = -44.5

# vec(cor)


def par(cor, slice_idx=1300):
    sino = sinos[slice_idx]
    vol_geom = astra.create_vol_geom(sinos.shape[0], sinos.shape[2])
    proj_geom = astra.create_proj_geom('parallel', 1.0, sino.shape[1], proj_angles)
    proj_id = astra.create_projector('cuda', proj_geom, vol_geom)
    sino_id = astra.data2d.create('-sino', proj_geom, sino)
    rec_id = astra.data2d.create('-vol', vol_geom)
    cfg = astra.astra_dict('FBP_CUDA')
    cfg['ReconstructionDataId'] = rec_id
    cfg['ProjectionDataId'] = sino_id
    cfg['FilterType'] = 'ram-lak'
    cfg['ProjectorId'] = proj_id
    alg_id = astra.algorithm.create(cfg)
    astra.algorithm.run(alg_id)
    recon = astra.data2d.get(rec_id)
    astra.data2d.delete(sino_id)
    astra.data2d.delete(rec_id)
    pyplot.imshow(recon, cmap="Greys_r")
    pyplot.show()
