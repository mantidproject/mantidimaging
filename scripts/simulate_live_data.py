# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from pathlib import Path
import os
import shutil
import argparse
import random

from tqdm import tqdm
import time


def copy_dataset(source_dir: Path, dest_dir: Path, rate: float, mode: str, verbose: bool) -> None:
    """
    Copy data from a source directory to a destination directory.
    Files are copied one image at a time at a specified rate in seconds.

    param source_dir: Source directory containing dataset to copy
    param dest_dir: Destination directory to copy dataset to
    param rate: Rate in seconds at which to copy files from dataset i.e. 1, 1.5, 2...
    param slow_copy_mode: copy the file slowly in chunks
    """
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)
    source_list = list(source_dir.iterdir())
    it = source_list if verbose else tqdm(source_list)

    for item in it:
        source_item = item
        dest_item = dest_dir / item.name
        if source_item.is_file():
            if verbose:
                print(f"Copying {source_item}", end="", flush=True)

            if mode == "slow":
                slow_copy(source_item, dest_item)
            elif mode == "faulty":
                faulty_copy(source_item, dest_item)
            else:
                shutil.copy(source_item, dest_item)
            if verbose:
                print(" DONE")

            time.sleep(rate)
        elif source_item.is_dir():
            copy_dataset(source_item, dest_item, rate, mode, verbose)

def slow_copy(source: Path, dest: Path) -> None:
    data = source.read_bytes()
    data_size = len(data)
    if dest.exists():
        dest.unlink()
    with dest.open("wb") as dest_file:
        written = 0
        while written < data_size:
            time.sleep(0.1)
            start = written
            stop = start + data_size // 10
            written += dest_file.write(data[start:stop])


def faulty_copy(source: Path, dest: Path) -> None:
    data = source.read_bytes()
    data_size = len(data)
    if dest.exists():
        dest.unlink()
    if random.random() < 0.1:
        data = data[:random.randint(0, data_size)]
    dest.write_bytes(data)


def main() -> None:
    """
    Main function to copy dataset from a source directory to a destination directory
    """
    default_output_dir = Path.cwd() / "mock_dataset_copy"
    parser = argparse.ArgumentParser(description="Make copy of dataset at a specified rate (s)")
    parser.add_argument("-s", "--source_dir", required=True, help="Source directory containing dataset to copy")
    parser.add_argument("-d",
                        "--dest_dir",
                        default=default_output_dir,
                        required=False,
                        help="Destination directory to copy dataset to")
    parser.add_argument("-r",
                        "--rate",
                        default=0,
                        type=float,
                        required=False,
                        help="Rate in seconds at which to copy files from dataset i.e. 1, 1.5, 2...")
    parser.add_argument("--mode", choices=["normal", "slow", "faulty"], help="Copy method", default="normal")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    args = parser.parse_args()
    copy_dataset(args.source_dir, args.dest_dir, args.rate, args.mode, args.verbose)
    print("Copy complete")


if __name__ == "__main__":
    main()
