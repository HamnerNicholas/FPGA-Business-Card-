import sys
import shlex

if len(sys.argv) < 2:
    print("Usage: python assembler_dual_output.py <source.asm>")
    sys.exit(1)

filename = sys.argv[1]

address_width = 16

# Output files
LOGISIM_TEXT_FILE = "machineCode2.txt"
LOGISIM_DATA_FILE = "globalMem.txt"
LOGISIM_IVT_FILE = "ivt.txt"

QUARTUS_TEXT_FILE = "instruction_ram.hex"
QUARTUS_DATA_FILE = "global_memory.hex"
QUARTUS_IVT_FILE = "ivt.hex"

equivalents = {
    "r0": 0, "r1": 1, "r2": 2, "r3": 3, "r4": 4, "r5": 5, "r6": 6, "r7": 7,
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6, "R7": 7,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
}
labels = {}

ivt_labels = ["INT0", "INT1", "INT2", "INT3", "INT4", "INT5", "INT6", "INT7"]
ivt_list = ["0000" for _ in range(8)]

SRF_OP = 0
ALUI_OP = 1
ALU_OP = 2
IO_OP = 3
COPY_OP = 4
BRANCH_OP = 5
LOAD_OP = 6
STORE_OP = 7

OP_STYLE = "op"
OP_REG_STYLE = "opreg"
OP_IMM_STYLE = "opimm"
OP_REG_IMM_STYLE = "opregimm"

srf_subops = {
    "jsr": (0b00, 2, OP_IMM_STYLE, 0b000),
    "rsr": (0b01, 1, OP_STYLE, 0b000),
    "ssrf": (0b10, 2, OP_REG_STYLE, 0b000),
    "rsrf": (0b11, 2, OP_REG_STYLE, 0b000),
}
alui_subops = {
    "addi": (0b00, 3, OP_REG_IMM_STYLE, 0b001),
    "subi": (0b01, 3, OP_REG_IMM_STYLE, 0b001),
    "multi": (0b10, 3, OP_REG_IMM_STYLE, 0b001),
    "divi": (0b11, 3, OP_REG_IMM_STYLE, 0b001),
}
alu_subops = {
    "add": (0b00, 2, OP_REG_STYLE, 0b010),
    "sub": (0b01, 2, OP_REG_STYLE, 0b010),
    "mult": (0b10, 2, OP_REG_STYLE, 0b010),
    "div": (0b11, 2, OP_REG_STYLE, 0b010),
}
io_subops = {
    "tty": (0b00, 1, OP_STYLE, 0b011),
    "ttya": (0b01, 1, OP_STYLE, 0b011),
    "halt": (0b10, 1, OP_STYLE, 0b011),
}
copy_subops = {
    "copy": (0b00, 2, OP_REG_STYLE, 0b100),
    "rint": (0b01, 1, OP_STYLE, 0b100),
}
branch_subops = {
    "beq": (0b00, 3, OP_REG_IMM_STYLE, 0b101),
    "bne": (0b01, 3, OP_REG_IMM_STYLE, 0b101),
    "blt": (0b10, 3, OP_REG_IMM_STYLE, 0b101),
    "jump": (0b11, 2, OP_IMM_STYLE, 0b101),
}
load_subops = {
    "load": (0b00, 2, OP_IMM_STYLE, 0b110),
    "loadio": (0b01, 2, OP_IMM_STYLE, 0b110),
    "loadr": (0b10, 2, OP_REG_STYLE, 0b110),
}
store_subops = {
    "store": (0b00, 2, OP_IMM_STYLE, 0b111),
    "storeio": (0b01, 2, OP_IMM_STYLE, 0b111),
    "storer": (0b10, 2, OP_REG_STYLE, 0b111),
}

directive_ops = {
    ".org": 2,
    ".word": 2,
    ".define": 3,
    ".text": 1,
    ".data": 1,
    ".ivt": 3,
}

instruction_set = (
    srf_subops
    | alui_subops
    | alu_subops
    | io_subops
    | copy_subops
    | branch_subops
    | load_subops
    | store_subops
)


def lex_line(line):
    lexer = shlex.shlex(line, posix=True)
    lexer.commenters = ";"
    lexer.whitespace_split = True
    return list(lexer)


def parse_fields(line):
    fields = lex_line(line)
    if not fields:
        return fields

    op = fields[0]
    if op in [":", ".define", ".data", ".text", ".org", ".word", ".ivt"]:
        return fields

    reg = fields[1] if len(fields) > 1 else None
    imm = fields[2] if len(fields) > 2 else (fields[1] if len(fields) > 1 else None)
    return op, reg, imm, fields


def directive_validation(fields, line_num):
    op = fields[0]
    if op in directive_ops and len(fields) != directive_ops[op]:
        raise Exception(f"Missing arguments for {op} at line {line_num}")


