# Instruction Set Architecture

This document describes the instruction set used by the custom 8-bit FPGA CPU.

The processor uses a fixed-width **16-bit instruction format** with an 8-bit immediate field, 2-bit sub-operation field, 3-bit register field, and 3-bit primary opcode.

## Instruction Format

```text
15                    8 7      6 5       3 2       0
+----------------------+----------+---------+---------+
|      Immediate       |  Subop   | Register| Opcode  |
|        8 bits        |  2 bits  |  3 bits | 3 bits  |
+----------------------+----------+---------+---------+
```

| Field | Width | Description |
|---|---:|---|
| Immediate | 8 bits | Constant, memory address, branch target, or other instruction-specific value |
| Subop | 2 bits | Selects an operation within an opcode family |
| Register | 3 bits | Selects one of eight general-purpose registers |
| Opcode | 3 bits | Selects the primary instruction family |

The eight general-purpose registers are:

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

---

# Opcode Families

The processor uses all eight possible 3-bit primary opcodes.

| Opcode | Binary | Family |
|---:|:---:|---|
| 0 | `000` | Subroutine Register File / subroutine control |
| 1 | `001` | Immediate arithmetic |
| 2 | `010` | Register arithmetic |
| 3 | `011` | I/O / CPU control |
| 4 | `100` | Register copy / interrupt |
| 5 | `101` | Branch / jump |
| 6 | `110` | Load |
| 7 | `111` | Store |

---

# Opcode `000` — Subroutine Register File

This family provides subroutine control and access to the **Subroutine Register File (SRF)**.

| Instruction | Subop | Operands |
|---|:---:|---|
| `jsr` | `00` | immediate |
| `rsr` | `01` | none |
| `ssrf` | `10` | register |
| `rsrf` | `11` | register |

## `jsr`

```asm
jsr address
```

Subop:

```text
00
```

Used to jump to a subroutine.

Example:

```asm
jsr printNum
```

The assembler resolves labels into the 8-bit immediate field.

---

## `rsr`

```asm
rsr
```

Subop:

```text
01
```

Returns from a subroutine.

---

## `ssrf`

```asm
ssrf rX
```

Subop:

```text
10
```

Writes to the Subroutine Register File using the selected register field.

The compiler uses this mechanism when passing function arguments and saving return values.

Example:

```asm
ssrf r1
```

---

## `rsrf`

```asm
rsrf rX
```

Subop:

```text
11
```

Reads from the Subroutine Register File using the selected register field.

Example:

```asm
rsrf r0
```

The compiler uses `r0` in this instruction form when retrieving a function return value.

---

# Opcode `001` — Immediate Arithmetic

Immediate arithmetic instructions use a general-purpose register together with the 8-bit immediate field.

| Instruction | Subop | Operands |
|---|:---:|---|
| `addi` | `00` | register, immediate |
| `subi` | `01` | register, immediate |
| `multi` | `10` | register, immediate |
| `divi` | `11` | register, immediate |

## `addi`

```asm
addi rX value
```

Subop:

```text
00
```

Performs immediate addition.

Example:

```asm
addi r1 5
```

---

## `subi`

```asm
subi rX value
```

Subop:

```text
01
```

Performs immediate subtraction.

Example:

```asm
subi r2 10
```

---

## `multi`

```asm
multi rX value
```

Subop:

```text
10
```

Performs immediate multiplication.

Example:

```asm
multi r3 4
```

---

## `divi`

```asm
divi rX value
```

Subop:

```text
11
```

Performs immediate division.

Example:

```asm
divi r1 2
```

---

# Opcode `010` — Register Arithmetic

Register arithmetic instructions use the selected general-purpose register and the accumulator datapath.

| Instruction | Subop | Operands |
|---|:---:|---|
| `add` | `00` | register |
| `sub` | `01` | register |
| `mult` | `10` | register |
| `div` | `11` | register |

## `add`

```asm
add rX
```

Subop:

```text
00
```

Performs register-based addition.

---

## `sub`

```asm
sub rX
```

Subop:

```text
01
```

Performs register-based subtraction.

---

## `mult`

```asm
mult rX
```

Subop:

```text
10
```

Performs register-based multiplication.

---

## `div`

```asm
div rX
```

Subop:

```text
11
```

Performs register-based division.

---

# Opcode `011` — I/O and CPU Control

This family contains TTY output and CPU halt operations.

