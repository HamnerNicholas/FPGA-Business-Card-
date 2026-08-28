# RTL

This directory contains the Verilog RTL for the custom 8-bit CPU implemented on the FPGA CPU Business Card.

The processor is a resource-optimized version of the larger custom CPU architecture, targeting the Intel/Altera MAX 10 `10M02DCV36C8G`.

The Business Card implementation retains the core processor datapath, arithmetic operations, memory system, control flow, and LED output while removing hardware that is unnecessary for the standalone card demonstration.

## Top-Level Design

The top-level module is:

```text
CPU_CARD.v
```

It connects the major processor components:

```text
                    Internal Oscillator
                            |
                            v
                      Clock Divider
                            |
                            v
                    +---------------+
                    |      PC       |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Instruction   |
                    | Memory        |
                    +-------+-------+
                            |
                            v
                    Instruction Decode
                            |
              +-------------+-------------+
              |                           |
              v                           v
        Register File                    ALU
              |                           |
              +-------------+-------------+
                            |
                            v
                      Accumulator
                            |
                  +---------+---------+
                  |                   |
                  v                   v
            Global Memory        LED Register
                                      |
                                      v
                                   LED[7:0]
```

## CPU Configuration

The Business Card processor uses:

```text
Data width:          8 bits
Address width:       8 bits
Instruction width:  16 bits
Registers:           8
Register address:    3 bits
Sub-operation field: 2 bits
```

The instruction format is documented in:

[`../docs/ISA.md`](../docs/ISA.md)

---

# RTL Modules

## `CPU_CARD.v`

Top-level module for the FPGA CPU Business Card.

Responsibilities include:

- Instantiating the MAX 10 internal oscillator
- Generating the CPU clock
- Generating the power-on reset
- Connecting the processor datapath
- Instantiating instruction memory
- Instantiating global data memory
- Decoding instruction sub-operations
- Driving the 8-bit LED output register

The module also contains the card-specific startup reset logic.

At power-up, the CPU is temporarily held in reset while a counter advances from its initial state.

Conceptually:

```text
Power Applied
     |
     v
MAX 10 Configures
     |
     v
Startup Counter
     |
     v
CPU Reset Released
     |
     v
Program Execution
```

The manual reset button is ORed with the automatic startup reset.

---

## `INSTRUCTION_RAM.v`

Stores and decodes the CPU's 16-bit program instructions.

The instruction format is:

```text
15                    8 7      6 5       3 2       0
+----------------------+----------+---------+---------+
|      Immediate       |  Subop   | Register| Opcode  |
|        8 bits        |  2 bits  |  3 bits | 3 bits  |
+----------------------+----------+---------+---------+
```

The module separates the current instruction into:

```text
imm
SubopField
regField
op_code
```

and generates the primary opcode control signals.

Program contents are initialized from:

```text
instruction_ram.hex
```

The Business Card implementation uses a reduced program-memory depth compared with the larger CPU implementation.

---

## `PC.v`

Implements the Program Counter and control-flow logic.

The PC normally advances sequentially through instruction memory.

It also handles control-flow operations such as:

```text
BEQ
BNE
BLT
JUMP
```

These instructions allow the compiler to generate:

- `if` statements
- `while` loops
- `for` loops
- Unconditional jumps

The PC uses the selected general-purpose register, accumulator value, immediate field, and branch sub-operation to determine the next instruction address.

---

## `ALU.v`

Implements the processor's Arithmetic Logic Unit.

The CPU retains four arithmetic operations:

```text
ADD
SUB
MULT
DIV
```

Both register and immediate arithmetic instruction families use the ALU.

The 2-bit instruction sub-operation selects the arithmetic function:

```text
00 -> ADD
01 -> SUB
10 -> MULT
11 -> DIV
```

The ALU operates on 8-bit values and produces an 8-bit result.

As a result, arithmetic follows the native width of the processor. Results exceeding the 8-bit range are truncated to the low 8 bits.

---

## `ACCUMULATOR_REGISTER.v`

Implements the CPU's 8-bit accumulator.

The accumulator is the central arithmetic register in the processor datapath.

It can receive values from sources including:

```text
ALU output
Global memory
I/O
Subroutine-related datapaths
```

depending on the processor configuration and active control signals.

Arithmetic results are written back into the accumulator.

---

## `REGISTER_FILE.v`

Implements the eight 8-bit general-purpose registers:

```text
r0
r1
r2
r3
r4
r5
r6
r7
```

The 3-bit instruction register field selects one of these registers.

The selected register is exposed as:

```text
regOut
```

The `copy` instruction writes the accumulator value into a selected register.

Registers are used for:

- Arithmetic operands
- Temporary expression values
- Loop comparisons
- Compiler-generated intermediate values

---

## `GLOBAL_MEMORY.v`

Implements the Business Card CPU's global data memory.

To reduce FPGA resource usage, the card implementation uses:

```text
16 × 8-bit global memory
```

rather than the larger memory used by the original CPU implementation.

The memory stores compiler-allocated variables such as:

```text
n
divisor
remainder
isPrime
run
```

for the prime-number demonstration.

Memory contents are initialized from:

```text
global_memory.hex
```

Global memory supports normal immediate-addressed load and store operations.

Reducing this memory was one of the major resource optimizations required to fit the CPU comfortably into the `10M02`.

