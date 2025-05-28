# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import argparse
import csv
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from statistics import stdev
from collections.abc import Callable

import numpy as np
import pandas as pd

try:
    from plotly import graph_objs as go
    from plotly.subplots import make_subplots
except ModuleNotFoundError:
    print("Approval tests require plotly")
    print("Try: mamba install plotly")
    exit(1)

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from mantidimaging.core.io.filenames import FilenameGroup  # noqa: E402
from mantidimaging.core.io.loader import loader  # noqa: E402
from mantidimaging.core.operations.loader import load_filter_packages  # noqa: E402
from mantidimaging.core.io.instrument_log import InstrumentLog, ShutterCount
from mantidimaging.core.utility.data_containers import FILE_TYPES

script_dir = Path(__file__).resolve().parent
log_directory = script_dir / "logs"
os.makedirs(log_directory, exist_ok=True)
log_file_name = f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_file_path = log_directory / log_file_name

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_file_path, mode='a'),
                              logging.StreamHandler()])

console_logger = logging.getLogger()
console_logger.handlers[1].setLevel(logging.ERROR)


class ConfigManager:

    def __init__(self):
        self._base_data_dir = Path.home() / "mantidimaging-data"
        print(f"{self._base_data_dir=}")

    @cached_property
    def save_dir(self):
        dir_path = Path(os.getenv("MANTIDIMAGING_APPROVAL_TESTS_DIR", self._base_data_dir / "approval_tests"))
        if not dir_path.exists():
            print(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @cached_property
    def load_sample(self):
        return self._base_data_dir / "ISIS" / "IMAT" / "IMAT00010675" / "Tomo" / "IMAT_Flower_Tomo_000000.tif"


config_manager = ConfigManager()

FILTERS = {f.filter_name: f for f in load_filter_packages()}
TEST_CASE_RESULTS: list[TestCase] = []
GIT_TOKEN = subprocess.check_output(["git", "describe"], encoding="utf_8").strip()
COMMIT_DATE = subprocess.check_output(["git", "log", "--pretty=format:%ai", "-n1"], encoding="utf_8").strip()

with open(Path(__file__).resolve().parent / "test_cases.json", encoding="UTF-8") as f:
    TEST_CASES = json.load(f)


@dataclass
class TestCase:
    operation: str
    test_name: str
    sub_test_name: str
    test_number: int
    params: dict
    pre_run_step: str
    op_func: Callable
    duration: float = 0.0
    message: str = ""
    status: str = ""

    def __bool__(self):
        return self.status == "pass"


def process_params(param):
    """
    Handle parameter values that cannot be encoded natively in json
    """
    if isinstance(param, list):
        if param[0] == "tuple":
            return tuple(param[1:])
    return param


class TestRunner:

    def __init__(self):
        self.args = None

    def configure(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-m",
                            "--mode",
                            type=str,
                            choices=["compare", "time"],
                            help="what mode to run in (compare or time)")
        parser.add_argument("-r", "--runs", type=int, default=5, help="number of times to run each test case")
        parser.add_argument("-v", "--verbose", action="store_true", help="print verbose output")
        parser.add_argument("-g", "--graphs", action="store_true", help="print verbose output")
        parser.add_argument("-k",
                            dest="match",
                            type=str,
                            help="only run tests which match the given substring expression")
        parser.add_argument("--gui", dest="gui", action="store_true", help="Show GUI comparison for differences")

        self.args = parser.parse_args()

    def run_tests(self):
        if self.args.mode == "time":
            self.time_mode(self.args.runs)

        if self.args.mode == "compare":
            self.compare_mode()

        if self.args.graphs:
            create_plots()

    def run_test(self, test_case):
        image_stack = self.load_image_stack()

        # Handling various pre-run steps
        if test_case.pre_run_step == 'add_nan':
            image_stack = self.add_nan(image_stack, fraction=0.1)
        elif test_case.pre_run_step == 'add_flats_and_darks':
            self.add_flats_and_darks(test_case.params)
        elif test_case.pre_run_step == 'load_monitor_log':
            log_data = self.load_monitor_log()
            image_stack.log_file = log_data
        elif test_case.pre_run_step == 'load_shutter_counts':
            shutter_data = self.load_shutter_counts()
            image_stack.shutter_count_file = shutter_data

        test_case.duration, new_image_stack = self.time_operation(image_stack, test_case.op_func, test_case.params)
        file_name = config_manager.save_dir / f"{test_case.test_name}.npz"

        if file_name.is_file():
            baseline_image_stack = self.load_post_operation_image_stack(file_name)
            self.compare_image_stacks(baseline_image_stack, new_image_stack.data, test_case)

            if test_case.status == "pass":
                print(".", end="")
            elif test_case.status == "fail":
                print("F", end="")
            else:
                print("?", end="")
                test_case.status = "unknown"
        else:
            print("X", end="")
            test_case.status = "new baseline"
            self.save_image_stack(file_name, new_image_stack)

        TEST_CASE_RESULTS.append(test_case)

    def add_flats_and_darks(self, params):
        for frame_type in ['flat_before', 'flat_after', 'dark_before', 'dark_after']:
            if frame_type not in params:
                continue
            try:
                filename_group = FilenameGroup.from_file(config_manager.load_sample)
                related_filename_group = filename_group.find_related(getattr(FILE_TYPES, params[frame_type]))
                if not related_filename_group:
                    raise ValueError(f"Related files not found for {frame_type}")
                related_filename_group.find_all_files()
                image_stack = loader.load(filename_group=related_filename_group)  # Corrected this line
                if image_stack is None or not hasattr(image_stack, 'data'):
                    raise ValueError(f"Failed to load or invalid image stack for {frame_type}")
                params[frame_type] = image_stack
            except Exception as e:
                print(f"Error with {frame_type}: {e}")

    def load_monitor_log(self):
        filename_group = FilenameGroup.from_file(config_manager.load_sample)
        filename_group.find_log_file()
        log_file_path = filename_group.log_path

        if log_file_path is None:
            raise ValueError("Log file path could not be determined.")

        with open(log_file_path) as file:
            log_lines = file.readlines()
            return InstrumentLog(log_lines, Path(log_file_path))

    def create_fake_shutter_files(self):
        shutter_count_data = np.array([[0, 74421], [1, 74420], [2, 74420], [3, 74420], [4, 74420], [5, 74418]])
        shutter_times_data = np.array([[0, 0.01, 0.0001007], [1, 0.00032416, 0.00001], [2, 0.00031424, 0.00002],
                                       [3, 0.00031424, 0.00003], [4, 0.00032256, 0.00002], [5, 0.00033472, 0.00004]])
        spectra_file_data = np.column_stack((np.linspace(0.01, 0.0120275,
                                                         num=100), np.linspace(1917858, 6389242, num=100, dtype=int)))

        self.shutter_log_dir = tempfile.TemporaryDirectory()

        np.savetxt(Path(self.shutter_log_dir.name) / "test_ShutterCount.txt",
                   shutter_count_data,
                   fmt='%.0f',
                   delimiter='\t')
        np.savetxt(Path(self.shutter_log_dir.name) / "test_ShutterTimes.txt",
                   shutter_times_data,
                   fmt='%.8f',
                   delimiter='\t')
        np.savetxt(Path(self.shutter_log_dir.name) / "test_Spectra.txt", spectra_file_data, fmt='%7.7f', delimiter='\t')

    def load_shutter_counts(self):
        self.create_fake_shutter_files()
        shutter_count_path = Path(self.shutter_log_dir.name) / "test_ShutterCount.txt"
        if shutter_count_path is None:
            raise ValueError("Shutter count file path could not be determined.")

        with open(shutter_count_path) as file:
            shutter_count_lines = file.readlines()

        return ShutterCount(shutter_count_lines, Path(shutter_count_path))

    def add_nan(self, image_stack, fraction=0.001):
        data = image_stack.data
        total_elements = data.size
        num_nans = int(total_elements * fraction)
        step_size = total_elements // num_nans
        nan_indices = np.arange(0, total_elements, step_size)[:num_nans]
        data.ravel()[nan_indices] = np.nan
        return image_stack

    def compare_mode(self):
        for operation, test_case_info in TEST_CASES.items():
            print(f"Running tests for {operation}:")
            cases = test_case_info["cases"]
            for test_number, case in enumerate(cases):
                sub_test_name = case["test_name"]
                test_name = f"{operation.lower()}_{sub_test_name}"
                if self.args.match and self.args.match not in test_name:
                    continue
                params = test_case_info["params"] | case["params"]
                params = {k: process_params(v) for k, v in params.items()}
                op_class = FILTERS[operation]
                op_func = op_class.filter_func
                pre_run_step = case.get("pre_run_step", {})
                test_case = TestCase(operation=operation,
                                     test_name=test_name,
                                     sub_test_name=sub_test_name,
                                     test_number=test_number,
                                     params=params,
                                     pre_run_step=pre_run_step,
                                     op_func=op_func)
                self.run_test(test_case)
            print("\n")

        self.print_compare_mode_results()

    def print_compare_mode_results(self):
        print(f"{'=' * 40}RESULTS{'=' * 40}")
        failures = 0
        passes = 0
        new_baselines = 0

        for test_case in TEST_CASE_RESULTS:
            if test_case.status == "fail":
                failures += 1
                print(f"[FAIL] {test_case.operation} test #{test_case.test_number:03d}"
                      f", {test_case.test_name} -> {test_case.message}\n")
            elif test_case.status == "pass":
                passes += 1
                if self.args.verbose:
                    print(f"[PASS] {test_case.operation} test #{test_case.test_number:03d},"
                          f"{test_case.test_name} -> {test_case.duration}s\n")
            elif test_case.status == "new baseline":
                new_baselines += 1
                if self.args.verbose:
                    print(f"[NEW] {test_case.operation} test #{test_case.test_number:03d}, {test_case.test_name}\n")

        print(f"{failures} failed\n{passes} passed\n{new_baselines} new baseline(s)")
        print(f"{'=' * 42}END{'=' * 42}")

    def time_mode(self, runs):
        # TODO: time_mode() does not run the re-processing steps like the compare mode does, i.e. load_monitor_log
        #  is not run for the monitor normalisation operation so it fails
        durations = defaultdict(list)
        image_stack = self.load_image_stack()
        for operation, test_case_info in TEST_CASES.items():
            print(f"Running tests for {operation}:")
            cases = test_case_info["cases"]
            for case in cases:
                sub_test_name = case["test_name"]
                test_name = f"{operation.lower()}_{sub_test_name}"
                params = case["params"] | test_case_info["params"]
                op_func = FILTERS[operation].filter_func
                for _ in range(runs):
                    image_stack2 = image_stack.copy()
                    duration = self.time_operation(image_stack2, op_func, params)[0]
                    durations[test_name].append(duration)

        self.print_time_mode_results(durations)

    def print_time_mode_results(self, durations):
        print(f"\n{'=' * 40}RESULTS{'=' * 40}", end="")
        with open("timings.csv", "a", newline="", encoding="utf_8") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            if csvfile.tell() == 0:
                writer.writerow(["test_name", "avg", "quickest", "slowest", "stdev", "version", "commit_date"])
            for test_name, times in durations.items():
                avg = sum(times) / len(times)
                quickest = min(times)
                slowest = max(times)
                print(f"\n{test_name}:\n\tAvg: {avg}\n\tQuickest: {quickest}\n\tSlowest: {slowest}")
                data = (
                    test_name,
                    avg,
                    quickest,
                    slowest,
                    stdev(times),
                    GIT_TOKEN,
                    COMMIT_DATE,
                )
                writer.writerow(data)

        print(f"{'=' * 42}END{'=' * 42}")

    def time_operation(self, image_stack, op_func, params):
        start = time.perf_counter()
        image_stack = self.run_operation(image_stack, op_func, params)
        duration = time.perf_counter() - start
        return duration, image_stack

    def run_operation(self, image_stack, op_func, params):
        op_func(image_stack, **params)
        return image_stack

    def save_image_stack(self, filepath, image_stack):
        np.savez(filepath, image_stack.data)

    def load_post_operation_image_stack(self, filepath):
        return np.load(filepath)["arr_0"]

    def load_image_stack(self):
        filename_group = FilenameGroup.from_file(config_manager.load_sample)
        filename_group.find_all_files()
        image_stack = loader.load(filename_group=filename_group)
        return image_stack

    def compare_image_stacks(self, baseline_image_stack, new_image_stack, test_case):
        if not (isinstance(baseline_image_stack, np.ndarray) and isinstance(new_image_stack, np.ndarray)):
            test_case.status = "fail"
            test_case.message = "new image stack is not an array"
        elif baseline_image_stack.shape != new_image_stack.shape:
            test_case.status = "fail"
            test_case.message = "new image stack is different shape to the baseline"
        elif baseline_image_stack.dtype != new_image_stack.dtype:
            test_case.status = "fail"
            test_case.message = "new image stack is different dtype to the baseline"
        elif not np.array_equal(baseline_image_stack, new_image_stack):
            test_case.status = "fail"
            test_case.message = "arrays are not equal"
            if self.args.gui:
                self.gui_compare_image_stacks(baseline_image_stack, new_image_stack)
        else:
            test_case.status = "pass"
            test_case.message = "arrays are equal"

    def gui_compare_image_stacks(self, baseline_image_stack, new_image_stack):
        from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout
        from mantidimaging.gui.widgets.mi_image_view.view import MIImageView
        app = QApplication([])
        win = QWidget()
        win.resize(600, 900)
        layout = QHBoxLayout()
        win.setLayout(layout)

        imvs = []
        for name, data in (
            ("Baseline", baseline_image_stack),
            ("New", new_image_stack),
            ("Diff", new_image_stack - baseline_image_stack),
        ):
            imv = MIImageView()
            imv.name = name
            imv.enable_nan_check(True)
            imv.setImage(data)
            layout.addWidget(imv)
            imvs.append(imv)

        imvs[0].sigTimeChanged.connect(imvs[1].setCurrentIndex)
        imvs[0].sigTimeChanged.connect(imvs[2].setCurrentIndex)

        win.show()
        app.exec()


def create_plots():
    df = pd.read_csv("timings.csv", parse_dates=["commit_date"])
    traces = []
    test_names = []

    for i, (test_name, group) in enumerate(df.groupby("test_name"), start=1):
        group.sort_values("commit_date", inplace=True)
        traces.append((
            i,
            go.Scatter(
                x=group["commit_date"],
                y=group["avg"],
                text=group["version"],
                name=f"{test_name} Average",
                error_y={
                    'type': 'data',
                    'array': group['stdev'],
                    'visible': True
                },
            ),
        ))
        traces.append((
            i,
            go.Scatter(
                x=group["commit_date"],
                y=group["quickest"],
                text=group["version"],
                name=f"{test_name} Minimum",
            ),
        ))
        test_names.append(test_name)

    fig = make_subplots(rows=len(traces), cols=1, subplot_titles=test_names)
    for i, trace in traces:
        fig.add_trace(trace, row=i, col=1)

    fig.update_layout(legend_tracegroupgap=238)
    fig.write_html(f"{datetime.today().strftime('%Y-%m-%d')}.html", default_height="1500%")


def main():
    runner = TestRunner()
    runner.configure()
    runner.run_tests()


if __name__ == "__main__":
    main()
