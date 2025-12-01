from enum import Enum
import os
import sys

class InstructionMode(Enum):
    ARM = 0
    THUMB = 1

class Assembler:
    def __init__(self):

        self._labels = {}
        self._INS_SET_MODE = InstructionMode.ARM

    def assemble(self, source_file):
        # Parse (2 passes)
        self._parse_source_file(source_file)   

        # Extract labels
        self._pass_one()

        # Translate instructions to binary
        self._pass_two()
        
    def _error(self, line_num, msg, error_code):
        print(f"{self.source["name"]}:{line_num}: ERROR: {msg}")
        sys.exit(error_code)

    def _parse_source_file(self, source_file):
        try:
            with open(source_file, 'r') as file:
                self.source = {}
                self.source["name"] = os.path.basename(source_file)
                self.source["instructions"] = []

                # Clean the lines
                for i, line in enumerate(file):
                    line = line.strip()
                    if line == '' or line.startswith("//"):
                        continue
                    else:
                        if ("//" in line):
                            line = line[:line.index("//")]      # Remove comments

                        instruction = {}
                        instruction["line_num"] = i     # For error msg
                        instruction["tokens"] = [el for el in line.split(' ') if el != '']
                        self.source["instructions"].append(instruction)

        except IOError as e:
            print(f"ERROR: Unable to open source file '{source_file}'")
            sys.exit(1)


    def _pass_one(self):
        # First pass collect all the labels and their line num
        PC = 0

        for ins in self.source["instructions"]:
            first_word = ins["tokens"][0]

            if first_word.endswith(':'):        # Label
                label_name = first_word[:-1]

                if first_word[0].isalpha() or first_word.startswith('_'):
                    self._labels[label_name] = PC
                else:
                    self._error(ins["line_num"], "Invalid label.", -1) 

            elif first_word.startswith('.'):    # Directive
                directive = first_word.upper()

                match directive:
                    # === CONTROL DIRECTIVES ===
                    case ".ARM":    
                        self._INS_SET_MODE = InstructionMode.ARM
                    case ".THUMB":
                        self._INS_SET_MODE = InstructionMode.THUMB
                    case ".CODE":
                        if ins["tokens"] != 2:
                            self._error(ins["line_num"], "Expected instruction set 32 or 16 after .code.", -1) 

                        code = ins["tokens"][1]
                        if code == "16":
                            self._INS_SET_MODE = InstructionMode.THUMB
                        elif code == "32":
                            self._INS_SET_MODE = InstructionMode.ARM
                        else:
                            self._error(ins["line_num"], f"Invalid instruction set {code}. Expected 16 or 32.", -1)
                    case ".INCLUDE":
                        # .include {file}
                        pass
                    case ".ALIGN" | ".BALIGN": 
                        # .align {alignment} {, fill}, {, max}
                        pass
                    case ".BALIGNW":
                        pass
                    case ".BALIGNL":
                        pass
                    case ".END":
                        pass
                    case ".FAIL":
                        pass
                    case ".ERR":
                        pass
                    case ".PRINT":
                        pass
                    case ".SECTION":
                        pass
                    case ".TEXT":
                        pass
                    case ".DATA":
                        pass
                    case ".BSS":
                        pass
                    case ".STRUCT":
                        pass
                    case ".ORG":
                        pass
                    case ".POOL":
                        pass

                    # === Symbol Directives ===
                    case ".EQU" | ".SET":
                        pass
                    case ".EQUIV":
                        pass
                    case ".GLOBAL" | ".GLOBL":
                        pass

                    # === Constant Definition Directives ===
                    case ".BYTE":
                        pass
                    case ".HWORD" | ".SHORT":
                        pass
                    case ".WORD" | ".INT" | ".LONG":
                        pass
                    case ".ASCII":
                        pass
                    case ".ASCIZ":
                        pass
                    case ".STRING":
                        pass
                    case ".QUAD":
                        pass
                    case ".OCTA":
                        pass
                    case ".FLOAT" | ".SINGLE":
                        pass
                    case ".DOUBLE":
                        pass
                    case ".FILL":
                        pass
                    case ".ZERO":
                        pass
                    case ".SPACE" | "SKIP":
                        pass

                    # === Assembly Listing Directives ===
                    case ".EJECT":
                        pass
                    case ".PSIZE":
                        pass
                    case ".LIST":
                        pass
                    case ".NOLIST":
                        pass
                    case ".TITLE":
                        pass
                    case ".SBTTL":
                        pass
                    
                    # === Conditional Directives ===
                    case ".IF":
                        pass
                    case ".ELSEIF":
                        pass
                    case ".ELSE":
                        pass
                    case ".ENDIF":
                        pass
                    case ".IFDEF":
                        pass
                    case ".IFNDEF" | ".IFNOTDEF":
                        pass
                    case ".IFC" | ".IFEQS" | ".IFNES":
                        pass
                    case ".IFEQ":
                        pass
                    case ".IFNE":
                        pass
                    case ".IFGE":
                        pass
                    case ".IFLE":
                        pass
                    case ".IFLT":
                        pass

                    # === Debug Directives ===
                    case ".FUNC" | ".ENDFUNC" | ".STABS":
                        continue

                    # === Looping Directives ===
                    case ".REPT":
                        pass
                    case ".IRP":
                        pass
                    case ".IRPC":
                        pass
                    case ".ENDR":
                        pass

                    # === Macro Directives ===
                    case ".MACRO":
                        pass
                    case ".ENDM":
                        pass
                    case ".EXITM":
                        pass
                    case ".PURGEM":
                        pass


    def _pass_two(self):
        pass



def main():
    if (len(sys.argv) != 2):
        print("ERROR: Usage 'python assembler.py <source_file>'")
        sys.exit(1)

    source_file = sys.argv[1]
    Assembler().assemble(source_file)


if __name__ == "__main__":
    main()

