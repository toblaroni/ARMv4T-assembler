# Assembler
The purpose of this project is to learn a bit of assembly and how assemblers work by writing one myself in Python. I have written a simple assembler as part of the NAND2Tetris project but this was very simplified. I'm interested in learning about real-world instruction sets and how they get assembled. 

### RISC-V
I am going to make a RISC-V assembler. Specifically a RV32I assembler. RISC-V is a free and open source ISA, as opposed to ARM and x86 which are licensed. There are many extensions of the base ISA, however I want to build an assembler for the RV32I base instruction set. 

### RV32I
- RV32I is the 32-bit base integer instruction set (no floating point operations). 
- It has 40 instructions. 
- It's little-endian. 
- I will be using GNU assembler syntax.
- Instructions are aligned on 4-byte boundaries (misalignment causes exception). 

### Resources
- [Comprehensive Guide to 32-Bit RISC-V Assembly Programming](https://gist.github.com/robert-saramet/1b9ef3cac5a8345c90d84ac1ac4a8d2b)
- [RV32I Cheat Sheet](https://www.vicilogic.com/static/ext/RISCV/RV32I_BaseInstructionSet.pdf)


