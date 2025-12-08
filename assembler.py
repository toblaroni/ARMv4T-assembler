from enum import Enum
import os
import sys
import argparse
from pathlib import Path
import json
import re
from enum import Enum


class TokenType(Enum):
    Instruction = 0
    Directive = 1
    Label = 2


class Assembler:
    def __init__(self, verbose=False):
        self._labels = {}
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

                        tokens = [ el for el in re.split(r'\s|,', line) if el != "" ] 

                        for token in tokens:
                            token = {}
                            token["value"] = token

                            if self._token_is_label(token):
                                token["type"] = TokenType.Label
                            elif self._token_is_directive(token):
                                token["type"] = TokenType.Directive
                            else:
                                token["type"] = TokenType.Instruction
                            
                            token["line_num"] = i+1     # For error msg
                            self._source[self._cur_file]["tokens"].append(token)

        except IOError as e:
            print(f"ERROR: Unable to open source file '{source_file}'")
            sys.exit(1)


    def _token_is_label(self, token):
        return  token.endswith(':') and (token[0].isalpha() or token.startswith('_'))

    def _token_is_directive(self, token):
        return token.startswith('.')

    def _calc_padding(self, tokens, line_num):
        alignment = 4           # Default 2**2
        if len(tokens) == 2:
            power = tokens[1]
            try:
                alignment = 2**int(power)
            except ValueError:
                self._error(line_num, f"Expected integer, got {power}", -1)

        return (alignment - (self._PC % alignment)) % alignment


    def _pass_one(self):
        self._verbose_print(f"=== Starting first pass for {self._cur_file} ===")

        for ins in self._source[self._cur_file]["instructions"]:
            self._verbose_print(f"Parsing line {ins["line_num"]}: {ins["tokens"]}")
            tokens = ins["tokens"]
            token_index = 0

            if self._token_is_label(tokens[0]):         # Label
                label_name = tokens[0][:-1]     # Remove colon
                if not label_name in self._labels:
                    self._labels[label_name] = self._PC
                    token_index = 1
                else:
                    self._error(ins["line_num"], f"{label_name} already defined.", -1)

            if token_index == len(tokens):  # Just a label on its own line
                continue

            # === Handle Directives ===
            elif self._token_is_directive(tokens[token_index]):
                directive = tokens[token_index].upper()
                self._verbose_print(f"Handling directive: {directive}")

                match directive:
                    # === CONTROL DIRECTIVES ===
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

                        self._PC += self._calc_padding(tokens, ins["line_num"])

                        
                    case ".TEXT":
                        continue
                    case ".DATA":
                        continue

                    # === Symbol Directives ===
                    case ".EQU" | ".SET":
                        continue
                    case ".GLOBAL" | ".GLOBL":  # This is for the linker...
                        continue

                    # === Constant Definition Directives ===
                    case ".BYTE":   # MVP
                        for token in tokens[1:]:
                            # Assume they're the right size for now...
                            self._PC += 1

                    case ".WORD" | ".INT" | ".LONG":    # MVP
                        for token in tokens[1:]:
                            # Assume they're the right size for now...
                            self._PC += 4   # 4-Bytes

                    case _:
                        self._error(ins["line_num"], f"This directive doesn't exist or hasn't been implemented yet: {directive}", -1)

            else:   # Assume normal instructions
                self._PC += 4

    def _pass_two(self):
        # Turn assembly to binary...
        self._verbose_print(f"=== Starting first pass for {self._cur_file} ===")

        self._PC = 0
        self._output_buffer = bytearray()

        for ins in self._source[self._cur_file]["instructions"]:
            tokens = ins["tokens"]
            
            # If first word in label, remove it
            if self._token_is_label(tokens[0]):
                tokens = tokens[1:]

            if len(tokens) == 0:
                continue
            
            if self._token_is_directive(tokens[0]):
                directive = tokens[0].upper()
                
                match directive:
                    # === CONTROL DIRECTIVES ===
                    case ".INCLUDE":    
                        continue    # Handled in first pass

                    case ".ALIGN" | ".BALIGN": 
                        if len(tokens) > 2:
                            self._error(ins["line_num"], "Syntax: '.ALIGN {expression}'", -1)

                        padding = self._calc_padding(tokens, ins["line_num"])

                        if padding != 0:
                            self._output_buffer.extend(bytearray.fromhex('00'*padding))
                            self._PC += padding
                            self._verbose_print(f"Alignment: Padded {padding} bytes (PC now at 0x{self._PC:X})")
                        
                    # ** Ignoring these for now
                    case ".TEXT":
                        continue
                    case ".DATA":
                        continue
                    # === Symbol Directives ===
                    case ".EQU" | ".SET":
                        continue
                    case ".GLOBAL" | ".GLOBL":  # This is for the linker...
                        continue

                    # === Constant Definition Directives ===
                    case ".BYTE":
                        for token in tokens[1:]:


                    case ".WORD" | ".INT" | ".LONG":    # MVP
                        for token in tokens[1:]:
                            # Assume they're the right size for now...
                            self._PC += 4   # 4-Bytes

                    case _:
                        self._error(ins["line_num"], f"This directive doesn't exist or hasn't been implemented yet: {directive}", -1)


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