| Instruction | Subop | Operands |
|---|:---:|---|
| `tty` | `00` | none |
| `ttya` | `01` | none |
| `halt` | `10` | none |
| — | `11` | reserved |

## `tty`

```asm
tty
```

Subop:

```text
00
```

TTY-related output instruction.

The assembler/compiler may also emit text-oriented TTY output depending on source syntax.

---

## `ttya`

```asm
ttya
```

Subop:

```text
01
```

Outputs the current accumulator value through the TTY interface.

The compiler's numeric printing routine uses `ttya` after converting a number into ASCII.

Example:

```asm
addi r1 0x30
ttya
```

---

## `halt`

```asm
halt
```

Subop:

```text
10
```

Halts CPU execution on implementations that include halt support.

---

# Opcode `100` — Copy / Interrupt

| Instruction | Subop | Operands |
|---|:---:|---|
| `copy` | `00` | register |
| `rint` | `01` | none |
| — | `10` | reserved |
| — | `11` | reserved |

## `copy`

```asm
copy rX
```

Subop:

```text
00
```

Copies the accumulator value into the selected general-purpose register.

Example:

```asm
copy r1
```

---

## `rint`

```asm
rint
```

Subop:

```text
01
```

Interrupt-related control instruction.

---

# Opcode `101` — Branch and Jump

| Instruction | Subop | Operands |
|---|:---:|---|
| `beq` | `00` | register, immediate |
| `bne` | `01` | register, immediate |
| `blt` | `10` | register, immediate |
| `jump` | `11` | immediate |

## `beq`

```asm
beq rX address
```

Subop:

```text
00
```

Branches to the immediate address when the equality condition is satisfied.

Example:

```asm
beq r1 LOOP_END
```

---

## `bne`

```asm
bne rX address
```

Subop:

```text
01
```

Branches when the inequality condition is satisfied.

---

## `blt`

```asm
blt rX address
```

Subop:

```text
10
```

Branches when the selected register satisfies the CPU's less-than comparison condition.

Example:

```asm
blt r1 WHILEBODY1
```

The compiler uses this instruction to implement `<` comparisons in `if`, `while`, and `for` statements.

---

## `jump`

```asm
jump address
```

Subop:

```text
11
```

Performs an unconditional jump to the immediate address.

Example:

```asm
jump LOOP_START
```

---

# Opcode `110` — Load

| Instruction | Subop | Operands |
|---|:---:|---|
| `load` | `00` | immediate |
| `loadio` | `01` | immediate |
| `loadr` | `10` | register |
| — | `11` | reserved |

## `load`

```asm
load address
```

Subop:

```text
00
```

Loads a value from global memory using an immediate address.

Conceptually:

```text
ACC <- RAM[address]
```

Example:

```asm
load 4
```

---

## `loadio`

```asm
loadio address
```

Subop:

```text
01
```

Loads a value from an I/O address into the accumulator.

---

## `loadr`

```asm
loadr rX
```

Subop:

```text
10
```

Performs a register-indirect global-memory load.

The selected register contains the memory address.

Conceptually:

```text
ACC <- RAM[rX]
```

Example:

```asm
loadr r2
```

If:

```text
r2 = 0x05
```

then:

```text
ACC <- RAM[0x05]
```

This instruction was added to support runtime array indexing such as:

```text
A[i]
```

---

# Opcode `111` — Store

| Instruction | Subop | Operands |
|---|:---:|---|
| `store` | `00` | immediate |
| `storeio` | `01` | immediate |
| `storer` | `10` | register |
| — | `11` | reserved |

## `store`

```asm
store address
```

Subop:

```text
00
```

Stores the accumulator into global memory using an immediate address.

Conceptually:

```text
RAM[address] <- ACC
```

Example:

```asm
store 4
```

---

## `storeio`

```asm
storeio address
```

Subop:

```text
01
```

Writes the accumulator to an I/O address.

On the FPGA Business Card, this instruction is used to update the LED output register.

Example:

```asm
load 0
storeio 0
```

This loads the value stored at global-memory address `0` into the accumulator and writes it to the card's LED output.

---

## `storer`

```asm
storer rX
```

Subop:

```text
10
```

Performs a register-indirect global-memory store.

The selected register contains the memory address.

Conceptually:

```text
RAM[rX] <- ACC
```

Example:

```asm
storer r2
```

If:

```text
r2  = 0x05
ACC = 0x2A
```

then:

```text
RAM[0x05] <- 0x2A
```

This instruction allows the compiler to generate runtime array assignments such as:

