import os
import sys
import argparse
from pathlib import Path
import json
from parser import Parser

class Assembler:
    def __init__(self, verbose=False):
        self._labels = {}
        self._source = {}                           # Contains info on all source code encountered
        self._PC = 0
        self._cur_file = None
        self._output_file_path = None
        self.verbose = verbose

    def _verbose_print(self, *msgs):
        if self.verbose:
            print("INFO:", *msgs)

    def assemble(self, source_file, output_file=None, verbose=False):
        if self._output_file_path == None:
            if output_file == None:
                try:
                    self._output_file_path = f"{os.path.splitext(source_file)[0]}.out"
                except Exception:
                    print(f"ERROR: Invalid input file {source_file}")
                    sys.exit(-1)
            else:
                # TODO Validate output path
                self._output_file_path = output_file

        self._verbose_print(f"Output file set to {self._output_file_path}")

        self.parser = Parser(source_file)

        # Extract labels
        self._pass_one()

        # Translate instructions to binary
        self._pass_two()

        # Output binary

    def _pass_one(self):
        self._verbose_print(f"=== Starting first pass for {self._cur_file} ===")

    def _pass_two(self):
        # Turn assembly to binary...
        self._verbose_print(f"=== Starting first pass for {self._cur_file} ===")

    def _error(self, line_num, msg, error_code):
        print(f"{self._cur_file}:{line_num}: ERROR: {msg}")
        sys.exit(error_code)


def main():
    parser = argparse.ArgumentParser(
        description="A simple ARMv7 assembler.",
        usage="%(prog)s <source_file> [-o output_file]"
    )

    parser.add_argument(
        "source_file",
        type=str,
        help="Input assembly file to be assembled."
    )

    parser.add_argument(
        "--output-file", "-o",
        required=False,
        dest="output_file",
        help="Specify the name of the output object file. Defaults to <source_file>.out",
        default=None,
        type=str
    )

    parser.add_argument(
        "--verbose", "-v",
        required=False,
        default=False,
        help="Enable verbose output of assembly process.",
        action="store_true",
        dest="verbose"
    )

    args = parser.parse_args()

    Assembler(verbose=args.verbose).assemble(
        source_file=args.source_file,
        output_file=args.output_file
    )


if __name__ == "__main__":
    main()

