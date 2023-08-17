# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import shutil
import argparse
import random

from tqdm import tqdm
import time


def copy_dataset(source_dir, dest_dir, rate, slow_copy_mode, faulty_copy_mode):
    """
    Copy data from a source directory to a destination directory.
    Files are copied one image at a time at a specified rate in seconds.

    param source_dir: Source directory containing dataset to copy
    param dest_dir: Destination directory to copy dataset to
    param rate: Rate in seconds at which to copy files from dataset i.e. 1, 1.5, 2...
    param slow_copy_mode: copy the file slowly in chunks
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    source_list = os.listdir(source_dir)
    for item in tqdm(source_list):
        source_item = os.path.join(source_dir, item)
        dest_item = os.path.join(dest_dir, item)
        if os.path.isfile(source_item):
            if slow_copy_mode:
                slow_copy(source_item, dest_item)
            elif faulty_copy_mode:
                faulty_copy(source_item, dest_item)
            else:
                shutil.copy(source_item, dest_item)

            time.sleep(float(rate))
        if os.path.isdir(source_item):
            copy_dataset(source_item, dest_item, rate, slow_copy_mode, faulty_copy_mode)


def slow_copy(source, dest):
    with open(source, "rb") as source_file:
        data = source_file.read()
    data_size = len(data)

    if os.path.exists(dest):
        os.remove(dest)

    with open(dest, "wb") as dest_file:
        writen = 0
        while writen < data_size:
            time.sleep(0.1)
            start = writen
            stop = start + data_size // 10
            writen += dest_file.write(data[start:stop])


def faulty_copy(source, dest):
    with open(source, "rb") as source_file:
        data = source_file.read()
    data_size = len(data)

    if os.path.exists(dest):
        os.remove(dest)

    if random.random() < 0.1:
        data = data[:random.randint(0, data_size)]

    with open(dest, "wb") as dest_file:
        dest_file.write(data)


def main():
    """
    Main function to copy dataset from a source directory to a destination directory
    """
    default_output_dir = os.path.join(os.getcwd(), "mock_dataset_copy")
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
    parser.add_argument("--slow", action="store_true", help="Use slow copy method")
    parser.add_argument("--faulty", action="store_true", help="Use faulty copy method")
    args = parser.parse_args()
    copy_dataset(args.source_dir, args.dest_dir, args.rate, args.slow, args.faulty)
    print("Copy complete")
    os._exit(0)


if __name__ == "__main__":
    main()