---

## `CLOCK_DIVIDER.v`

Divides the FPGA source clock to generate the CPU execution clock.

The Business Card uses the MAX 10's internal oscillator, eliminating the need for an external crystal or oscillator.

The divider allows the CPU to execute slowly enough for changes on the LED output to remain visually observable.

---

## `COPY_SUBOP_CONTROL.v`

Decodes the sub-operation field for the `COPY` instruction family.

The broader instruction family includes operations such as:

```text
copy
rint
```

The Business Card primarily uses standard register-copy behavior.

---

## `LOAD_SUBOP_CONTROL.v`

Decodes the sub-operation field for the `LOAD` instruction family.

The broader ISA defines:

```text
load
loadio
loadr
```

where:

```text
load    -> immediate-addressed global memory
loadio  -> I/O memory
loadr   -> register-indirect global memory
```

Not every load mode is required by the resource-optimized Business Card implementation.

---

## `STORE_SUBOP_CONTROL.v`

Decodes the sub-operation field for the `STORE` instruction family.

The broader ISA defines:

```text
store
storeio
storer
```

For the Business Card, two operations are particularly important:

```text
store
```

writes the accumulator into global data memory.

```text
storeio
```

writes the accumulator to the card's I/O hardware.

The default card firmware uses `storeio` to update the LED output register.

---

## `internal.v`

Wrapper generated for the MAX 10 internal oscillator.

The internal oscillator provides the source clock for the Business Card CPU.

Its output is passed through `CLOCK_DIVIDER.v` before being used as the CPU clock.

Because the oscillator is contained inside the FPGA, the PCB does not require an external clock source.

---

# LED Output Register

The Business Card adds an 8-bit output register specifically for the onboard LEDs.

The register is updated when the CPU executes an I/O store.

Conceptually:

```text
ACC
 |
 | storeio
 v
+--------------+
| LED Register |
+------+-------+
       |
       v
   LED[7:0]
```

The register retains its previous value while the CPU continues executing.

This means intermediate calculations do not appear on the LEDs.

Only values explicitly written by software are displayed.

The default prime-number program uses:

```asm
load 0
storeio 0
```

to load the current prime into the accumulator and latch it onto the LEDs.

---

# Reset Logic

The Business Card contains both manual and automatic reset mechanisms.

The top-level reset is generated from:

```text
Manual Reset
     |
     +------+
            |
            v
          OR ----> CPU Reset
            ^
            |
     +------+
     |
Startup Reset
```

The startup reset is generated from a counter clocked by the FPGA's internal oscillator.

This allows the CPU to begin execution from a known state whenever the card is powered on.

---

# Resource Optimization

The Business Card CPU targets the small:

```text
10M02DCV36C8G
```

MAX 10 FPGA.

Several changes were made relative to the larger CPU implementation to reduce FPGA resource usage.

The most significant was reducing global data memory.

A larger asynchronous memory implementation consumed a substantial portion of the FPGA's logic resources.

Reducing global memory to:

```text
16 bytes
```

allowed the complete processor to fit comfortably while preserving the core CPU architecture.

The final implementation retains:

```text
8-bit datapath
8 general-purpose registers
Accumulator
ADD
SUB
MULT
DIV
Conditional branches
Program memory
Global memory
I/O output
```

The CPU therefore remains a general programmable processor rather than dedicated LED-control logic.

---

# Business Card Firmware

The default program calculates prime numbers at runtime.

The CPU repeatedly tests candidate values and displays each discovered prime on the eight LEDs.

Example output:

```text
Prime       LED[7:0]

2           00000010
3           00000011
5           00000101
7           00000111
11          00001011
13          00001101
17          00010001
19          00010011
```

The program itself is located in:

[`../software/examples/`](../software/examples/)

The machine-code image generated by the software toolchain initializes the CPU's instruction memory.

---

# Building

The RTL is intended for Intel Quartus Prime and targets:

```text
Family: MAX 10
Device: 10M02DCV36C8G
```

The top-level entity is:

```text
CPU_CARD
```

The typical build flow is:

```text
Custom Program
      |
      v
Compiler
      |
      v
Assembler
      |
      v
instruction_ram.hex
      |
      v
Quartus Project
      |
      v
CPU_CARD
      |
      v
MAX 10 Configuration
```

For FPGA programming instructions, see:

[`../docs/PROGRAMMING.md`](../docs/PROGRAMMING.md)

---

# Broader CPU Architecture

The RTL in this directory represents the Business Card implementation.

The project's compiler, assembler, and ISA support features from the broader CPU architecture that may not all be instantiated in this reduced FPGA target.

Examples include:

```text
Subroutine Register File
Function calls
Interrupts
TTY output
Graphics I/O
Register-indirect memory access
```

This allows the software toolchain to remain useful for the larger CPU project while the Business Card uses only the hardware necessary for its standalone demonstration.

---

# Related Documentation

### Architecture

[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)

Detailed explanation of the processor architecture.

### ISA

[`../docs/ISA.md`](../docs/ISA.md)

Complete instruction-set documentation.

### Software

[`../software/`](../software/)

Compiler, assembler, and example programs.

### Hardware

[`../hardware/`](../hardware/)

PCB schematic, layout, Gerbers, BOM, and assembly files.
