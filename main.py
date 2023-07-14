import os
import sys
import json
from dataclasses import dataclass
import time
import logging
from typing import List
from cmsis_svd_original.parser import SVDParser as SVDParserOriginal
from cmsis_svd_new.parser import SVDParser as SVDParserNew

DATA_DIR = "data"
DIFFERENCES_DIR = "differences"


@dataclass
class SVDFilePath:
    name: str
    relative: str
    absolute: str
    directories: List[str]


def get_svd_file_paths() -> List[SVDFilePath]:
    abs_path = os.path.dirname(os.path.abspath(__file__))

    svd_paths: List[SVDFilePath] = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".svd"):
                svd_paths.append(
                    SVDFilePath(
                        name=file,
                        relative=os.path.join(root, file),
                        absolute=os.path.abspath(os.path.join(abs_path, root, file)),
                        directories=root.removeprefix(DATA_DIR).removeprefix("/").split("/"),
                    )
                )

    return svd_paths


def main() -> None:
    elapsed_original_time: int = 0
    elapsed_new_time: int = 0

    # iterate over all svd files in ./data directory
    for svd_file_path in get_svd_file_paths():
        parser_original_dict = None
        parser_new_dict = None

        # parse svd files with original package
        current_process_time = time.process_time_ns()
        try:
            parser_original = SVDParserOriginal.for_xml_file(svd_file_path.absolute)
            parser_original_dict = parser_original.get_device().to_dict()
        except KeyError as key_error:
            logging.error("original package: received KeyError for path %s: %s", svd_file_path.relative, key_error)
        except TypeError as type_error:
            logging.error("original package: received TypeError for path %s: %s", svd_file_path.relative, type_error)
        elapsed_original_time += time.process_time_ns() - current_process_time

        # parse svd files with new package (pre-processing approach)
        current_process_time = time.process_time_ns()
        try:
            parser_new = SVDParserNew.for_xml_file(svd_file_path.absolute)
            parser_new_dict = parser_new.get_device().to_dict()
        except KeyError as key_error:
            logging.error("new package: received KeyError for path %s: %s", svd_file_path.relative, key_error)
        except TypeError as type_error:
            logging.error("new package: received TypeError for path %s: %s", svd_file_path.relative, type_error)
        elapsed_new_time += time.process_time_ns() - current_process_time

        # if both packages where successful (i.e. no exception), but the resulting dictionaries are different, create
        # a corresponding folder in ./differences/ which contains the json dumps of both dictionaries
        if parser_original_dict is not None and parser_new_dict is not None:
            if parser_original_dict != parser_new_dict:
                logging.error("different results for %s", svd_file_path.relative)

                dir_path = os.path.join(
                    DIFFERENCES_DIR, os.path.sep.join(svd_file_path.directories), svd_file_path.name
                )
                os.makedirs(dir_path, exist_ok=True)

                with open(os.path.join(dir_path, "original.txt"), "w", encoding="utf8") as file:
                    file.write(json.dumps(parser_original_dict, sort_keys=True, indent=4, separators=(",", ": ")))

                with open(os.path.join(dir_path, "new.txt"), "w", encoding="utf8") as file:
                    file.write(json.dumps(parser_new_dict, sort_keys=True, indent=4, separators=(",", ": ")))

    # output the processing time of both packages
    logging.info("original package: processing time in seconds: %.3f", elapsed_original_time / 1000000000)
    logging.info("new package: processing time in seconds: %.3f", elapsed_new_time / 1000000000)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler(filename="logging.txt"), logging.StreamHandler(stream=sys.stderr)],
    )

    main()
