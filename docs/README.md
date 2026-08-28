# Documentation

This directory contains the technical documentation for the FPGA CPU Business Card and the broader custom CPU architecture.

## Documents

### [ARCHITECTURE.md](ARCHITECTURE.md)

Describes the processor architecture and FPGA implementation, including:

- 8-bit accumulator-based datapath
- General-purpose registers
- ALU
- Program counter
- Instruction memory
- Global data memory
- I/O
- LED output register
- Subroutine Register File
- Clock and reset behavior
- Differences between the full CPU and the resource-optimized business-card implementation

---

### [ISA.md](ISA.md)

Documents the custom 16-bit Instruction Set Architecture, including:

- Instruction format
- Opcode families
- Sub-operation encoding
- Arithmetic instructions
- Branch and jump instructions
- Load/store instructions
- Register-indirect memory access
- Subroutine instructions
- I/O instructions
- Interrupt-related instructions
- Assembler directives

---

### [PROGRAMMING.md](PROGRAMMING.md)

Explains how to configure and program the MAX 10 FPGA, including:

- JTAG pogo-pad interface
- USB-Blaster connections
- Quartus Programmer workflow
- Temporary `.sof` configuration
- Persistent internal-flash configuration
- Standalone boot verification
- Updating the CPU program
- Troubleshooting

---

## Project Documentation Flow

The documentation is organized roughly from hardware architecture to software execution:

```text
ARCHITECTURE.md
      |
      v
How the CPU works
      |
      v
ISA.md
      |
      v
How the CPU is programmed
      |
      v
PROGRAMMING.md
      |
      v
How the FPGA is configured
```

For source code and implementation files, see:

```text
../rtl/
../software/
../hardware/
```

The root project README provides the high-level overview of the complete FPGA CPU Business Card project.
