# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import datetime
import pathlib
import unittest
from pathlib import Path
from unittest import mock

import h5py
import numpy as np
import numpy.testing as npt

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.utility import NEXUS_PROCESSED_DATA_PATH
from mantidimaging.core.operation_history.const import TIMESTAMP

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader
from mantidimaging.core.io import saver
from mantidimaging.core.io.saver import _rescale_recon_data, _save_recon_to_nexus, _save_processed_data_to_nexus, \
    _save_image_stacks_to_nexus, _convert_float_to_int
from mantidimaging.core.utility.version_check import CheckVersion
from mantidimaging.test_helpers import FileOutputtingTestCase

NX_CLASS = "NX_class"


def _decode_nexus_class(nexus_data) -> str:
    return nexus_data.attrs[NX_CLASS].decode("utf-8")


def _nexus_dataset_to_string(nexus_dataset) -> str:
    return np.array(nexus_dataset).tobytes().decode("utf-8")


def _create_sample_with_filename() -> ImageStack:
    sample = th.generate_images()
    sample.filenames = [Path(f"image{i}.tiff") for i in range(sample.data.shape[0])]
    return sample


def test_rescale_negative_recon_data():
    recon = th.generate_images()
    recon.data -= np.min(recon.data) * 1.2

    assert np.min(_rescale_recon_data(recon.data)) >= 0
    assert int(np.max(_rescale_recon_data(recon.data))) == np.iinfo("uint16").max


