# Example Programs

This directory contains example programs written for the custom 8-bit CPU.

## Prime Number Generator

The primary demonstration program for the FPGA CPU Business Card is the prime-number generator.

Rather than storing a predefined LED sequence, the processor calculates prime numbers at runtime and displays each discovered prime on the card's eight LEDs as an 8-bit binary value.

The sequence begins:

```text
Decimal     Binary

2           00000010
3           00000011
5           00000101
7           00000111
11          00001011
13          00001101
17          00010001
19          00010011
23          00010111
29          00011101
31          00011111
...
97          01100001
```

After reaching the configured upper limit, the program begins again at 2.

## Prime Detection

The card demonstration determines whether a candidate number is divisible by a potential divisor using repeated subtraction.

Conceptually:

```text
remainder = candidate

while divisor < remainder
    remainder = remainder - divisor
ewhile
```

If the final remainder equals the divisor, the remainder is converted to zero:

```text
if remainder == divisor
    remainder = 0
endif
```

A zero remainder indicates that the candidate is divisible by the divisor and therefore is not prime.

## LED Output

When a prime number is discovered, the program executes:

```text
asm = {
    load 0
    storeio 0
}
```

The candidate number is stored at global-memory address `0`.

`load 0` places the prime number into the accumulator, and `storeio 0` writes the accumulator value into the business card's 8-bit LED output register.

The LED register holds its value while the CPU searches for the next prime.

As a result, every value displayed on the LEDs represents a prime number that was calculated by the processor at runtime.

## Why Prime Numbers?

Prime generation provides a compact demonstration of several CPU features:

- Arithmetic
- Subtraction
- Comparisons
- Nested loops
- Conditional branches
- Global memory
- I/O operations
- Program control flow

It also provides an immediately visible demonstration that the LEDs are being controlled by software executing on the custom CPU rather than by dedicated LED animation logic.

## Running an Example

The software flow is:

```text
Example Program
      |
      v
   Compiler
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
FPGA CPU
```

The generated instruction-memory file is then included in the Quartus project used to configure the MAX 10 FPGA.
