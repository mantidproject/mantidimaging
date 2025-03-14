# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
import unittest

from parameterized import parameterized

from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase
from ..filenames import FilenameGroup, FilenamePattern, FilenamePatternGolden
from ...utility.data_containers import FILE_TYPES


class FilenamePatternTest(unittest.TestCase):

    @parameterized.expand([
        ("foo", "foo", 0, ""),
        ("foo.txt", "foo", 0, ".txt"),
        ("foo_0001.txt", "foo_", 4, ".txt"),
        # The 180 here is not an index
        ("IMAT00006388_PSI_cylinder_Sample_180deg.tif", "IMAT00006388_PSI_cylinder_Sample_180deg", 0, ".tif"),
        ("IMAT00006388_PSI_cylinder_Sample_000.tif", "IMAT00006388_PSI_cylinder_Sample_", 3, ".tif"),
        ("IMAT_Flower_Dark_Before_000000.tif", "IMAT_Flower_Dark_Before_", 6, ".tif"),
        ("IMAT_Flower_Dark_Before.json", "IMAT_Flower_Dark_Before", 0, ".json"),
        ("IMAT00024129_double_capillary_working_image_60C_wet gas_current holding_new_000.tif",
         "IMAT00024129_double_capillary_working_image_60C_wet gas_current holding_new_", 3, ".tif"),
        ("τομογραφία_01.tiff", "τομογραφία_", 2, ".tiff"),
        ("𓊨𓏏𓆇𓁐_0001.txt", "𓊨𓏏𓆇𓁐_", 4, ".txt"),
        ("📷_000.tif", "📷_", 3, ".tif"),
    ])
    def test_pattern_from_name(self, filename, prefix, count, suffix):
        p1 = FilenamePattern.from_name(filename)
        self.assertEqual(p1.prefix, prefix)
        self.assertEqual(p1.digit_count, count)
        self.assertEqual(p1.suffix, suffix)

    def test_pattern_generate(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertEqual(p1.generate(23), "IMAT_Flower_Tomo_000023.tif")
        self.assertEqual(p1.generate(0), "IMAT_Flower_Tomo_000000.tif")

    def test_pattern_match(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertTrue(p1.match("IMAT_Flower_Tomo_000023.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo_0000.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo.tif"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo.json"))
        self.assertFalse(p1.match("IMAT_Flower_Tomo_000007.tiff"))

    def test_pattern_dont_match_180(self):
        p1 = FilenamePattern.from_name("IMAT00006388_PSI_cylinder_Sample_000.tif")
        self.assertTrue(p1.match("IMAT00006388_PSI_cylinder_Sample_943.tif"))
        self.assertFalse(p1.match("IMAT00006388_PSI_cylinder_Sample_180deg.tif"))
        self.assertFalse(p1.match("IMAT00006388_PSI_cylinder_Sample_360deg.tif"))

    def test_pattern_match_different_digits(self):
        # Allow cases where index has grown above padding
        p1 = FilenamePattern.from_name("img_000.tif")
        self.assertTrue(p1.match("img_000.tif"))
        self.assertTrue(p1.match("img_001.tif"))
        self.assertTrue(p1.match("img_100.tif"))
        self.assertTrue(p1.match("img_999.tif"))
        self.assertTrue(p1.match("img_1000.tif"))
        self.assertFalse(p1.match("img_0000.tif"))

    def test_pattern_match_different_digits_no_zeros(self):
        # Allow cases where index has grown above padding
        p1 = FilenamePattern.from_name("img_1.tif")
        self.assertTrue(p1.match("img_10.tif"))
        self.assertTrue(p1.match("img_100.tif"))
        self.assertTrue(p1.match("img_101.tif"))
        self.assertTrue(p1.match("img_1234.tif"))
        self.assertFalse(p1.match("img_0000.tif"))

    def test_pattern_get_index(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        self.assertEqual(p1.get_index("IMAT_Flower_Tomo_000023.tif"), 23)
        self.assertRaises(ValueError, p1.get_index, "foo")
        self.assertRaises(ValueError, p1.get_index, "IMAT_Flower_Tomo_00002x.tif")

    def test_unindexed(self):
        p1 = FilenamePattern.from_name("IMAT00006388_PSI_cylinder_Sample_180deg.tif")
        self.assertEqual(p1.get_index("IMAT00006388_PSI_cylinder_Sample_180deg.tif"), 0)
        self.assertEqual(p1.generate(0), "IMAT00006388_PSI_cylinder_Sample_180deg.tif")

    def test_match_metadata(self):
        p1 = FilenamePattern.from_name("IMAT_Flower_Tomo_000000.tif")
        self.assertFalse(p1.match_metadata("IMAT_Flower_Tomo_000000.tif"))
        self.assertTrue(p1.match_metadata("IMAT_Flower_Tomo.json"))

        p2 = FilenamePattern.from_name("foo.tif")
        self.assertFalse(p2.match_metadata("foo.tif"))
        self.assertTrue(p2.match_metadata("foo.json"))


class FilenameGroupTest(FakeFSTestCase):

    def test_filenamepattern_from_file_unindexed(self):
        p1 = Path("foo", "bar", "baz.tiff")
        f1 = FilenameGroup.from_file(p1)
        self._files_equal(f1.directory, Path("foo", "bar"))

        all_files = list(f1.all_files())
        self._file_list_count_equal(all_files, [p1])

    def test_filenamepattern_from_file_indexed(self):
        p1 = Path("foo", "IMAT_Flower_Tomo_000007.tif")
        f1 = FilenameGroup.from_file(p1)

        all_files = list(f1.all_files())
        self._file_list_count_equal(all_files, [p1])

    def test_pattern_from_dir(self):
        test_dir = Path("/foo")

        for i in [9, 2, 1, 6, 8, 7, 0, 5, 3, 4]:
            self.fs.create_file(test_dir / f"bbb_{i:06d}.tif")
            self.fs.create_file(test_dir / f"ccc_{i:06d}.tif")
        self.fs.create_file(test_dir / "otherfile")
        self.fs.create_file(test_dir / "anotherfile")

        f1 = FilenameGroup.from_directory(test_dir)

        self._files_equal(f1.first_file(), "/foo/bbb_000000.tif")

    def test_pattern_from_dir_no_files(self):
        test_dir = Path("/foo")
        self.fs.create_dir(test_dir)
        f1 = FilenameGroup.from_directory(test_dir)
        self.assertIsNone(f1)

    def test_first_files(self):
        filename = "IMAT_Flower_Tomo_000001.tif"
        f1 = FilenameGroup.from_file(filename)

        self._files_equal(f1.first_file(), filename)

    def test_all_files(self):
        pattern = FilenamePattern.from_name("IMAT_Flower_Tomo_000007.tif")
        f1 = FilenameGroup(Path("foo"), pattern, [0, 1, 2])

        all_files = list(f1.all_files())
        self._files_equal(all_files[0], Path("foo", "IMAT_Flower_Tomo_000000.tif"))
        self._files_equal(all_files[1], Path("foo", "IMAT_Flower_Tomo_000001.tif"))
        self._files_equal(all_files[2], Path("foo", "IMAT_Flower_Tomo_000002.tif"))

    def test_find_all_files(self):
        file_list = [Path(f"IMAT_Flower_Tomo_{i:06d}.tif") for i in range(10)]
        for file_name in file_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file(file_list[7])
        fg.find_all_files()

        self.assertEqual(fg.all_indexes, list(range(10)))

    def test_find_all_files_different_digits(self):
        file_list = [Path(f"IMAT_Flower_Tomo_{i:01d}.tif") for i in range(5, 15)]
        for file_name in file_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file("IMAT_Flower_Tomo_1.tif")
        fg.find_all_files()

        self.assertEqual(fg.all_indexes, list(range(5, 15)))

    def test_find_all_files_metadata(self):
        file_list = [Path(f"IMAT_Flower_Tomo_{i:06d}.tif") for i in range(10)]
        file_list.append(Path("IMAT_Flower_Tomo.json"))
        for file_name in file_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file("IMAT_Flower_Tomo_000000.tif")
        fg.find_all_files()

        self._files_equal(fg.metadata_path, Path("IMAT_Flower_Tomo.json"))

    def test_find_log(self):
        log = Path("/foo", "tomo.txt")
        self.fs.create_file(log)

        sample = Path("/foo", "tomo", "IMAT_Flower_Tomo_000000.tif")
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_log_file()

        self._files_equal(fg.log_path, log)

    @parameterized.expand([
        ("/foo/tomo/IMAT_Flower_Tomo_000000.tif", "/foo/shuttercount.txt"),
        ("/foo/Flat_Before/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_Before_shuttercount.txt"),
        ("/foo/Flat_After/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_After_shuttercount.txt"),
    ])
    def test_find_shuttercount_log(self, sample_path, log_path):
        log = Path(log_path)
        self.fs.create_file(log)

        sample = Path(sample_path)
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_shutter_count_file()

        self._files_equal(fg.shutter_count_path.resolve(), log.resolve())

    def test_find_log_best(self):
        log = Path("/foo", "Dark_log.txt")
        self.fs.create_file(log)
        self.fs.create_file(Path("/foo", "Dark_aaa_log.txt"))
        self.fs.create_file(Path("/foo", "Dark_bbb_log.txt"))

        sample = Path("/foo", "Dark", "IMAT_Flower_Tomo_000000.tif")
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_log_file()

        self._files_equal(fg.log_path, log)

    def test_find_log_over_spectra_if_both(self):
        spectra = Path("/foo", "spectra.txt")
        self.fs.create_file(spectra)
        log = Path("/foo", "TomoIMAT_Flower_Tomo_000000_log.txt")
        self.fs.create_file(log)

        sample = Path("/foo", "Tomo", "IMAT_Flower_Tomo_000000.tif")
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_log_file()

        self._files_equal(fg.log_path, log)

    def test_find_spectra(self):
        spectra = Path("/foo", "sample_spectra.txt")
        self.fs.create_file(spectra)

        sample = Path("/foo", "Tomo", "IMAT_Flower_Tomo_000000.tif")
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_log_file()

        self._files_equal(fg.log_path, spectra)

    @parameterized.expand([
        ("/foo/Tomo/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_Before_ShutterCount.txt"),
        ("/foo/Tomo/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_After_ShutterCount.txt"),
    ])
    def test_find_shuttercount_no_flat_before_or_after(self, sample_path, log_path):
        log = Path(log_path)
        self.fs.create_file(log)

        sample = Path(sample_path)
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_shutter_count_file()

        self.assertIsNone(fg.shutter_count_path)

    @parameterized.expand([
        ("/foo/Flat_Before/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_Before_ShutterCount.txt"),
        ("/foo/Flat_After/IMAT_Flower_Tomo_000000.tif", "/foo/Flat_After_ShutterCount.txt"),
    ])
    def test_find_shuttercount_if_flat_before(self, sample_path, log_path):
        log = Path(log_path)
        self.fs.create_file(log)

        sample = Path(sample_path)
        self.fs.create_file(sample)

        fg = FilenameGroup.from_file(sample)
        fg.find_shutter_count_file()

        self._files_equal(fg.shutter_count_path, log)

    @parameterized.expand([
        ("/a/Tomo/foo_Tomo_%06d.tif", "/a/Flat_Before/foo_Flat_Before_%06d.tif"),
        ("/a/Tomo/foo_Tomo_%06d.tif", "/a/Flat/foo_Flat_%06d.tif"),
        ("/a/tomo/foo_tomo_%06d.tif", "/a/flat_before/foo_flat_before_%06d.tif"),
        ("/foo/Tomo/IMAT00026734_Tomo_CoinCell_7_Angled_PH40_Tomo_%03d.tif",
         "/foo/Flat_Before/IMAT00026732_Tomo_CoinCell_7_Angled_PH40_Flat_Before_%03d.tif"),
    ])
    def test_find_related(self, tomo_pattern, flat_pattern):
        tomo_list = [Path(tomo_pattern % i) for i in range(10)]
        flat_before_list = [Path(flat_pattern % i) for i in range(10)]
        for file_name in tomo_list + flat_before_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file(tomo_list[0])
        flat_before_fg = fg.find_related(FILE_TYPES.FLAT_BEFORE)

        self.assertIsNotNone(flat_before_fg)
        flat_before_fg.find_all_files()
        self._file_list_count_equal(flat_before_list, flat_before_fg.all_files())

    @parameterized.expand([
        ("/a/180deg/foo_180deg.tif"),
        ("/a/180deg/foo_180deg_000000.tif"),
    ])
    def test_find_related_proj_180(self, proj_name):
        tomo_list = [Path("/a/Tomo/foo_Tomo_%06d.tif" % i) for i in range(10)]
        proj_180_list = [Path(proj_name)]
        for file_name in tomo_list + proj_180_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file(tomo_list[0])
        proj_180_fg = fg.find_related(FILE_TYPES.PROJ_180)
        self.assertIsNotNone(proj_180_fg)
        proj_180_fg.find_all_files()

        self._file_list_count_equal(proj_180_list, list(proj_180_fg.all_files()))

    def test_find_related_dotfiles(self):
        tomo_list = [Path("/Tomo/IMAT00021865_CMOS_LegoScan_EquiDis_PH60_Tomo_%3d.tif" % i) for i in range(10)]
        flat_before_list = [
            Path("/Flat_After/IMAT00021866_CMOS_LegoScan_EquiDis_PH60_Flat_After_%3d.tif" % i) for i in range(10)
        ]
        flat_bad_list = [
            Path("/Flat_After/._IMAT00021866_CMOS_LegoScan_EquiDis_PH60_Flat_After_%3d.tif" % i) for i in range(10)
        ]
        for file_name in tomo_list + flat_before_list + flat_bad_list:
            self.fs.create_file(file_name)

        fg = FilenameGroup.from_file(tomo_list[0])
        flat_before_fg = fg.find_related(FILE_TYPES.FLAT_AFTER)

        self.assertIsNotNone(flat_before_fg)
        flat_before_fg.find_all_files()
        self._files_equal(flat_before_list[0], flat_before_fg.first_file())
        self._file_list_count_equal(flat_before_list, flat_before_fg.all_files())


class GoldenFilenameGroupTest(FakeFSTestCase):

    def test_golden_pattern(self):
        filename = "IMAT00021870_CMOS_LegoScan_GR_PH40_GRtomo_0.0_001.tif"
        group = FilenameGroup.from_file(filename)

        self.assertTrue(isinstance(group.pattern, FilenamePatternGolden))
        self.assertEqual([1], group.all_indexes)

    def test_all_files(self):
        angles = [0.0, 111.2461, 42.4922, 153.7384, 16.2306]
        basename = "IMAT00021870_CMOS_LegoScan_GR_PH40_GRtomo_{}_{:03d}.tif"
        filenames = [basename.format(a, n) for n, a in enumerate(angles)]

        for filename in filenames:
            self.fs.create_file(filename)

        group = FilenameGroup.from_file(filenames[0])
        group.find_all_files()

        self._file_list_count_equal(filenames, group.all_files())