class IOTest(FileOutputtingTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sample_path = "sample/file/path.tiff"

    def assert_files_exist(self, base_name, file_format, stack=True, num_images=1, indices=None):
        if not stack:
            if not indices:
                indices = [0, num_images, 1]
            filenames = saver.generate_names(base_name, indices, num_images, out_format=file_format)
            for f in filenames:
                self.assertTrue(Path(f).is_file(), f"File does not exist: {f}")
        else:
            filename = Path(f"{base_name}.{file_format}")
            self.assertTrue(filename.is_file(), f"File does not exist: {filename}")

    # fits sequential
    def test_preproc_fits_seq(self):
        self.do_preproc('fits')

    # fits sequential loader indices
    def test_preproc_fits_seq_loader_indices_4_5(self):
        self.do_preproc('fits', loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_fits_seq_loader_indices_0_7(self):
        self.do_preproc('fits', loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_fits_seq_loader_indices_3_9(self):
        self.do_preproc('fits', loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_fits_seq_loader_indices_5_9(self):
        self.do_preproc('fits', loader_indices=[5, 9, 1], expected_len=4)

    # fits sequential saver indices
    def test_preproc_fits_seq_saver_indices_0_5(self):
        self.do_preproc('fits', saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_fits_seq_saver_indices_0_2(self):
        self.do_preproc('fits', saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_fits_seq_saver_indices_3_10(self):
        self.do_preproc('fits', saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_fits_seq_saver_indices_7_10(self):
        self.do_preproc('fits', saver_indices=[7, 10, 1], expected_len=3)

    # tiff sequential
    def test_preproc_tiff_seq(self):
        self.do_preproc('tiff')

    # tiff sequential loader indices
    def test_preproc_tiff_seq_loader_indices_4_5(self):
        self.do_preproc('tiff', loader_indices=[4, 5, 1], expected_len=1)

    def test_preproc_tiff_seq_loader_indices_0_7(self):
        self.do_preproc('tiff', loader_indices=[0, 7, 1], expected_len=7)

    def test_preproc_tiff_seq_loader_indices_3_9(self):
        self.do_preproc('tiff', loader_indices=[3, 9, 1], expected_len=6)

    def test_preproc_tiff_seq_loader_indices_5_9(self):
        self.do_preproc('tiff', loader_indices=[5, 9, 1], expected_len=4)

    # tiff sequential saver indices
    def test_preproc_tiff_seq_saver_indices_0_5(self):
        self.do_preproc('tiff', saver_indices=[0, 5, 1], expected_len=5)

    def test_preproc_tiff_seq_saver_indices_0_2(self):
        self.do_preproc('tiff', saver_indices=[0, 2, 1], expected_len=2)

    def test_preproc_tiff_seq_saver_indices_3_10(self):
        self.do_preproc('tiff', saver_indices=[3, 10, 1], expected_len=7)

    def test_preproc_tiff_seq_saver_indices_7_10(self):
        self.do_preproc('tiff', saver_indices=[7, 10, 1], expected_len=3)

    def do_preproc(self, img_format, loader_indices=None, expected_len=None, saver_indices=None, data_as_stack=False):
        expected_images = th.generate_images()
        if saver_indices:
            # Slice only the required range for expected output
            expected_images.data = expected_images.data[saver_indices[0]:saver_indices[1]]
        # Save the images
        saver.image_save(expected_images, self.output_directory, out_format=img_format, indices=saver_indices)
        # Assert the expected files exist
        base_name = Path(self.output_directory) / saver.DEFAULT_NAME_PREFIX
        self.assert_files_exist(base_name, img_format, data_as_stack, expected_images.data.shape[0], saver_indices)

        # Load the saved file group
        filename = f"{saver.DEFAULT_NAME_PREFIX}_000000.{img_format}"
        group = FilenameGroup.from_file(Path(self.output_directory) / filename)
        group.find_all_files()
        loaded_images = loader.load(group, indices=loader_indices)

        # Validate shape if loader_indices provided
        if loader_indices:
            self.assertEqual(expected_len, len(loaded_images.data))
            expected_images.data = expected_images.data[loader_indices[0]:loader_indices[1]]
        npt.assert_equal(loaded_images.data, expected_images.data)

    def test_load_sample(self):
        img_format = 'tiff'
        images = th.generate_images()

        saver.image_save(images, self.output_directory, out_format=img_format)
        data_as_stack = False
        base_name = Path(self.output_directory) / saver.DEFAULT_NAME_PREFIX
        self.assert_files_exist(base_name, img_format, data_as_stack, images.data.shape[0])

        filename = f"{saver.DEFAULT_NAME_PREFIX}_000000.tiff"
        group = FilenameGroup.from_file(Path(self.output_directory) / filename)
        group.find_all_files()

        loaded_images = loader.load(group)
        npt.assert_equal(loaded_images.data, images.data)

    def test_metadata_round_trip(self):
        # Create dummy image stack
        sample = th.gen_img_numpy_rand()
        images = ImageStack(sample)
        images.metadata['message'] = 'hello, world!'

        # Save image stack
        saver.image_save(images, self.output_directory)

        # Load image stack back
        filename = saver.DEFAULT_NAME_PREFIX + "_000000.tif"
        group = FilenameGroup.from_file(Path(self.output_directory) / filename)
        group.find_all_files()
        loaded_images = loader.load(group)

        # Ensure properties have been preserved
        self.assertEqual(loaded_images.metadata, images.metadata)

    def test_nexus_simple_dataset_save(self):
        sample = th.generate_images()
        sample.data *= 12
        sample._projection_angles = sample.projection_angles()

        sd = Dataset(sample=sample)
        sd.sample.record_operation("", "")

        path = "nexus/file/path"
        sample_name = "sample-name"

        with h5py.File(path, "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, sample_name, True)

            # test entry field
            self.assertEqual(_decode_nexus_class(nexus_file["entry1"]), "NXentry")
            self.assertEqual(_decode_nexus_class(nexus_file["entry1"]["tomo_entry"]), "NXsubentry")

            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            # test definition field
            self.assertEqual(_nexus_dataset_to_string(tomo_entry["definition"]), "NXtomo")

            # test instrument field
            self.assertEqual(_decode_nexus_class(tomo_entry["instrument"]), "NXinstrument")

            # test instrument/detector fields
            self.assertEqual(_decode_nexus_class(tomo_entry["instrument"]["detector"]), "NXdetector")
            npt.assert_array_equal(np.array(nexus_file[NEXUS_PROCESSED_DATA_PATH]["data"]),
                                   sd.sample.data.astype("float32"))
            npt.assert_array_equal(np.array(tomo_entry["instrument"]["detector"]["image_key"]),
                                   [0 for _ in range(sd.sample.data.shape[0])])

            # test instrument/sample fields
            self.assertEqual(_decode_nexus_class(tomo_entry["sample"]), "NXsample")
            self.assertEqual(_nexus_dataset_to_string(tomo_entry["sample"]["name"]), sample_name)
            npt.assert_array_equal(np.array(tomo_entry["sample"]["rotation_angle"]),
                                   sd.sample.projection_angles().value)

            # test links
            self.assertEqual(tomo_entry["data"]["rotation_angle"], tomo_entry["sample"]["rotation_angle"])
            self.assertEqual(tomo_entry["data"]["image_key"], tomo_entry["instrument"]["detector"]["image_key"])

    def test_nexus_missing_projection_angles_save_as_zeros(self):
        shape = (10, 8, 10)
        sample = th.generate_images(shape)
        flat_before = th.generate_images(shape)
        flat_before._projection_angles = flat_before.projection_angles()

        sd = Dataset(sample=sample, flat_before=flat_before)
        path = "nexus/file/path"
        sample_name = "sample-name"

        with h5py.File(path, "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, sample_name, True)
            tomo_entry = nexus_file["entry1"]["tomo_entry"]
            rotation_angle_entry = tomo_entry["sample"]["rotation_angle"]

            # test rotation angle fields
            expected = np.concatenate([flat_before.projection_angles().value, np.zeros(shape[0])])
            npt.assert_array_equal(expected, np.array(rotation_angle_entry))

            # test rotation angle links
            self.assertEqual(tomo_entry["data"]["rotation_angle"], rotation_angle_entry)

    def test_nexus_complex_processed_dataset_save(self):
        image_stacks = []
        for _ in range(5):
            image_stack = th.generate_images()
            image_stack.data *= 12
            image_stacks.append(image_stack)
            image_stack._projection_angles = image_stack.projection_angles()

        sd = Dataset(sample=image_stacks[0],
                     flat_before=image_stacks[1],
                     flat_after=image_stacks[2],
                     dark_before=image_stacks[3],
                     dark_after=image_stacks[4])
        sd.sample.record_operation("", "")

        with h5py.File("nexus/file/path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)
            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            npt.assert_array_equal(
                np.array(nexus_file[NEXUS_PROCESSED_DATA_PATH]["data"]),
                np.concatenate(
                    [sd.dark_before.data, sd.flat_before.data, sd.sample.data, sd.flat_after.data,
                     sd.dark_after.data]).astype("float32"))
            # test instrument field
            npt.assert_array_equal(
                np.array(tomo_entry["instrument"]["detector"]["image_key"]),
                [2 for _ in range(sd.dark_before.data.shape[0])] + [1 for _ in range(sd.flat_before.data.shape[0])] +
                [0 for _ in range(sd.sample.data.shape[0])] + [1 for _ in range(sd.flat_after.data.shape[0])] +
                [2 for _ in range(sd.dark_after.data.shape[0])])

            # test instrument/sample fields
            npt.assert_array_equal(np.array(tomo_entry["sample"]["rotation_angle"]),
                                   np.concatenate([images.projection_angles().value for images in image_stacks]))
            self.assertEqual(nexus_file[NEXUS_PROCESSED_DATA_PATH]["rotation_angle"],
                             tomo_entry["sample"]["rotation_angle"])
            self.assertEqual(nexus_file[NEXUS_PROCESSED_DATA_PATH]["image_key"],
                             tomo_entry["instrument"]["detector"]["image_key"])

    def test_nexus_unprocessed_dataset_save(self):
        image_stacks = []
        for _ in range(5):
            image_stack = th.generate_images()
            image_stack.data *= 12
            image_stacks.append(image_stack)
            image_stack._projection_angles = image_stack.projection_angles()

        sd = Dataset(sample=image_stacks[0],
                     flat_before=image_stacks[1],
                     flat_after=image_stacks[2],
                     dark_before=image_stacks[3],
                     dark_after=image_stacks[4])

        with h5py.File("nexus/file/path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)
            tomo_entry = nexus_file["entry1"]["tomo_entry"]

            npt.assert_array_equal(
                np.array(tomo_entry["instrument"]["detector"]["data"]),
                np.concatenate(
                    [sd.dark_before.data, sd.flat_before.data, sd.sample.data, sd.flat_after.data,
                     sd.dark_after.data]).astype("float32"))

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    def test_h5py_os_error_returns(self, nexus_save_mock, file_mock):
        file_mock.side_effect = OSError
        with self.assertRaises(RuntimeError):
            saver.nexus_save(Dataset(sample=th.generate_images()), Path("path"), "sample-name", True)
        nexus_save_mock.assert_not_called()

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    @mock.patch("pathlib.Path.unlink")
    def test_failed_nexus_save_deletes_file(self, unlink_mock, nexus_save_mock, file_mock):
        nexus_save_mock.side_effect = OSError
        save_path = pathlib.Path("failed/save/path")
        with self.assertRaises(RuntimeError):
            saver.nexus_save(Dataset(sample=th.generate_images()), save_path, "sample-name", True)
        file_mock.return_value.close.assert_called_once()
        unlink_mock.assert_called_once_with(missing_ok=True)

    @mock.patch("mantidimaging.core.io.saver.h5py.File")
    @mock.patch("mantidimaging.core.io.saver._nexus_save")
    def test_successful_nexus_save_closes_file(self, nexus_save_mock: mock.Mock, file_mock: mock.Mock):
        saver.nexus_save(Dataset(sample=th.generate_images()), Path("path"), "sample-name", True)
        file_mock.return_value.close.assert_called_once()
        nexus_save_mock.assert_called_once()

    @mock.patch("mantidimaging.core.io.saver._save_recon_to_nexus")
    def test_save_recons_if_present(self, recon_save_mock: mock.Mock):
        sample = _create_sample_with_filename()
        sample._projection_angles = sample.projection_angles()

        sd = Dataset(sample=sample)
        sd.recons.data = [th.generate_images(), th.generate_images()]

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)

        self.assertEqual(recon_save_mock.call_count, len(sd.recons))

    def test_save_process(self):
        ds = Dataset(sample=th.generate_images())
        process_path = "processed-data/process"
        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            rotation_angle = nexus_file.create_dataset("rotation_angle", dtype="float")
            image_key = nexus_file.create_dataset("image_key", dtype="int")
            _save_processed_data_to_nexus(nexus_file, ds, rotation_angle, image_key, True)
            assert "process" in nexus_file[NEXUS_PROCESSED_DATA_PATH]
            self.assertEqual(_decode_nexus_class(nexus_file[NEXUS_PROCESSED_DATA_PATH]), "NXdata")
            self.assertEqual(_decode_nexus_class(nexus_file[process_path]), "NXprocess")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[process_path]["program"]), "Mantid Imaging")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[process_path]["version"]),
                             CheckVersion().get_version())
            self.assertIn(str(datetime.date.today()), _nexus_dataset_to_string(nexus_file[process_path]["date"]))

    @mock.patch("mantidimaging.core.io.saver._save_recon_to_nexus")
    def test_dont_save_recons_if_none_present(self, recon_save_mock: mock.Mock):

        sample = th.generate_images()
        sample._projection_angles = sample.projection_angles()

        sd = Dataset(sample=sample)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)

        recon_save_mock.assert_not_called()

    def test_save_recon_to_nexus(self):

        sample = _create_sample_with_filename()
        sample._projection_angles = sample.projection_angles()

        sd = Dataset(sample=sample)

        recon = th.generate_images(seed=2)
        recon.metadata[TIMESTAMP] = None
        recon.name = recon_name = "Recon"
        sd.recons.append(recon)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]), "NXentry")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["title"]), recon_name)
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["definition"]), "NXtomoproc")

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["INSTRUMENT"]), "NXinstrument")
            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]), "NXsource")

            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["type"]),
                             "Neutron source")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["name"]), "ISIS")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["INSTRUMENT"]["SOURCE"]["probe"]),
                             "neutron")

            self.assertEqual(_decode_nexus_class(nexus_file[recon_name]["SAMPLE"]), "NXsample")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["SAMPLE"]["name"]), recon_name)

            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["program"]),
                             "Mantid Imaging")
            self.assertEqual(_nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["version"]),
                             CheckVersion().get_version())
            self.assertIn(str(datetime.date.today()),
                          _nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["date"]))

            npt.assert_allclose(np.array(nexus_file[recon_name]["data"]["data"]), recon.data, rtol=1e-3)

    def test_use_recon_date_from_image_stack(self):
        sample = _create_sample_with_filename()
        sample._projection_angles = sample.projection_angles()

        sd = Dataset(sample=sample)

        recon = th.generate_images(seed=2)
        recon.name = recon_name = "Recon"
        gemini = "2022-06-18"
        recon.metadata[TIMESTAMP] = datetime.date.fromisoformat(gemini)
        sd.recons.append(recon)

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            saver._nexus_save(nexus_file, sd, "sample-name", True)
            self.assertIn(str(datetime.date.fromisoformat(gemini)),
                          _nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["date"]))

    def test_save_recon_xyz_data(self):
        recon = th.generate_images()
        recon.name = recon_name = "Recon"
        recon.pixel_size = pixel_size = 3

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            _save_recon_to_nexus(nexus_file, recon, self.sample_path)
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["x"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[0])]))
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["y"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[1])]))
            npt.assert_array_equal(np.array(nexus_file[recon_name]["data"]["z"]),
                                   np.array([pixel_size * i for i in range(recon.data.shape[2])]))

    def test_raw_file_field(self):
        recon = th.generate_images()
        recon.name = recon_name = "Recon"

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            _save_recon_to_nexus(nexus_file, recon, self.sample_path)
            self.assertEqual(
                _nexus_dataset_to_string(nexus_file[recon_name]["reconstruction"]["parameters"]["raw_file"]),
                self.sample_path)

    def test_save_image_stacks_to_nexus_as_int(self):
        ds = Dataset(sample=th.generate_images())

        with h5py.File("path", "w", driver="core", backing_store=False) as nexus_file:
            data = nexus_file.create_group("data")
            _save_image_stacks_to_nexus(ds, data, False)
            self.assertEqual(data["data"].dtype, "int16")

    def test_convert_float_to_int(self):
        n_arrs = 3
        float_arr = [th.gen_img_numpy_rand() for _ in range(3)]
        conv, factors = _convert_float_to_int(float_arr)

        for i in range(n_arrs):
            close_arr = np.isclose(conv[i] / factors[i], float_arr[i], rtol=1e-5)
            self.assertTrue(np.count_nonzero(close_arr) >= len(close_arr) * 0.75)

    def test_create_rits_format(self):
        tof = np.array([1, 2, 3])
        transmission = np.array([4, 5, 6])
        absorption = np.array([7, 8, 9])
        rits_formatted_data = saver.create_rits_format(tof, transmission, absorption)
        expected = '1\t4\t7\n2\t5\t8\n3\t6\t9'
        self.assertEqual(rits_formatted_data, expected)


if __name__ == '__main__':
    unittest.main()
