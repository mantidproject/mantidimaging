# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import stdev
from typing import Callable

import numpy as np
import pandas as pd

try:
    from plotly import graph_objs as go
    from plotly.subplots import make_subplots
except ModuleNotFoundError:
    print("Approval tests require plotly")
    print("Try: mamba install plotly")
    exit(1)

sys.path.append(str(Path(__file__).parent.parent.parent))
from mantidimaging.core.io.filenames import FilenameGroup  # noqa: E402
from mantidimaging.core.io.loader import loader  # noqa: E402
from mantidimaging.core.operations.loader import load_filter_packages  # noqa: E402

LOAD_SAMPLE = Path("C:/Users/44770/Downloads/mantidimaging-data-small "
                   "(2)/mantidimaging-data-small/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif")

if path := os.getenv("MANTIDIMAGING_APPROVAL_TESTS_DIR"):
    SAVE_DIR = Path(path)
else:
    print("Set MANTIDIMAGING_APPROVAL_TESTS_DIR for output path")
    exit(1)
if not SAVE_DIR.exists():
    print(f"Creating directory: {SAVE_DIR}")
    SAVE_DIR.mkdir()

FILTERS = {f.filter_name: f for f in load_filter_packages()}
TEST_CASE_RESULTS: list[TestCase] = []
GIT_TOKEN = subprocess.check_output(["git", "describe"], encoding="utf_8").strip()
COMMIT_DATE = subprocess.check_output(["git", "log", "--pretty=format:%ai", "-n1"], encoding="utf_8").strip()
with open(Path(__file__).parent / "test_cases.json", encoding="UTF-8") as f:
    TEST_CASES = json.load(f)


@dataclass
class TestCase:
    operation: str
    test_name: str
    sub_test_name: str
    test_number: int
    params: dict
    op_func: Callable
    duration: float = 0.0
    message: str = ""
    status: str = ""

    def __bool__(self):
        return self.status == "pass"


def compare_mode():
    for operation, test_case_info in TEST_CASES.items():
        print(f"Running tests for {operation}:")
        cases = test_case_info["cases"]
        for test_number, case in enumerate(cases):
            sub_test_name = case["test_name"]
            test_name = f"{operation.lower()}_{sub_test_name}"
            if args.match and args.match not in test_name:
                continue
            params = case["params"] | test_case_info["params"]
            op_class = FILTERS[operation]
            op_func = op_class.filter_func
            test_case = TestCase(operation, test_name, sub_test_name, test_number, params, op_func)
            run_test(test_case)
        print("\n")

    print_compare_mode_results()


def print_compare_mode_results():
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
            if args.verbose:
                print(f"[PASS] {test_case.operation} test #{test_case.test_number:03d},"
                      f"{test_case.test_name} -> {test_case.duration}s\n")
        elif test_case.status == "new baseline":
            new_baselines += 1
            if args.verbose:
                print(f"[NEW] {test_case.operation} test #{test_case.test_number:03d}, {test_case.test_name}\n")

    print(f"{failures} failed\n{passes} passed\n{new_baselines} new baseline(s)")
    print(f"{'=' * 42}END{'=' * 42}")


def time_mode(runs):
    durations = defaultdict(list)
    image_stack = load_image_stack()
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
                duration = time_operation(image_stack2, op_func, params)[0]
                durations[test_name].append(duration)

    print_time_mode_results(durations)


def print_time_mode_results(durations):
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


def time_operation(image_stack, op_func, params):
    start = time.perf_counter()
    image_stack = run_operation(image_stack, op_func, params)
    duration = time.perf_counter() - start
    return duration, image_stack


def run_test(test_case):
    image_stack = load_image_stack()
    test_case.duration, new_image_stack = time_operation(image_stack, test_case.op_func, test_case.params)

    file_name = SAVE_DIR / (test_case.test_name + ".npz")
    if file_name.is_file():
        baseline_image_stack = load_post_operation_image_stack(file_name)
        compare_image_stacks(baseline_image_stack, new_image_stack.data, test_case)
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
        save_image_stack(file_name, new_image_stack)

    TEST_CASE_RESULTS.append(test_case)


def run_operation(image_stack, op_func, params):
    op_func(image_stack, **params)
    return image_stack


def save_image_stack(filepath, image_stack):
    np.savez(filepath, image_stack.data)


def load_post_operation_image_stack(filepath):
    return np.load(filepath)["arr_0"]


def load_image_stack():
    filename_group = FilenameGroup.from_file(Path(LOAD_SAMPLE))
    filename_group.find_all_files()
    image_stack = loader.load(filename_group=filename_group)
    return image_stack


def compare_image_stacks(baseline_image_stack, new_image_stack, test_case):
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
        if args.gui:
            gui_compare_image_stacks(baseline_image_stack, new_image_stack)
    else:
        test_case.status = "pass"
        test_case.message = "arrays are equal"


def gui_compare_image_stacks(baseline_image_stack, new_image_stack):
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-m",
                        "--mode",
                        type=str,
                        choices=["compare", "time"],
                        help="what mode to run in (compare or time)")
    parser.add_argument("-r", "--runs", type=int, default=5, help="number of times to run each test case")
    parser.add_argument("-v", "--verbose", action="store_true", help="print verbose output")
    parser.add_argument("-g", "--graphs", action="store_true", help="print verbose output")
    parser.add_argument("-k", dest="match", type=str, help="only run tests which match the given substring expression")
    parser.add_argument("--gui", dest="gui", action="store_true", help="Show GUI comparison for differences")

    global args
    args = parser.parse_args()

    if args.mode == "time":
        time_mode(args.runs)

    if args.mode == "compare":
        compare_mode()

    if args.graphs:
        create_plots()


if __name__ == "__main__":
    main()