def validate_instruction(field_length, op, reg, imm, line_number):
    if op not in instruction_set:
        raise Exception(f"'{op}' not a valid instruction on line number {line_number}")

    subop, valid_length, style, op_code = instruction_set[op]

    # tty allows raw string operands and ttya/halt have no extra operands.
    if op in io_subops:
        return

    if field_length != valid_length:
        if style == OP_IMM_STYLE and field_length == 1:
            raise Exception(f"Missing immediate field for '{op}' on line {line_number}")
        if style == OP_REG_STYLE and field_length == 1:
            raise Exception(f"Missing register field for '{op}' on line {line_number}")
        if style == OP_REG_IMM_STYLE and field_length == 2:
            raise Exception(f"Missing register or immediate field for '{op}' on line {line_number}")
        raise Exception(f"Total fields out of range for {op} on line {line_number}")

    if style in (OP_REG_STYLE, OP_REG_IMM_STYLE):
        if reg not in equivalents:
            raise Exception(f"Register field '{reg}' for instruction '{op}' is not valid on line {line_number}")
        reg_value = equivalents[reg]
        if reg_value < 0 or reg_value > 7:
            raise Exception(f"Register index {reg_value} out of range on line {line_number}")

    if style in (OP_IMM_STYLE, OP_REG_IMM_STYLE):
        if imm is None:
            raise Exception(f"Immediate required for '{op}' on line {line_number}")
        try:
            val = int(imm, 0)

        except ValueError:
            if imm in equivalents:
                val = equivalents[imm]

            elif imm in labels:
                return

            else:
                raise Exception(
                    f"Undefined label or constant '{imm}' "
                    f"on line {line_number}"
                )

        if not (-128 <= val <= 255):
            raise Exception(
                f"Immediate value {val} (from '{imm}') "
                f"out of range on line {line_number}"
            )


def encode_instruction(imm_num, subop_num, reg_num, family_op):
    return ((imm_num & 0xFF) << 8) | ((subop_num & 0x3) << 6) | ((reg_num & 0x7) << 3) | (family_op & 0x7)


def fmt_instruction(value):
    return format(value & 0xFFFF, "04x")


def fmt_data(value):
    return format(value & 0xFF, "02x")


def write_logisim_raw(path, words):
    with open(path, "w") as f:
        f.write("v2.0 raw\n")
        if words:
            f.write(" ".join(words) + " ")


def write_quartus_hex(path, words):
    with open(path, "w") as f:
        for word in words:
            f.write(str(word) + "\n")


