# FPGA CPU Business Card

A fully functional **8-bit custom CPU implemented on an Intel/Altera MAX 10 FPGA and integrated into a 6-layer PCB business card**.

The project combines custom processor architecture, FPGA RTL, a custom instruction set, assembler, compiler, and PCB design into a standalone embedded system.

The card executes real machine code on the custom CPU and calculates prime numbers at runtime, displaying each result in binary using eight onboard LEDs.

<p align="center">
  <img src="images/pcb-front.png" width="48%">
  <img src="images/pcb-back.png" width="48%">
</p>

---

## Overview

The FPGA CPU Business Card is a physical implementation of a custom accumulator-based processor.

The complete development flow spans from a high-level programming language down to the PCB:

```text
High-Level Program
        |
        v
 Custom Compiler
        |
        v
Custom Assembly
        |
        v
 Custom Assembler
        |
        v
16-bit Machine Code
        |
        v
Instruction Memory
        |
        v
Custom 8-bit CPU
        |
        v
Intel MAX 10 FPGA
        |
        v
6-Layer Custom PCB
        |
        v
8-bit LED Output
```

The goal of the project is to demonstrate the complete relationship between software, processor architecture, digital logic, and physical hardware.

---

## Features

### Custom CPU

- 8-bit accumulator-based architecture
- 16-bit fixed-width instructions
- 8 general-purpose registers
- Custom instruction set
- 8-bit global address space
- Conditional branching
- Memory and I/O operations
- Subroutine support in the broader architecture

### Arithmetic

The CPU implements four core arithmetic operations:

```text
ADD
SUB
MULT
DIV
```

Both immediate and register-based arithmetic instructions are supported.

### Software Toolchain

The project includes a custom Python-based:

- Compiler
- Assembler
- High-level programming language
- Assembly language
- Machine-code generator

The compiler supports features including:

- Variables
- Arithmetic expressions
- Operator precedence
- `if` statements
- `while` loops
- `for` loops
- Functions
- Function parameters
- Return values
- Arrays
- Variable array indexing
- Inline assembly
- Interrupt declarations
- TTY output
- Pixel/graphics operations

### Hardware

- Intel/Altera MAX 10 `10M02DCV36C8G`
- 6-layer PCB
- CR2032 battery power
- 1.2 V FPGA core supply
- 2.5 V FPGA I/O supply
- 8 onboard LEDs
- Manual reset button
- Power switch
- JTAG pogo-pad programming interface
- Internal FPGA configuration flash
- Automatic standalone boot

---

# Prime Number Demonstration

The default Business Card firmware calculates prime numbers at runtime.

The LED sequence is **not stored as a predefined animation**.

Instead, the custom CPU executes a program that tests candidate numbers for divisibility and writes each discovered prime to an 8-bit output register.

The sequence begins:

| Decimal | Binary |
|---:|:---:|
| 2 | `00000010` |
| 3 | `00000011` |
| 5 | `00000101` |
| 7 | `00000111` |
| 11 | `00001011` |
| 13 | `00001101` |
| 17 | `00010001` |
| 19 | `00010011` |
| 23 | `00010111` |
| 29 | `00011101` |
| 31 | `00011111` |

The program continues through the configured range before restarting.

Each prime remains latched on the LEDs while the CPU searches for the next value.

---

## Example Source Program

The default demonstration is written using the project's custom high-level language.

```text
let n = 2
let divisor = 2
let remainder = 0
let isPrime = 1
let run = 0

while run < 1

    n = 2

    while n < 100

        divisor = 2
        isPrime = 1

        while divisor < n

            remainder = n

            while divisor < remainder
                remainder = remainder - divisor
            ewhile

            if remainder == divisor
                remainder = 0
            endif

            if remainder == 0
                isPrime = 0
            endif

            divisor = divisor + 1

        ewhile

        if isPrime == 1
            asm = {
                load 0
                storeio 0
            }
        endif

        n = n + 1

    ewhile

ewhile
```

The compiler translates this into custom assembly, which is then converted by the assembler into 16-bit machine instructions executed by the FPGA CPU.

---

# CPU Architecture

The processor uses a compact accumulator-based datapath.

The Business Card implementation is a resource-optimized version of the larger CPU architecture.

One of the primary optimizations was reducing global data memory to **16 bytes**, allowing the processor to fit comfortably within the small MAX 10 FPGA while preserving its core architecture.

For a detailed description, see:

[CPU Architecture](docs/ARCHITECTURE.md)

---

# Instruction Set

Every instruction is 16 bits:

