# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
This is a Utility script to unpack tiff files into a directory of images using lossless compression.
Paths used as arguments are relative to the location of the script.
If a destination path does not exist, the script will create it.
This script is temporary while larger work is undertaken to improve how datasets are loaded,
stored and accessed within Mantid Imaging.

Usage:
    python tiff_unpacker.py -s <path to tiff file> -d <path to output directory>
    python tiff_unpacker.py
        -s <path to tiff file>
        -d <path to output directory>
        -r <start> <stop>
        -n <naming convention>

Example usage with all arguments to unpack images 10 to 20 with naming convention "tbin_<index>":
    python tiff_unpacker.py -s /path/to/tiff/file.tiff -d /path/to/output/directory -r 10 20 -n tbin_
"""
import argparse
from tqdm import tqdm
from pathlib import Path
from tifffile import TiffFile, imwrite
from logging import getLogger, basicConfig, INFO

basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=INFO)
logger = getLogger(__name__)


def unpack_tiff(source: Path, destination: Path, img_range: tuple[int, int], naming_convention: str) -> None:
    """
    Unpack a tiff file into a directory of LZW compressed tif images

    Parameters:
        source: Path to tiff file
        destination: Path to output directory

    Returns:
        None
    """
    with TiffFile(source) as tif:
        for i, img in enumerate(tqdm(tif.pages[img_range[0]:img_range[1]], desc="Unpacking tiff file")):
            imwrite(destination / f"{naming_convention}{i}.tiff",
                    img.asarray().astype('float32'),
                    compression="zlib",
                    predictor=True,
                    metadata={
                        'axes': img.axes,
                    })
    validate_written_file_count(destination, img_range)


def validate_written_file_count(destination: Path, img_range: tuple[int, int]) -> None:
    """
    Return a printed statement of the number of files written to the output directory and the expected number of files

    Parameters:
        destination: Path to output directory
        img_range: Range of images to unpack

    Returns:
        None
    """
    expected_files = img_range[1] - img_range[0]
    written_files = len(list(destination.glob("*.tiff")))
    if expected_files != written_files:
        logger.warning("Expected to write %s files but wrote %s files", expected_files, written_files)
    else:
        logger.info("Successfully wrote %s files to %s", expected_files, destination)


def validate_input_range(data_length: int, start: int, stop: int) -> tuple[int, int]:
    """
    Validate the input range

    If start is greater than stop then raise ValueError
    If stop is greater than the number of images in the tiff file then raise ValueError
    If stop is 0 then set stop to the number of images in the tiff file

    Parameters:
        data_length: Number of images in the tiff file
        start: Start index of the range
        stop: Stop index of the range

    Returns:
        Start index of the range
        Stop index of the range
    """
    if start > stop:
        raise ValueError(f"Start {start} must be less than stop {stop}")
    if stop > data_length:
        raise ValueError(f"Stop {stop} must be less than the number of images in the tiff file {data_length}")
    if stop == 0:
        stop = data_length
    return start, stop


def validate_paths(source: Path, destination: Path) -> None:
    """
    Validate the source and destination paths

    Parameters:
        source: Path to tiff file
        destination: Path to output directory

    Returns:
        None
    """
    if not source.is_file():
        raise ValueError(f"{source} is not a file")
    if not destination.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory %s as it previously did not exist", destination)


def input_parser() -> tuple[Path, Path, tuple[int, int], str]:
    """
    Input parser for the script

    Expected input:
        python tiff_unpacker.py <path to tiff file> <path to output directory>

    Returns:
        Path to tiff file
        Path to output directory
        Range of images to unpack
        Naming convention of output images
    """
    parser = argparse.ArgumentParser(description="Unpack tiff file into a directory of images")
    parser.add_argument("-s", "--source", help="Absolute path to tiff file", type=Path, required=True)
    parser.add_argument("-d", "--destination", help="Absolute path to output directory", type=Path, required=True)
    parser.add_argument("-r",
                        "--range",
                        help="Range of images to unpack start <start stop>",
                        type=int,
                        nargs=2,
                        required=False,
                        default=[0, 0])
    parser.add_argument("-n",
                        "--name",
                        help="Naming convention of output images (default is tbin_)",
                        type=str,
                        required=False,
                        default="tbin_")
    args = parser.parse_args()
    validate_paths(args.source, args.destination)
    args.range = validate_input_range(len(TiffFile(args.source).pages), *args.range)
    return args.source, args.destination, args.range, args.name


def main() -> None:
    """
    Main function to unpack tiff file into a directory of images
    """
    unpack_tiff(*input_parser())


if __name__ == "__main__":
    main()