try:
    with open(filename, "r") as file:
        lines = file.readlines()

    text_addr = 0
    data_addr = 0
    mode = "text"

    # First pass: labels/constants and address counting.
    for line_num, line in enumerate(lines, start=1):
        fields = lex_line(line)
        if not fields:
            continue

        op = fields[0]
        if op == ":":
            if len(fields) < 2:
                raise Exception(f"Missing label name on line {line_num}")
            labels[fields[1]] = (mode, text_addr if mode == "text" else data_addr)
        elif op == "tty" and len(fields) >= 2:
            text_addr += len(fields[1])
        elif op == ".define":
            directive_validation(fields, line_num)
            equivalents[fields[1]] = int(fields[2], 0)
        elif op == ".data":
            mode = "data"
        elif op == ".word" and mode == "data":
            data_addr += 1
        elif op == ".text":
            mode = "text"
        elif op == ".org":
            directive_validation(fields, line_num)
            target_addr = int(fields[1], 0) if fields[1] not in equivalents else equivalents[fields[1]]
            if mode == "text":
                if target_addr < text_addr:
                    raise Exception(f".org cannot move backwards in text on line {line_num}")
                text_addr = target_addr
            elif mode == "data":
                if target_addr < data_addr:
                    raise Exception(f".org cannot move backwards in data on line {line_num}")
                data_addr = target_addr
        elif op in instruction_set:
            text_addr += 1

    text_addr = 0
    data_addr = 0
    mode = "text"

    logisim_text = []
    quartus_text = []
    logisim_data = []
    quartus_data = []

    # Second pass: emit machine code and memory images.
    for line_num, line in enumerate(lines, start=1):
        fields = lex_line(line)
        if not fields:
            continue

        op = fields[0]

        if op == ":":
            continue

        if op in directive_ops:
            directive_validation(fields, line_num)

            if op == ".org":
                target_addr = equivalents[fields[1]] if fields[1] in equivalents else int(fields[1], 0)
                if mode == "text":
                    if target_addr < text_addr:
                        raise Exception(f".org address {target_addr} is behind current text address at line {line_num}")
                    while text_addr < target_addr:
                        logisim_text.append("0000")
                        quartus_text.append("0000")
                        text_addr += 1
                else:
                    if target_addr < data_addr:
                        raise Exception(f".org address {target_addr} is behind current data address at line {line_num}")
                    while data_addr < target_addr:
                        logisim_data.append("00")
                        quartus_data.append("00")
                        data_addr += 1
                continue

            if op == ".define":
                continue

            if op == ".data":
                mode = "data"
                continue

            if op == ".text":
                mode = "text"
                continue

            if op == ".word":
                if mode != "data":
                    raise Exception(f".word used outside of .data section on line {line_num}")
                token = fields[1]
                if len(token) == 1 and token.isprintable() and not token.isdigit():
                    value = ord(token)
                elif token in labels:
                    value = labels[token][1]
                elif token in equivalents:
                    value = equivalents[token]
                else:
                    value = int(token, 0)
                data_word = fmt_data(value)
                logisim_data.append(data_word)
                quartus_data.append(data_word)
                data_addr += 1
                continue

            if op == ".ivt":
                interrupt_index = fields[1]
                interrupt_vector = fields[2]
                if interrupt_index not in ivt_labels:
                    raise Exception(f"Undefined interrupt pin on line {line_num}")
                if interrupt_vector not in labels:
                    raise Exception(f"Undefined label or constant '{interrupt_vector}' on line {line_num}")
                write_index = ivt_labels.index(interrupt_index)
                section, addr = labels[interrupt_vector]
                ivt_list[write_index] = fmt_instruction(addr)
                continue

        parsed = parse_fields(line)
        if not isinstance(parsed, tuple):
            continue
        op_str, reg_str, imm_str, fields = parsed
        validate_instruction(len(fields), op_str, reg_str, imm_str, line_num)

        subop_num = instruction_set[op_str][0]
        family_op = instruction_set[op_str][3]
        reg_num = equivalents[reg_str] if reg_str in equivalents else 0

        if family_op == IO_OP and subop_num == io_subops["tty"][0]:
            if len(fields) < 2:
                raise Exception(f"tty requires a string operand on line {line_num}")
            for char in fields[1]:
                imm_num = ord(char)
                machine_code = encode_instruction(imm_num, 0, 0, family_op)
                word = fmt_instruction(machine_code)
                logisim_text.append(word)
                quartus_text.append(word)
                print(word)
                text_addr += 1
            continue

        if family_op == IO_OP and subop_num == io_subops["ttya"][0]:
            # Logisim version keeps the legacy imm[7] mux-select convention.
            logisim_machine_code = encode_instruction(0x80, subop_num, 0, family_op)
            # Quartus/Verilog version uses the subop control line and does not need imm[7].
            quartus_machine_code = encode_instruction(0x00, subop_num, 0, family_op)

            logisim_word = fmt_instruction(logisim_machine_code)
            quartus_word = fmt_instruction(quartus_machine_code)
            logisim_text.append(logisim_word)
            quartus_text.append(quartus_word)
            print(quartus_word)
            text_addr += 1
            continue

        if imm_str is None:
            imm_num = 0
        elif imm_str in equivalents:
            imm_num = equivalents[imm_str]
        elif imm_str in labels:
            section, target = labels[imm_str]
            if family_op == BRANCH_OP or family_op == SRF_OP:
                imm_num = target - text_addr
                if not (-128 <= imm_num <= 127):
                    raise Exception(
                        f"Relative jump to '{imm_str}' is out of range "
                        f"on line {line_num}: offset {imm_num}"
                    )
            else:
                imm_num = target

                if not (0 <= imm_num <= 255):
                    raise Exception(
                        f"Address of '{imm_str}' is out of range "
                        f"on line {line_num}: address {imm_num}"
                    )
        else:
            imm_num = int(imm_str, 0)

        machine_code = encode_instruction(imm_num, subop_num, reg_num, family_op)
        word = fmt_instruction(machine_code)
        print(word)

        if mode == "text":
            logisim_text.append(word)
            quartus_text.append(word)
            text_addr += 1
        else:
            # Kept for compatibility with old behavior, though instructions should normally live in .text.
            data_word = fmt_data(machine_code)
            logisim_data.append(data_word)
            quartus_data.append(data_word)
            data_addr += 1

    write_logisim_raw(LOGISIM_TEXT_FILE, logisim_text)
    write_logisim_raw(LOGISIM_DATA_FILE, logisim_data)
    write_logisim_raw(LOGISIM_IVT_FILE, ivt_list)

    write_quartus_hex(QUARTUS_TEXT_FILE, quartus_text)
    write_quartus_hex(QUARTUS_DATA_FILE, quartus_data)
    write_quartus_hex(QUARTUS_IVT_FILE, ivt_list)

    print("\nWrote Logisim files:")
    print(f"  {LOGISIM_TEXT_FILE}")
    print(f"  {LOGISIM_DATA_FILE}")
    print(f"  {LOGISIM_IVT_FILE}")
    print("Wrote Quartus files:")
    print(f"  {QUARTUS_TEXT_FILE}")
    print(f"  {QUARTUS_DATA_FILE}")
    print(f"  {QUARTUS_IVT_FILE}")

except FileNotFoundError:
    print("Code file not found.")
    sys.exit(1)
except Exception as e:
    print(f"\nASSEMBLER ERROR: {e}")
    sys.exit(1)