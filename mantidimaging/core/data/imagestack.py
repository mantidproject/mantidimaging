# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import datetime
import json
import uuid
from copy import deepcopy
from typing import Any, TextIO, TYPE_CHECKING, cast
import logging
from pathlib import Path

import numpy as np

from mantidimaging.core.data.geometry import Geometry, GeometryType
from mantidimaging.core.data.utility import mark_cropped
from mantidimaging.core.operation_history import const
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.data_containers import ProjectionAngles, Counts, Indices
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.core.utility.leak_tracker import leak_tracker

if TYPE_CHECKING:
    from mantidimaging.core.io.instrument_log import InstrumentLog, ShutterCount
    import numpy.typing as npt

LOG = logging.getLogger(__name__)


class StackNotFoundError(RuntimeError):

    def __init__(self, message: str, log_level: int = logging.ERROR):
        super().__init__(message)
        logging.log(log_level, message)


class ImageStack:
    name: str
    geometry: Geometry | None = None
    _shared_array: pu.SharedArray

    def __init__(self,
                 data: np.ndarray | pu.SharedArray,
                 filenames: list[Path] | None = None,
                 indices: list[int] | Indices | None = None,
                 metadata: dict[str, Any] | None = None,
                 sinograms: bool = False,
                 name: str | None = None):
        """
        :param data: a numpy array or SharedArray object containing the images of the Sample/Projection data
        :param filenames: All filenames that were matched for loading
        :param indices: Indices that were actually loaded
        :param metadata: Properties to copy when creating a new stack from an existing one
        :param sinograms: Set data ordering, if false: [t,y,x] if true: [y,t,x]
        :param name: A name for the stack
        """

        if isinstance(data, pu.SharedArray):
            self._shared_array = data
        else:
            self._shared_array = pu.SharedArray(data, None)

        self.indices = indices
        self._id = uuid.uuid4()

        self._filenames = filenames

        self.metadata: dict[str, Any] = deepcopy(metadata) if metadata else {}
        self._is_sinograms = sinograms

        self._proj180deg: ImageStack | None = None
        self._log_file: InstrumentLog | None = None
        self._shutter_count_file: ShutterCount | None = None
        self._projection_angles: ProjectionAngles | None = None

        if name is None:
            self.name = str(filenames[0].stem) if filenames else "untitled"
        else:
            self.name = name

        tracker_msg: str = f"ImageStack {self.name}"
        leak_tracker.add(self._shared_array.array, msg=tracker_msg)
        leak_tracker.add(self._shared_array, msg=tracker_msg)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ImageStack):
            return np.array_equal(self.data, other.data) \
                   and self.is_sinograms == other.is_sinograms \
                   and self.metadata == other.metadata \
                   and self.indices == other.indices
        elif isinstance(other, np.ndarray):
            return np.array_equal(self.data, other)
        else:
            raise ValueError(f"Cannot compare against {other}")

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __str__(self) -> str:
        return f'Image Stack: data={self.data.shape} | properties|={len(self.metadata)}'

    def count(self) -> int:
        return len(self._filenames) if self._filenames else 0

    @property
    def filenames(self) -> list[Path] | None:
        return self._filenames

    @filenames.setter
    def filenames(self, new_ones: list[Path]) -> None:
        assert len(new_ones) == self.data.shape[0], "Number of filenames and number of images must match."
        self._filenames = new_ones

    @property
    def id(self) -> uuid.UUID:
        return self._id

    def load_metadata(self, f: TextIO) -> None:
        """
        Load metadata json without overwriting existing values
        """
        self.metadata = json.load(f) | self.metadata
        self._is_sinograms = self.metadata.get(const.SINOGRAMS, False)

    def save_metadata(self, f: TextIO, rescale_params: dict[str, str | float] | None = None) -> None:
        self.metadata[const.SINOGRAMS] = self.is_sinograms

        if rescale_params is not None:
            self.metadata[const.RESCALED] = rescale_params

        json.dump(self.metadata, f, indent=4)

    def record_operation(self, func_name: str, display_name: str, *args, **kwargs) -> None:
        if const.OPERATION_HISTORY not in self.metadata:
            self.metadata[const.OPERATION_HISTORY] = []

        def accepted_type(o) -> bool:
            return any(isinstance(o, expected) for expected in [str, int, float, bool, tuple, list, SensibleROI])

        def prepare(o) -> Any:
            if isinstance(o, SensibleROI):
                return list(o)
            else:
                return o

        self.metadata[const.OPERATION_HISTORY].append({
            const.TIMESTAMP: datetime.datetime.now().isoformat(),
            const.OPERATION_NAME: func_name,
            const.OPERATION_KEYWORD_ARGS: {
                k: prepare(v)
                for k, v in kwargs.items() if accepted_type(v)
            },
            const.OPERATION_DISPLAY_NAME: display_name
        })

    @property
    def is_processed(self) -> bool:
        """
        :return: True if any of the data has been processed, False otherwise.
        """
        return const.OPERATION_HISTORY in self.metadata

    def copy(self, flip_axes: bool = False) -> ImageStack:
        shape = (self.data.shape[1], self.data.shape[0], self.data.shape[2]) if flip_axes else self.data.shape
        data_copy = pu.create_array(shape, self.data.dtype)
        if flip_axes:
            data_copy.array[:] = np.swapaxes(self.data, 0, 1)
        else:
            data_copy.array[:] = self.data[:]

        images = ImageStack(data_copy,
                            indices=deepcopy(self.indices),
                            metadata=deepcopy(self.metadata),
                            sinograms=not self.is_sinograms if flip_axes else self.is_sinograms)
        return images

    def copy_roi(self, roi: SensibleROI) -> ImageStack:
        shape = (self.data.shape[0], roi.height, roi.width)

        data_copy = pu.create_array(shape, self.data.dtype)
        data_copy.array[:] = self.data[:, roi.top:roi.bottom, roi.left:roi.right]

        images = ImageStack(data_copy,
                            indices=deepcopy(self.indices),
                            metadata=deepcopy(self.metadata),
                            sinograms=self._is_sinograms)

        mark_cropped(images, roi)
        return images

    def slice_as_image_stack(self, index: int) -> ImageStack:
        "A slice, either projection or sinogram depending on current ordering"
        return ImageStack(self.slice_as_array(index), metadata=deepcopy(self.metadata), sinograms=self.is_sinograms)

    def sino_as_image_stack(self, index: int) -> ImageStack:
        "A single sinogram slice as an ImageStack in projection ordering"
        return ImageStack(np.asarray([self.sino(index)]).swapaxes(0, 1), metadata=deepcopy(self.metadata))

    def slice_as_array(self, index: int) -> np.ndarray:
        return np.asarray([self.data[index]])

    @property
    def height(self) -> int:
        if not self._is_sinograms:
            return self.data.shape[1]
        else:
            return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[2]

    @property
    def h_middle(self) -> float:
        """
        Returns the horizontal middle (middle column) of the projections
        """
        return self.width / 2

    @property
    def num_images(self) -> int:
        return self.data.shape[0]

    @property
    def num_projections(self) -> int:
        if not self._is_sinograms:
            return self.data.shape[0]
        else:
            return self.data.shape[1]

    @property
    def num_sinograms(self) -> int:
        return self.height

    def sino(self, slice_idx: int) -> np.ndarray:
        if not self._is_sinograms:
            return np.swapaxes(self.data, 0, 1)[slice_idx]
        else:
            return self.data[slice_idx]

    def projection(self, projection_idx: int) -> np.ndarray:
        if self._is_sinograms:
            return np.swapaxes(self.data, 0, 1)[projection_idx]
        else:
            return self.data[projection_idx]

    def proj_180_degree_shape_matches_images(self) -> bool:
        if self.proj180deg is not None:
            return self.has_proj180deg(
            ) and self.height == self.proj180deg.height and self.width == self.proj180deg.width
        else:
            return False

    def has_proj180deg(self) -> bool:
        return self._proj180deg is not None

    @property
    def proj180deg(self) -> ImageStack | None:
        return self._proj180deg

    @proj180deg.setter
    def proj180deg(self, value: ImageStack | None) -> None:
        self._proj180deg = value

    @property
    def projections(self) -> np.ndarray:
        return self.data if not self._is_sinograms else np.swapaxes(self.data, 0, 1)

    @property
    def sinograms(self) -> np.ndarray:
        return self.data if self._is_sinograms else np.swapaxes(self.data, 0, 1)

    @property
    def data(self) -> np.ndarray:
        return self._shared_array.array

    @data.setter
    def data(self, value: np.ndarray) -> None:
        """
        Set data array and update geometry data

        :param value: new numpy array containing image data.
        """
        if isinstance(value, pu.SharedArray):
            self._shared_array = value
        else:
            self._shared_array = pu.copy_into_shared_memory(value)
        self.set_geometry_panels()

    @property
    def shared_array(self) -> pu.SharedArray:
        return self._shared_array

    @shared_array.setter
    def shared_array(self, shared_array: pu.SharedArray) -> None:
        self._shared_array = shared_array
        self.set_geometry_panels()

    @property
    def uses_shared_memory(self) -> bool:
        return self._shared_array.has_shared_memory

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    @staticmethod
    def create_empty_image_stack(shape: tuple[int, ...], dtype: npt.DTypeLike, metadata: dict[str, Any]) -> ImageStack:
        arr = pu.create_array(shape, dtype)
        return ImageStack(arr, metadata=metadata)

    @property
    def is_sinograms(self) -> bool:
        return self._is_sinograms

    @property
    def log_file(self) -> InstrumentLog | None:
        return self._log_file

    @log_file.setter
    def log_file(self, value: InstrumentLog | None) -> None:
        if value is not None:
            self.metadata[const.LOG_FILE] = str(value.source_file)
        elif value is None:
            del self.metadata[const.LOG_FILE]
        self._log_file = value

    @property
    def shutter_count_file(self) -> ShutterCount | None:
        return self._shutter_count_file

    @shutter_count_file.setter
    def shutter_count_file(self, value: ShutterCount | None) -> None:
        if value is not None:
            self.metadata[const.SHUTTER_COUNT_FILE] = str(value.source_file)
        elif value is None:
            del self.metadata[const.SHUTTER_COUNT_FILE]
        self._shutter_count_file = value

    def set_projection_angles(self, angles: ProjectionAngles) -> None:
        """
        Assigns a set of projection angles to the image stack and updates the associated geometry.

        This method validates that the number of provided angles matches the number of images in the stack.
        If the geometry object is present, it updates its angles accordingly.

        :param angles: An object containing the projection angles to assign, in radians.
        :raises RuntimeError: If the number of angles does not match the number of images in the stack.
        :side effects: Updates the internal projection angles and, if available, updates the geometry's angles.
        """

        if len(angles.value) != self.num_images:
            raise RuntimeError("The number of angles does not match the number of images. "
                               f"Num angles {len(angles.value)} and num images {self.num_images}")

        self._projection_angles = angles

        if self.geometry:
            self.geometry.set_angles(angles=angles.value, angle_unit="radian")

    def real_projection_angles(self) -> ProjectionAngles | None:
        """
        Return projection angles from actual data sources (log files or manually loaded files).

        This method returns angles that were either:
          - Explicitly set via projection_angles setter
          - Read from a log file during data loading

        :return: Real projection angles if they were found, None otherwise.
        """
        if self._projection_angles is not None:
            return self._projection_angles

        if self._log_file is not None and self._log_file.has_projection_angles():
            return self._log_file.projection_angles()

        return None

    def projection_angles(self, max_angle: float = 360.0) -> ProjectionAngles:
        """
        Return projection angles, in priority order:
        - From a log
        - From the manually loaded file with a list of angles
        - Automatically generated with equidistant step

        :param max_angle: The maximum angle up to which the angles will be generated.
                          Only used when the angles are generated, if they are provided
                          via a log or a file the argument will be ignored.
        """
        projection_angles = self.real_projection_angles()
        if projection_angles is not None:
            return projection_angles
        else:
            return ProjectionAngles(np.linspace(0, np.deg2rad(max_angle), self.num_projections))

    def counts(self) -> Counts | None:
        if self._log_file is not None:
            return self._log_file.counts()
        else:
            return None

    @property
    def pixel_size(self) -> float:
        pixel_size = cast(float, self.metadata.get(const.PIXEL_SIZE, 0))
        return pixel_size

    @pixel_size.setter
    def pixel_size(self, value: float) -> None:
        self.metadata[const.PIXEL_SIZE] = value

    def make_name_unique(self, existing_names: list[str]) -> None:
        name = self.name
        num = 1
        while self.name in existing_names:
            num += 1
            self.name = f"{name}_{num}"

            if num > 1000:
                raise ValueError(f"Could not make unique name for: {name}")

    def create_geometry(self, geom_type: GeometryType = GeometryType.PARALLEL3D) -> None:
        """
        Creates an AcquisitionGeometry belonging to the ImageStack.
        """
        self.geometry = Geometry(type=geom_type, num_pixels=(self.width, self.height), pixel_size=(1., 1.))
        self.set_geometry_angles()
        self.set_geometry_panels()

    def set_geometry_panels(self) -> None:
        """
        Updates the geometry's panel data based on its parent ImageStack's array data if both geometry
        and array data are present.

        Set the number of pixels and the pixel size for the geometry panel based on the
        current width and height of the image stack.

        :side effects: Modifies self.geometry by updating its panel configuration.
        """
        if not self.geometry or not self._shared_array:
            LOG.warning(f"Cannot update geometry panels:"
                        f"geometry is {self.geometry}, shared_array is {self._shared_array}")
            return

        num_pixels = (self.width, self.height)
        pixel_size = (1.0, 1.0)
        self.geometry.set_panel(num_pixels=num_pixels, pixel_size=pixel_size)

    def set_geometry_angles(self) -> None:
        """
        Updates the geometry's angle data based on its parent ImageStack's projection angles if both geometry
        and projection angles are present.

        :side effects: Modifies self.geometry by updating its angle configuration.
        """
        if not self.geometry or not self._projection_angles:
            LOG.warning(f"Cannot update geometry angles:"
                        f"geometry is {self.geometry}, projection angles is {self._projection_angles}")
            return

        self.geometry.set_angles(angles=self._projection_angles.value, angle_unit="radian")
