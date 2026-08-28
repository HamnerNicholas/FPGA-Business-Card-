# Software

This directory contains the software toolchain and example programs for the custom FPGA CPU.

The toolchain allows programs to be written in either the custom high-level language or directly in assembly before being converted into 16-bit machine code for the processor.

## Software Flow

```text
High-Level Source
      |
      v
   Compiler
      |
      v
Custom Assembly
      |
      v
   Assembler
      |
      v
16-bit Machine Code
      |
      v
FPGA Instruction Memory
```

Assembly programs can also be passed directly to the assembler without using the compiler.

## Directory Structure

```text
software/
├── compiler/
│   └── High-level language compiler
│
├── assembler/
│   └── Custom ISA assembler
│
└── examples/
    └── Example programs for the CPU
```

### Compiler

The `compiler/` directory contains the Python compiler for the custom high-level programming language.

It supports variables, arithmetic expressions, control flow, functions, arrays, inline assembly, and other features targeting the custom CPU architecture.

See [`compiler/README.md`](compiler/README.md) for syntax, features, and usage.

### Assembler

The `assembler/` directory contains the assembler for the custom 16-bit instruction format.

It translates assembly instructions and labels into machine code that can be loaded into the FPGA's instruction memory.

See [`assembler/README.md`](assembler/README.md) for details.

### Examples

The `examples/` directory contains programs demonstrating the CPU and software toolchain.

The primary FPGA Business Card demonstration calculates prime numbers at runtime and displays each discovered prime in binary using the eight onboard LEDs.

See [`examples/README.md`](examples/README.md) for more information.

## Business Card Demo

The software running on the FPGA Business Card is compiled using this toolchain.

Rather than storing a predefined LED sequence, the CPU executes a program that searches for prime numbers and writes each result to the card's LED output register.

```text
Source Program
     ↓
Compiler
     ↓
Assembler
     ↓
Machine Code
     ↓
Custom CPU
     ↓
Prime Calculation
     ↓
8-Bit LED Output
```

The compiler and assembler support the broader custom CPU architecture, so some software features are not required by the resource-optimized Business Card implementation.
