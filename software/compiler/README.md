# Custom 8-Bit CPU Compiler

This directory contains the compiler for the custom high-level language used with the FPGA CPU project.

The compiler translates source programs into assembly for the custom accumulator-based CPU. The generated assembly is then processed by the custom assembler to produce 16-bit machine code for the FPGA instruction memory.

## Compilation Flow

```text
High-Level Source
      |
      v
   compiler.py
      |
      v
  assembly.txt
      |
      v
   Assembler
      |
      v
instruction_ram.hex
      |
      v
Custom FPGA CPU
```

## Usage

```bash
python compiler.py <source_file>
```

Example:

```bash
python compiler.py examples/primes.cpu
```

The compiler writes the generated assembly to:

```text
assembly.txt
```

## Language Overview

The language currently supports:

- Integer variables
- Arrays
- Arithmetic expressions
- Parentheses and operator precedence
- Variable assignment
- Array reads and writes
- Variable-indexed arrays
- `if` statements
- `while` loops
- `for` loops
- Functions
- Function parameters
- Return values
- Function calls
- Inline assembly
- Interrupt declarations
- Numeric printing
- Text output
- Pixel drawing
- CPU halt

The compiler is implemented as a two-pass source translator:

1. **Data allocation pass**
   - Allocates variables and arrays in global memory.
   - Emits the `.data` section.

2. **Code-generation pass**
   - Parses executable statements.
   - Generates CPU assembly into the `.text` section.

---

# Variables

Variables are declared using:

```text
let name = value
```

Example:

```text
let x = 5
let y = 10
let result = 0
```

Variables are assigned sequential addresses in global data memory.

The compiler emits:

```asm
.data
.word 5
.word 10
.word 0
```

and internally records the RAM address assigned to each variable.

## Assignment

```text
result = x + y
```

Expressions are evaluated using temporary CPU registers before the final result is written back into global memory.

---

# Arithmetic

The compiler supports the four core CPU arithmetic operations:

```text
+
-
*
/
```

Example:

```text
result = a + b
result = a - b
result = a * b
result = a / b
```

Operator precedence follows the usual ordering:

```text
* /
```

before:

```text
+ -
```

Parentheses are also supported:

```text
result = (a + b) * c
```

Internally, expressions are converted to postfix notation before assembly generation.

Example:

```text
a + b * c
```

becomes conceptually:

```text
a b c * +
```

This allows the compiler to generate accumulator/register operations in the correct order.

---

# Integer Literals

Integer literals are parsed using Python-style base detection.

Examples:

```text
10
0xFF
0b10101010
```

Immediate operands accepted by helper routines may range from:

```text
-128 through 255
```

depending on the generated instruction.

---

# Conditional Statements

Syntax:

```text
if left == right
    ...
endif
```

Supported comparison operators:

```text
==
!=
<
```

Example:

```text
if remainder == 0
    isPrime = 0
endif
```

The compiler generates unique labels for each condition:

```asm
beq r1 IFTRUE1
jump IFEND1

: IFTRUE1
...

: IFEND1
```

Nested `if` statements are supported through an internal label stack.

---

# While Loops

Syntax:

```text
while left < right
    ...
ewhile
```

Supported comparison operators:

```text
==
!=
<
```

Example:

```text
while x < 10
    x = x + 1
ewhile
```

Nested `while` loops are supported.

The compiler generates labels such as:

```text
WHILESTART1
WHILEBODY1
WHILEEND1
```

and automatically generates the branch back to the start of the loop.

---

# For Loops

Syntax:

```text
for i = 0, i < 10, i++
    ...
efor
```

The initialization value may be a literal or another declared variable.

Supported update forms are:

```text
i++
i--
```

Supported condition operators are:

```text
==
!=
<
```

Example:

```text
for i = 0, i < 10, i++
    A[i] = i
efor
```

The compiler generates labels such as:

```text
FORSTART1
FORBODY1
FOREND1
```

---

# Arrays

Arrays are declared using:

```text
let A[] = 1, 2, 3, 4
```

The values are stored sequentially in global memory.

For example:

```text
let A[] = 10, 20, 30
```

may result in:

```text
A[0] -> RAM[0]
A[1] -> RAM[1]
A[2] -> RAM[2]
```

depending on previously allocated variables.

## Constant Indexing

Constant indexes are resolved at compile time.

```text
x = A[2]
```

can compile directly to:

```asm
load <A base + 2>
```

Likewise:

```text
A[2] = x
```

can use an immediate-address store.

## Variable Indexing

Variable indexes use the CPU's register-indirect memory instructions.

Example:

```text
x = A[i]
```

The compiler calculates:

```text
effective address = A base + i
```

and emits:

```asm
loadr rX
```

Likewise:

```text
A[i] = x
```

uses:

```asm
storer rX
```

This allows runtime array traversal:

```text
for i = 0, i < 10, i++
    A[i] = i
efor
```

The compiler performs compile-time bounds checking for constant indexes.

Runtime variable indexes are not bounds checked.

---

# Functions

Functions are declared using:

```text
func functionName arg1 arg2 = {
    ...
}
```

Example:

```text
func add a b = {
    return a + b
}
```

Up to **three function parameters** are supported.

Parameters are passed using the CPU's Special Register File.

Conceptually:

```text
argument 1 -> SRF1
argument 2 -> SRF2
argument 3 -> SRF3
```

The compiler automatically generates a jump around function definitions so normal program execution begins at `MAINSTART`.

Example generated structure:

```asm
jump MAINSTART

: FUNCadd
...

: MAINSTART
...
```

---

# Function Calls

Syntax:

```text
call add(x,y)
```