```text
A[i] = value
```

---

# Complete Instruction Table

| Instruction | Opcode | Subop | Operands |
|---|:---:|:---:|---|
| `jsr` | `000` | `00` | immediate |
| `rsr` | `000` | `01` | none |
| `ssrf` | `000` | `10` | register |
| `rsrf` | `000` | `11` | register |
| `addi` | `001` | `00` | register, immediate |
| `subi` | `001` | `01` | register, immediate |
| `multi` | `001` | `10` | register, immediate |
| `divi` | `001` | `11` | register, immediate |
| `add` | `010` | `00` | register |
| `sub` | `010` | `01` | register |
| `mult` | `010` | `10` | register |
| `div` | `010` | `11` | register |
| `tty` | `011` | `00` | none |
| `ttya` | `011` | `01` | none |
| `halt` | `011` | `10` | none |
| Reserved | `011` | `11` | — |
| `copy` | `100` | `00` | register |
| `rint` | `100` | `01` | none |
| Reserved | `100` | `10` | — |
| Reserved | `100` | `11` | — |
| `beq` | `101` | `00` | register, immediate |
| `bne` | `101` | `01` | register, immediate |
| `blt` | `101` | `10` | register, immediate |
| `jump` | `101` | `11` | immediate |
| `load` | `110` | `00` | immediate |
| `loadio` | `110` | `01` | immediate |
| `loadr` | `110` | `10` | register |
| Reserved | `110` | `11` | — |
| `store` | `111` | `00` | immediate |
| `storeio` | `111` | `01` | immediate |
| `storer` | `111` | `10` | register |
| Reserved | `111` | `11` | — |

---

# Assembler Directives

The assembler also supports several directives that are not CPU instructions.

| Directive | Arguments | Purpose |
|---|---:|---|
| `.org` | 1 | Sets assembly origin |
| `.word` | 1 | Inserts a raw data word |
| `.define` | 2 | Defines a symbolic value |
| `.text` | 0 | Marks the text/code section |
| `.data` | 0 | Marks the data section |
| `.ivt` | 2 | Defines an interrupt-vector-table entry |

## `.org`

```asm
.org address
```

Changes the current assembly origin.

---

## `.word`

```asm
.word value
```

Places a raw value into the generated memory image.

The compiler uses `.word` entries to initialize global variables and arrays.

Example:

```asm
.data
.word 2
.word 0
.word 1
```

---

## `.define`

```asm
.define NAME value
```

Creates a symbolic constant for use by the assembler.

---

## `.text`

```asm
.text
```

Marks the beginning of executable program code.

---

## `.data`

```asm
.data
```

Marks the data-initialization section.

The compiler emits this section before generated program code.

---

## `.ivt`

```asm
.ivt INTn label
```

Defines an interrupt-vector entry.

The compiler supports:

```text
INT0
INT1
INT2
INT3
INT4
INT5
INT6
INT7
```

Example:

```asm
.ivt INT2 FUNCtimerHandler
```

---

# Label Syntax

Labels are written using a leading colon:

```asm
: LOOP_START
```

Branches and jumps reference the label without the colon:

```asm
jump LOOP_START
```

The assembler resolves the label into the appropriate immediate address.

Example:

```asm
: LOOP

load 0
addi r1 1
store 0

jump LOOP
```

---

# Example Program

A small loop might look like:

```asm
.data
.word 0

.text

: LOOP

load 0
copy r1

addi r1 1
copy r1

store 0

jump LOOP
```

The assembler converts each instruction into the CPU's 16-bit instruction format and produces the machine-code image used by the FPGA instruction memory.

---

# Business Card Usage

The FPGA CPU Business Card uses the same core ISA but only requires a subset of the full instruction set for its default prime-number demonstration.

The important instructions used by the card firmware include:

```text
addi
sub
copy
load
store
storeio
beq
blt
jump
```

The broader ISA remains supported by the assembler and other CPU implementations.

For example, the CPU still defines:

```text
MULT
DIV
Subroutine Register File operations
register-indirect load/store
TTY output
interrupt support
```

even when a particular reduced FPGA build does not require every feature.

---

# Related Documentation

[`ARCHITECTURE.md`](ARCHITECTURE.md)

Describes the CPU datapath and overall processor architecture.

[`../software/assembler/`](../software/assembler/)

Contains the assembler implementation for this ISA.

[`../software/compiler/`](../software/compiler/)

Contains the high-level compiler that generates assembly for this ISA.