```text
15                    8 7      6 5       3 2       0
+----------------------+----------+---------+---------+
|      Immediate       |  Subop   | Register| Opcode  |
|        8 bits        |  2 bits  |  3 bits | 3 bits  |
+----------------------+----------+---------+---------+
```

The primary opcode families are:

| Opcode | Family |
|:---:|---|
| `000` | Subroutine Register File / Subroutine Control |
| `001` | Immediate Arithmetic |
| `010` | Register Arithmetic |
| `011` | I/O / CPU Control |
| `100` | Copy / Interrupt |
| `101` | Branch / Jump |
| `110` | Load |
| `111` | Store |

The complete ISA is documented here:

[Instruction Set Architecture](docs/ISA.md)

---

# Compiler and Assembler

The CPU has its own software toolchain written in Python.

## Compiler

The compiler translates the custom high-level language into CPU assembly.

```text
program.cpu
     |
     v
compiler.py
     |
     v
assembly.txt
```

Expressions are converted to postfix form before assembly generation, allowing arithmetic precedence and parentheses to be handled automatically.

The compiler also generates control-flow labels, function-call code, array addressing, and I/O operations.

[Compiler Documentation](software/compiler/README.md)

## Assembler

The assembler converts custom assembly into the processor's 16-bit machine-code format.

```text
assembly.txt
     |
     v
assembler.py
     |
     v
instruction_ram.hex
```

It resolves labels, instruction fields, sub-operations, directives, and memory initialization data.

[Assembler Documentation](software/assembler/README.md)

---

# FPGA Implementation

The Business Card targets:

```text
Intel/Altera MAX 10
10M02DCV36C8G
```

The processor is implemented entirely in FPGA logic.

The MAX 10 was selected in part because it contains internal non-volatile configuration memory.

After the internal configuration flash is programmed:

```text
Power On
   |
   v
MAX 10 Internal Flash
   |
   v
FPGA Configuration
   |
   v
Startup Reset
   |
   v
Custom CPU
   |
   v
Prime Program
```

The card therefore operates completely standalone after programming.

No external FPGA configuration-memory IC is required.

---

# PCB

The processor is integrated into a custom **6-layer PCB business card** measuring approximately:

```text
88.9 mm × 50.8 mm
```

The PCB includes:

- MAX 10 FPGA
- FPGA power distribution
- 1.2 V and 2.5 V regulators
- Local decoupling
- CR2032 battery holder
- Power switch
- Reset button
- Eight LED outputs
- JTAG programming pads
- Configuration-pin biasing
- Via-in-pad FPGA routing
- QR codes linking the physical card back to the project

Editable PCB files, schematic files, Gerbers, BOM, and placement data are available in:

[Hardware Files](hardware/README.md)

---

# JTAG Programming

The board exposes a compact six-pad JTAG interface:

```text
TCK
TMS
TDI
TDO
2.5V
GND
```

A USB-Blaster compatible programmer can connect through a pogo-pin fixture.

During development, a `.sof` can be loaded directly into the FPGA.

For standalone operation, the MAX 10 internal configuration flash can be programmed so the card automatically boots whenever power is applied.

[Programming Guide](docs/PROGRAMMING.md)

---

# Repository Structure

```text
.
├── rtl/
│   └── Verilog implementation of the Business Card CPU
│
├── software/
│   ├── compiler/
│   ├── assembler/
│   └── examples/
│
├── hardware/
│   ├── schematic/
│   ├── pcb/
│   ├── gerbers/
│   ├── bom/
│   └── placement/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ISA.md
│   └── PROGRAMMING.md
│
└── images/
    └── Project renders and photographs (currently awaiting boards to arrive)
```

---

# Documentation

More detailed documentation is available in the repository:

- [CPU Architecture](docs/ARCHITECTURE.md)
- [Instruction Set Architecture](docs/ISA.md)
- [FPGA Programming](docs/PROGRAMMING.md)
- [RTL](rtl/README.md)
- [Software Toolchain](software/README.md)
- [Hardware](hardware/README.md)

---

# Development

The project was developed and tested using:

- Intel Quartus Prime
- Verilog HDL
- Python
- EasyEDA
- Logisim
- Intel/Altera MAX 10 FPGA hardware

The CPU architecture and software toolchain were first developed and tested independently before being reduced and integrated into the Business Card FPGA implementation.

---

# Current Status

**Rev A**

- CPU RTL complete
- Compiler and assembler operational
- Prime-number firmware verified in simulation
- Firmware verified on MAX 10 development hardware
- 6-layer PCB designed
- FPGA design successfully fitted to the `10M02DCV36C8G`
- Manufacturing files generated
- Rev A PCB submitted for fabrication and assembly

Photos and hardware validation results will be added after the assembled boards arrive.

---