Arguments may currently be:

- Declared variables
- Integer literals
- `RETVAL`

Before the `jsr`, arguments are copied into Special Register File locations.

Example conceptually:

```asm
load <x>
copy r1
ssrf r1

load <y>
copy r1
ssrf r2

jsr FUNCadd
```

The compiler verifies that the number of supplied arguments matches the number of declared parameters.

---

# Return Values

Syntax:

```text
return expression
```

Examples:

```text
return x
return x + y
return A[i]
```

Return expressions support:

- Variables
- Literals
- Arithmetic
- Parentheses
- Arrays
- Variable-indexed arrays
- Function parameters
- `RETVAL`

The final result is written to special register `SRF0`.

Conceptually:

```asm
<calculate result>
ssrf r0
rsr
```

A function without an explicit return automatically receives:

```asm
rsr
```

at the end.

---

# RETVAL

`RETVAL` represents the result returned by the most recently called function.

Example:

```text
call add(x,y)
result = RETVAL
```

It may also be:

- Passed to another function
- Printed
- Used in expressions
- Returned from another function

The compiler reads it using:

```asm
rsrf r0
```

---

# Inline Assembly

Raw assembly can be passed directly through the compiler.

Syntax:

```text
asm = {
    load 0
    storeio 0
}
```

The contents of the block are written directly into the generated assembly file.

This is useful for:

- Device-specific I/O
- Custom CPU instructions
- Hardware testing
- Instructions not represented by the high-level language

The FPGA business-card prime-number demo uses inline assembly to write a calculated prime to the LED output register:

```text
asm = {
    load 0
    storeio 0
}
```

---

# Printing Numbers

Syntax:

```text
print value
```

Supported operands include:

```text
print 42
print x
print A[i]
print RETVAL
```

When numeric printing is used, the compiler automatically appends a `printNum` assembly subroutine.

The routine converts an unsigned integer into printable decimal digits and writes them through the CPU's TTY interface.

The subroutine is only emitted when numeric printing is actually used.

---

# Printing Text

Text strings may also be printed using:

```text
print "Hello"
```

Newlines may be embedded using:

```text
\n
```

The compiler tracks a virtual text line width of:

```text
32 characters
```

and converts newline characters into the appropriate amount of TTY spacing to advance to the next display row.

---

# Pixel Drawing

The compiler contains direct support for the CPU's graphics I/O interface.

Syntax:

```text
pixel x, y, color
```

or:

```text
pixel x y color
```

Operands may be:

- Integer literals
- Variables
- Function parameters
- `RETVAL`

The graphics ports are:

```text
16 -> X coordinate
17 -> Y coordinate
18 -> Color
19 -> Draw trigger
```

The compiler generates approximately:

```asm
<load X>
storeio 16

<load Y>
storeio 17

<load color>
storeio 18

addi r0 1
storeio 19
```

Compile-time coordinate checks are performed for literal values:

```text
X:     0-79
Y:     0-59
Color: 0-255
```

---

# Interrupts

The compiler supports declarations for eight interrupt-vector entries:

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

Syntax:

```text
interrupt INT2 = functionName
```

The target must be a previously declared function.

The compiler emits an IVT directive referencing the generated function label.

Example:

```asm
.ivt INT2 FUNCfunctionName
```

---

# Halt

Syntax:

```text
halt
```

Generates:

```asm
halt
```

for CPU implementations that include the halt instruction/control path.

---

# Register Usage

Expression evaluation uses temporary general-purpose registers.

Temporary allocation begins at:

```text
r1
```

and may use registers through:

```text
r7
```

The compiler currently detects register exhaustion:

```text
Register overflow
```

but does **not yet implement register spilling**.

Complex expressions that require more than the available registers therefore produce a compiler error.

---

# Special Register File Usage

The compiler relies on the CPU's Special Register File for function support.

Current convention:

```text
SRF0 -> function return value
SRF1 -> argument 1
SRF2 -> argument 2
SRF3 -> argument 3
```

The exact hardware behavior is defined by the CPU RTL and ISA.

---

# Prime Number Example

The FPGA CPU Business Card uses the following style of program:

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

This program calculates prime numbers at runtime and writes each discovered prime to the business card's LED register.

---

# Current Limitations

The compiler is intentionally lightweight and closely tied to the custom CPU architecture.

Current limitations include:

- No register spilling
- Maximum practical expression depth is limited by the eight CPU registers
- Function calls support at most three parameters
- Runtime array indexes are not bounds checked
- Comparisons currently support only:

```text
==
!=
<
```

- `for` updates currently support only:

```text
++
--
```

- Variables use statically allocated global memory
- No dynamic memory allocation
- No local-variable stack
- No automatic type system
- Arithmetic is limited to the CPU's native integer width
- Some features depend on CPU variants that include the corresponding hardware instructions or I/O peripherals

---

# Architecture Dependency

This compiler targets the broader custom CPU architecture.

Some compiler features may not be available on every physical CPU implementation.

For example, the full architecture supports register-indirect array operations using:

```text
loadr
storer
```

while the resource-reduced FPGA Business Card CPU does not require these instructions for its prime-number demonstration.

Likewise, graphics, TTY output, interrupts, and function-support hardware may be omitted from reduced CPU builds.

The compiler is therefore best understood as the software toolchain for the overall custom CPU architecture rather than only the minimal business-card configuration.

---

# Related Directories

```text
../assembler/
```

Contains the assembler that converts generated assembly into 16-bit machine code.

```text
../examples/
```

Contains example programs written in the high-level language.

```text
../../rtl/
```

Contains the Verilog implementation of the FPGA CPU.
