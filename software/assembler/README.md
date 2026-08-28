# Custom 8-Bit CPU Assembler

This directory contains the assembler for the custom 8-bit CPU implemented on the FPGA CPU Business Card.

The assembler converts assembly source code written for the processor's custom instruction set into 16-bit machine instructions that can be loaded into the FPGA's instruction memory.

## Overview

Each CPU instruction is encoded into a 16-bit instruction word containing:

- 8-bit immediate/address field
- 2-bit sub-operation field
- 3-bit register field
- 3-bit opcode

The assembler resolves instruction mnemonics, registers, immediate values, and labels into this machine-code format.

## Assembly Flow

```text
Assembly Source
      |
      v
   Assembler
      |
      v
16-bit Machine Code
      |
      v
instruction_ram.hex
      |
      v
FPGA Instruction Memory
```

## Features

The assembler supports the CPU's core instruction families, including:

- Arithmetic operations
- Immediate arithmetic
- Register operations
- Global memory load/store
- I/O load/store
- Conditional branches
- Jumps
- Labels
- Sub-operation encoding

The CPU retains the four primary arithmetic operations:

```text
ADD
SUB
MULT
DIV
```

## Output

The generated machine code is written to a HEX file that can be used to initialize the instruction memory in the Quartus FPGA project.

For the business card implementation, this file is:

```text
instruction_ram.hex
```

## Usage

Run the assembler with an assembly source file:

```bash
python assembler.py <assembly_file>
```

The resulting machine-code file can then be copied into the FPGA project's instruction-memory initialization file.

## Related Documentation

See the repository's ISA documentation for the complete instruction encoding and instruction set.

The higher-level compiler located in `../compiler/` automatically generates assembly compatible with this assembler.
