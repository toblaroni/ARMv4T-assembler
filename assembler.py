from enum import Enum
import os
import sys
import argparse
from pathlib import Path
import json
import re

class InstructionMode(Enum):
    ARM = 0
    THUMB = 1

class Assembler:
    def __init__(self, verbose=False):
        self._labels = {}
        self._INS_SET_MODE = InstructionMode.ARM    # Default
        self._source = {}                           # Contains info on all source code encountered
        self._PC = 0
        self._cur_file = None
        self._machine_code = []                     # Have a mega buffer that stores all output instructions
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

        # Parse (2 passes)
        self._parse_source_file(source_file)   

        # Extract labels
        self._pass_one()

        # Translate instructions to binary
        self._pass_two()

        print("Compilation Successful.")
        
    def _error(self, line_num, msg, error_code):
        print(f"{self._cur_file}:{line_num}: ERROR: {msg}")
        sys.exit(error_code)

    def _parse_source_file(self, source_file):
        try:
            with open(source_file, 'r') as file:
                file_name = os.path.basename(source_file)
                if file_name in self._source:
                    print(f"ERROR: {file_name} already parsed?!")
                    sys.exit(-1)

                self._verbose_print(f"Parsing {source_file}...")
                
                self._source[file_name] = {}
                self._source[file_name]["instructions"] = []
                self._source[file_name]["parent_file"] = self._cur_file     # Top-level file has no parent
                self._cur_file = file_name

                # Clean the lines
                for i, line in enumerate(file):
                    line = line.strip()
                    if line == '' or line.startswith("//"):
                        continue
                    else:
                        if ("//" in line):
                            line = line[:line.index("//")]      # Remove comments

                        instruction = {}
                        instruction["line_num"] = i+1     # For error msg
                        instruction["tokens"] = [ el for el in re.split(r'\s|,', line) if el != "" ] 

                        self._source[self._cur_file]["instructions"].append(instruction)


        except IOError as e:
            print(f"ERROR: Unable to open source file '{source_file}'")
            sys.exit(1)


    def _pass_one(self):
        self._verbose_print(f"Starting first pass for {self._cur_file}")

        for ins in self._source[self._cur_file]["instructions"]:
            self._verbose_print(f"Parsing line {ins["line_num"]}: {ins["tokens"]}")
            tokens = ins["tokens"]
            token_index = 0

            if tokens[0].endswith(':'):         # Label
                label_name = tokens[0][:-1]     # Remove colon

                if tokens[0][0].isalpha() or tokens[0].startswith('_'):
                    if not label_name in self._labels:
                        self._labels[label_name] = self._PC
                        token_index = 1
                    else:
                        self._error(ins["line_num"], f"{label_name} already defined.", -1)
                else:
                    self._error(ins["line_num"], "Invalid label.", -1) 

            if token_index == len(tokens):  # Just a label on its own line
                continue

            # === Handle Directives ===
            elif tokens[token_index].startswith('.'):
                directive = tokens[token_index].upper()
                self._verbose_print(f"Handling directive: {directive}")

                match directive:
                    # === CONTROL DIRECTIVES ===
                    case ".ARM":    
                        self._INS_SET_MODE = InstructionMode.ARM
                    case ".THUMB":
                        self._INS_SET_MODE = InstructionMode.THUMB
                    case ".CODE":
                        if len(tokens) != 2:
                            self._error(ins["line_num"], "Expected instruction set 32 or 16 after .code.", -1) 

                        code = tokens[token_index+1]
                        if code == "16":
                            self._INS_SET_MODE = InstructionMode.THUMB
                        elif code == "32":
                            self._INS_SET_MODE = InstructionMode.ARM
                        else:
                            self._error(ins["line_num"], f"Invalid instruction set {code}. Expected 16 or 32.", -1)

                    case ".INCLUDE":    
                        # .include {file}
                        if len(tokens) != 2:
                            self._error(ins["line_num"], "Syntax: '.INCLUDE {filename}'.", -1)
                        
                        # We need to recursively assemble the files
                        source_file = tokens[token_index+1]
                        self.assemble(source_file)
                        self._cur_file = self._source[self._cur_file]["parent_file"]

                    case ".ALIGN" | ".BALIGN":  # MVP
                        # .align {expression,{offset-expression}}
                        # I will ignore offset expression
                        if len(tokens) > 2:
                            self._error(ins["line_num"], "Syntax: '.ALIGN {expression}'", -1)

                        alignment = 4           # Default 2**2
                        if len(tokens) == 2:
                            power = tokens[token_index+1]
                            try:
                                alignment = 2**int(power)
                            except ValueError:
                                self._error(ins["line_num"], f"Expected integer, got {power}", -1)

                        padding = (alignment - (self._PC % alignment)) % alignment
                        self._PC += padding
                        
                    case ".TEXT":   # N2H
                        pass
                    case ".DATA":   # N2H
                        pass

                    case ".BALIGNW" | ".BALIGNL" | ".END" | ".FAIL" | ".ERR" | ".PRINT" | ".SECTION" | ".BSS" | ".STRUCT" | ".ORG" | ".POOL":
                        self._error(ins["line_num"], f"Directive {directive} not implemented yet!", -1)

                    # === Symbol Directives ===
                    case ".EQU" | ".SET":   # N2H
                        pass
                    case ".GLOBAL" | ".GLOBL":  # N2H
                        pass
                    case ".EQUIV":
                        self._error(ins["line_num"], f"Directive {directive} not implemented yet!", -1)

                    # === Constant Definition Directives ===
                    case ".BYTE":   # MVP
                        if len(tokens) == 1:
                            self._error(ins["line_num"], f"Expected value(s) after .BYTE directive.", -1)
                        for token in tokens[1:]:
                            if token.startswith("0x") and len(token[2:]) != 2:
                                self._error(ins["line_num"], f"Expected byte-sized value, got {token}.", -1)
                            self._PC += 1

                    case ".WORD" | ".INT" | ".LONG":    # MVP
                        pass

                    # Implement later
                    case ".HWORD" | ".SHORT" | ".ASCII" | ".ASCIZ" | ".STRING" | ".QUAD" | ".OCTA" | ".FLOAT" | ".SINGLE" | ".DOUBLE" | ".FILL" | ".ZERO" | ".SPACE" | "SKIP":
                        self._error(ins["line_num"], f"Directive {directive} not implemented yet!", -1)

                    # === Conditional Directives ===
                    # Preprocessor...
                    # Implement later
                    case ".IF" | ".ELSEIF" | ".ELSE" | ".ENDIF" | ".IFDEF" | ".IFNDEF" | ".IFNOTDEF" | ".IFC" | ".IFEQS" | ".IFNES" | ".IFEQ" | ".IFNE" | ".IFGE" | ".IFLE" | ".IFLT":
                        self._error(ins["line_num"], "Preprocessor directives not implemented yet!", -1)

                    # === Looping Directives ===
                    # Implement later
                    case ".REPT" | ".IRP" | ".IRPC" | ".ENDR":
                        self._error(ins["line_num"], "Looping directives not implemented yet!", -1)

                    # === Macro Directives ===
                    # Advanced assembler features
                    # Implement later
                    case ".MACRO" | ".ENDM" |".EXITM" | ".PURGEM":
                        self._error(ins["line_num"], "Macro directives not implemented yet!", -1)

                    case _:
                        self._error(ins["line_num"], f"Encountered unknown directive: {directive}", -1)


    def _pass_two(self):
        pass



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

