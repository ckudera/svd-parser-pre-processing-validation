import os
import time
import logging
from typing import List
from cmsis_svd_original.parser import SVDParser as SVDParserOriginal
from cmsis_svd_new.parser import SVDParser as SVDParserNew


def get_svd_file_paths() -> List[str]:
    abs_path = os.path.dirname(os.path.abspath(__file__))

    svd_paths: List[str] = []
    for root, _, files in os.walk("./data"):
        for file in files:
            if file.endswith(".svd"):
                svd_paths.append(os.path.abspath(os.path.join(abs_path, root, file)))

    return svd_paths


def main() -> None:
    elapsed_original_time: int = 0
    elapsed_new_time: int = 0

    for svd_file_path in get_svd_file_paths():
        parser_original_dict = None
        parser_new_dict = None

        current_process_time = time.process_time_ns()
        try:
            parser_original = SVDParserOriginal.for_xml_file(svd_file_path)
            parser_original_dict = parser_original.get_device().to_dict()
        except KeyError as key_error:
            logging.error("original package: received KeyError for path %s: %s", svd_file_path, key_error)
        except TypeError as type_error:
            logging.error("original package: received TypeError for path %s: %s", svd_file_path, type_error)
        elapsed_original_time += time.process_time_ns() - current_process_time

        current_process_time = time.process_time_ns()
        try:
            parser_new = SVDParserNew.for_xml_file(svd_file_path)
            parser_new_dict = parser_new.get_device().to_dict()
        except KeyError as key_error:
            logging.error("new package: received KeyError for path %s: %s", svd_file_path, key_error)
        except TypeError as type_error:
            logging.error("new package: received TypeError for path %s: %s", svd_file_path, type_error)
        elapsed_new_time += time.process_time_ns() - current_process_time

        if parser_original_dict is not None and parser_new_dict is not None:
            if parser_original_dict != parser_new_dict:
                logging.error("different results for %s", svd_file_path)

    logging.info("original package: processing time in seconds: %.3f", elapsed_original_time / 1000000000)
    logging.info("new package: processing time in seconds: %.3f", elapsed_new_time / 1000000000)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
