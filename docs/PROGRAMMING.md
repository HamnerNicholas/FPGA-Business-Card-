# Programming the FPGA CPU Business Card

The FPGA CPU Business Card uses an Intel/Altera MAX 10 FPGA and is programmed through a compact JTAG pogo-pad interface.

The MAX 10 includes internal non-volatile configuration flash, so the card can be programmed once and then boot automatically whenever power is applied.

## Programming Interface

The card exposes six programming pads:

```text
TCK
TMS
TDI
TDO
2.5V
GND
```

These signals connect to the MAX 10 JTAG interface.

The `2.5V` pad provides the programmer with the target I/O voltage reference.

The card should be powered normally while programming unless the programmer/jig has been specifically designed to provide the required power rails.

## JTAG Connections

Connect the USB-Blaster to the card as follows:

```text
USB-Blaster        FPGA CPU Card

TCK      --------> TCK
TMS      --------> TMS
TDI      --------> TDI
TDO      <-------- TDO
VREF     --------> 2.5V
GND      --------> GND
```

Do not apply 5 V logic directly to the FPGA JTAG pins.

The MAX 10 JTAG interface on this board operates from the 2.5 V I/O rail.

## Pogo-Pin Programming

The card uses exposed copper pads instead of a permanent JTAG header.

A programming jig can use spring-loaded pogo pins aligned with the six pads.

Conceptually:

```text
USB-Blaster
     |
     v
Programming Adapter
     |
     v
Pogo Pins
     |
     v
+----------------------+
| FPGA CPU Business    |
| Card                 |
|                      |
| TMS  TCK             |
| TDO  TDI             |
| 2.5V GND             |
+----------------------+
```

The pogo-pad labels are also printed on the rear silkscreen of the PCB.

## Quartus Programmer

Programming is performed using Intel Quartus Prime Programmer.

Open:

```text
Tools -> Programmer
```

Then select:

```text
Hardware Setup
```

and choose the connected USB-Blaster.

The programming mode should be:

```text
JTAG
```

## Detecting the FPGA

Before writing any configuration data, use:

```text
Auto Detect
```

Quartus should identify the MAX 10 device in the JTAG chain.

For the business card, the expected device is:

```text
10M02DCV36C8G
```

Successful detection confirms that:

- The FPGA is powered
- JTAG reference voltage is present
- TCK is connected
- TMS is connected
- TDI is connected
- TDO is connected
- The USB-Blaster can communicate with the FPGA

If Auto Detect fails, check power and JTAG connections before attempting programming.

## Temporary FPGA Configuration

During development, the FPGA can be configured using a Quartus `.sof` file.

A `.sof` configures the FPGA's volatile configuration memory.

Typical workflow:

```text
Quartus Project
      |
      v
Full Compilation
      |
      v
CPU_CARD.sof
      |
      v
Quartus Programmer
      |
      v
MAX 10
```

In Quartus Programmer:

1. Select the USB-Blaster.
2. Set mode to `JTAG`.
3. Add the generated `.sof` file.
4. Enable `Program/Configure`.
5. Click `Start`.

The design should begin running immediately after configuration completes.

## Volatile Configuration

A `.sof` configuration does not survive complete power loss.

Conceptually:

```text
USB-Blaster
     |
     v
JTAG
     |
     v
FPGA Configuration RAM
```

After power is removed, the configuration is lost.

This mode is convenient during development because it allows fast reprogramming.

## Persistent Configuration

For standalone operation, the MAX 10 internal configuration flash must be programmed.

The internal flash stores the FPGA image when power is removed.

At startup:

```text
Power Applied
     |
     v
MAX 10 Internal Flash
     |
     v
FPGA Configuration RAM
     |
     v
User Mode
     |
     v
Custom CPU Starts
```

No external configuration-memory IC is required.

## Generating a Persistent Programming File

After successfully testing the design using a `.sof`, create a programming file for the MAX 10 internal flash.

In Quartus, use:

```text
File -> Convert Programming Files
```

Select a MAX 10 internal-configuration programming format appropriate for the device.

