# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from tifffile import tifffile
import time

SIZE = (128, 128)


def make_image(size: tuple[int, int], message: str) -> np.ndarray:
    img = Image.new("L", size)
    draw = ImageDraw.Draw(img)
    draw.text([size[0] // 4, size[1] // 4], message, fill=255)
    return np.array(img) / 256


def make_dataset(dest_dir: Path, args: argparse.Namespace) -> None:

    if not dest_dir.exists():
        dest_dir.mkdir()

    for i in range(args.file_start, args.file_start + args.file_count):
        image = make_image(SIZE, f"Image {i}")
        file_path = dest_dir / f"image_{i:05}.tiff"
        tifffile.imwrite(
            file_path,
            (image * 2**15).astype(np.uint16),
            #compression="ZLIB",
        )
        if args.verbose:
            print("Image saved at", file_path)

        time.sleep(float(args.rate))


def main() -> None:
    """
    Main function to copy dataset from a source directory to a destination directory
    """
    default_output_dir = os.path.join(os.getcwd(), "mock_dataset_copy")
    parser = argparse.ArgumentParser(description="Make a dataset at a specified rate (s)")
    parser.add_argument("-d",
                        "--dest_dir",
                        default=default_output_dir,
                        required=False,
                        help="Destination directory to copy dataset to")
    parser.add_argument("-f", "--file-count", type=int, default=100)
    parser.add_argument("-s", "--file-start", type=int, default=0)
    parser.add_argument("-r",
                        "--rate",
                        default=0,
                        type=float,
                        required=False,
                        help="Rate in seconds at which to copy files from dataset i.e. 1, 1.5, 2...")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    args = parser.parse_args()
    make_dataset(Path(args.dest_dir), args)
    print("Complete")


if __name__ == "__main__":
    main()