The resulting programming file can then be loaded into Quartus Programmer and written to the FPGA's internal configuration flash through JTAG.

The exact available options may vary depending on the Quartus version and MAX 10 device.

## Programming the Internal Flash

Once the persistent programming file has been generated:

1. Open `Tools -> Programmer`.
2. Select the USB-Blaster.
3. Set the interface to `JTAG`.
4. Add the generated programming file.
5. Select the internal configuration memory for programming.
6. Enable verification if available.
7. Click `Start`.

Wait until Quartus reports successful completion before removing power or disconnecting the programming fixture.

## Standalone Boot Test

After programming the internal configuration flash, verify that the card boots without the programmer.

1. Disconnect the USB-Blaster.
2. Turn the card off.
3. Wait briefly.
4. Turn the card back on.
5. Observe the LEDs.

The card should automatically:

```text
Power Up
   |
   v
Configure MAX 10
   |
   v
Release Startup Reset
   |
   v
Execute CPU Program
   |
   v
Display Prime Numbers
```

If the prime-number LED sequence begins without Quartus or the USB-Blaster connected, persistent configuration is working correctly.

## Default Business Card Program

The default card firmware calculates prime numbers at runtime and writes each prime to the 8-bit LED output register.

The visible sequence begins:

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
...
97          01100001
```

The program then starts the sequence again.

## Updating the Program

To change the program running on the custom CPU:

```text
High-Level Program
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
instruction_ram.hex
      |
      v
Quartus Project
      |
      v
FPGA Configuration File
```

After updating `instruction_ram.hex`, recompile the Quartus project so the new machine-code image is included in the FPGA configuration.

The updated FPGA image can then be loaded temporarily using a `.sof` or written permanently into internal flash.

## Reset Behavior

The card includes both:

- A physical reset button
- An automatic startup-reset circuit implemented in FPGA logic

The startup reset holds the CPU in reset briefly after FPGA configuration.

This prevents the processor from beginning execution before the clock and internal logic are ready.

Pressing the reset button restarts CPU execution without requiring the FPGA configuration to be reloaded.

## JTAG Configuration Pins

The board includes external biasing for the MAX 10 configuration/JTAG interface.

The configuration network includes pull resistors for signals such as:

```text
TMS
TDI
TCK
JTAGEN
nCONFIG
nSTATUS
CONF_DONE
```

These ensure deterministic behavior during power-up and programming.

The dedicated JTAG pins remain reserved for programming rather than being reused as ordinary GPIO.

## Troubleshooting

### USB-Blaster Does Not Appear

Check:

- USB connection
- USB-Blaster driver installation
- Quartus Hardware Setup

The programmer should appear as a selectable hardware device.

### Auto Detect Does Not Find the MAX 10

Check:

- Card power switch
- Battery voltage
- 1.2 V rail
- 2.5 V rail
- GND connection
- 2.5 V JTAG reference
- TCK
- TMS
- TDI
- TDO
- Pogo-pin alignment

### Programming Works but the Card Does Not Boot After Power Cycle

The FPGA was probably configured using only a `.sof`.

A `.sof` programs volatile configuration memory.

Program the MAX 10 internal configuration flash for persistent startup.

### FPGA Configures but CPU Does Not Run

Check:

- `instruction_ram.hex` was included before compilation
- Reset input is not being held active
- Internal oscillator is enabled
- Clock divider is operating
- CPU startup-reset logic eventually releases reset

## Safety Notes

Before connecting a programming adapter:

- Verify the adapter pinout.
- Verify GND orientation.
- Verify the target voltage reference.
- Avoid applying 5 V to the 2.5 V JTAG interface.
- Do not connect programming pins while the pogo adapter is misaligned.
- Avoid shorting adjacent pads with pogo pins.

## Related Documentation

[`ARCHITECTURE.md`](ARCHITECTURE.md)

Describes the processor architecture and FPGA implementation.

[`ISA.md`](ISA.md)

Documents the custom instruction set.

[`../software/`](../software/)

Contains the compiler, assembler, and example programs.

[`../hardware/`](../hardware/)

Contains the schematic, PCB source, Gerbers, BOM, and placement files.
