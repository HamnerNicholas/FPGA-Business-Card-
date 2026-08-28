import sys
import shlex
from collections import deque
import re

if len(sys.argv) < 2:
    print("Usage: python compiler.py <filename>")
    sys.exit(1)

filename = sys.argv[1]


variables = {}
variable_contents = []
variable_address = 0
valid_operators = ["+", "-", "*", "/"]
arrays = {}
array_values = []
in_asm_block = False
function_names = {}
in_func_block = False
emitted_main_jump = False
function_has_return = False
function_params = {}
current_function_params = {}

GFX_X_PORT = 16
GFX_Y_PORT = 17
GFX_COLOR_PORT = 18
GFX_DRAW_PORT = 19

TEXT_LINE_WIDTH = 32

ivt_labels = ["INT0", "INT1", "INT2", "INT3", "INT4", "INT5", "INT6", "INT7"]
ivt_list = ["0000" for _ in range(8)]

# helpers for data translation
def parse_integer_literal(token):
    try:
        return int(token, 0)
    except ValueError:
        return None

def is_integer_literal(token):
    return parse_integer_literal(token) is not None

# helper to emit the rest of a string when using the newline char "\n"
def emit_tty_text(text, out_file, current_column):
    parts = text.split("\\n")

    for index, part in enumerate(parts):
        if part:
            out_file.write(f'tty "{part}"\n')
            current_column = (
                current_column + len(part)
            ) % TEXT_LINE_WIDTH

        # Every separator between split sections represents one newline.
        if index < len(parts) - 1:
            if current_column == 0:
                spaces_remaining = TEXT_LINE_WIDTH
            else:
                spaces_remaining = TEXT_LINE_WIDTH - current_column

            out_file.write(
                f'tty "{" " * spaces_remaining}"\n'
            )

            current_column = 0

    return current_column

# helper to load the acc with a value specified by an instruction
def emit_operand_to_acc(
    operand,
    variables,
    out_file,
    line_num
):
    literal_value = parse_integer_literal(operand)

    if literal_value is not None:
        if literal_value < -128 or literal_value > 255:
            raise Exception(
                f"Immediate value '{operand}' out of range "
                f"on line {line_num}"
            )

        out_file.write(f"addi r0 {operand}\n")
        return

    if operand == "RETVAL":
        out_file.write("rsrf r0\n")
        return

    if operand in current_function_params:
        srf_num = current_function_params[operand]
        out_file.write(f"rsrf r{srf_num}\n")
        return

    if operand in variables:
        out_file.write(f"load {variables[operand]}\n")
        return

    raise Exception(
        f"Invalid pixel operand '{operand}' on line {line_num}"
    )

# Math expression conversion
def parse_to_postfix(fields_slice, variables):
    precedence = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2
    }

    output_queue = []
    operator_stack = []

    for token in fields_slice:
        # Check if token is a number, variable, or array element
        if token.isdigit() or token in variables or ("[" in token and "]" in token) or token == "RETVAL" or token in current_function_params or token in current_function_params:
            output_queue.append(token)

        elif token == "(":
            operator_stack.append(token)

        elif token == ")":
            while operator_stack and operator_stack[-1] != "(":
                output_queue.append(operator_stack.pop())

            if operator_stack and operator_stack[-1] == "(":
                operator_stack.pop()

        elif token in precedence:
            while (
                operator_stack
                and operator_stack[-1] in precedence
                and precedence[operator_stack[-1]] >= precedence[token]
            ):
                output_queue.append(operator_stack.pop())

            operator_stack.append(token)

    while operator_stack:
        output_queue.append(operator_stack.pop())

    return output_queue

# Checking if registers overflow, needs actual register spilling algorithm
def check_register_overflow(reg_num, line_num):
    if reg_num > 7:
        raise Exception(f"Register overflow on line {line_num}")

# Helper function for loading variables to registers
def load_operand_to_reg(operand, reg, variables, out_file):
    if operand == "RETVAL":
        out_file.write("rsrf r0\n")
        out_file.write(f"copy {reg}\n")

    elif operand in current_function_params:
        srf_num = current_function_params[operand]
        out_file.write(f"rsrf r{srf_num}\n")
        out_file.write(f"copy {reg}\n")

    elif operand in variables:
        out_file.write(f"load {variables[operand]}\n")
        out_file.write(f"copy {reg}\n")

    elif is_integer_literal(operand):
        out_file.write(f"addi r0 {operand}\n")
        out_file.write(f"copy {reg}\n")

    elif operand.startswith("r"):
        if operand != reg:
            out_file.write(f"addi {operand} 0\n")
            out_file.write(f"copy {reg}\n")

    else:
        raise Exception(f"Invalid operand '{operand}'")

# Assembly code for printing ascii numbers
def emit_print_num_subroutine(out_file):
    out_file.write("""
: printNum

; Load number to print


rsrf r0
copy r0


; Clear counters


rsrf r7
copy r1        ; hundreds
copy r2        ; tens
copy r3        ; constant zero

                   
; Count hundreds


: countHundreds

rsrf r7
addi r7 100

blt r0 doneHundreds

subi r0 100
copy r0

addi r1 1
copy r1

jump countHundreds

: doneHundreds
                   
; Count tens

: countTens

rsrf r7
addi r7 10

blt r0 doneTens

subi r0 10
copy r0

addi r2 1
copy r2

jump countTens

: doneTens

addi r0 0
copy r6

; Print hundreds digit

rsrf r7
beq r1 skipHundreds

addi r1 0x30
ttya

: skipHundreds

; Print tens digit

rsrf r7
beq r1 checkTensZero

addi r2 0x30
ttya
jump printOnes

: checkTensZero

rsrf r7
beq r2 printOnes

addi r2 0x30
ttya

; Print ones digit


: printOnes

addi r6 0x30
ttya

tty " "

rsr
""")

# For loop increment code control
def emit_increment(update_tokens, variables, out_file, line_num):
    if len(update_tokens) != 1:
        raise Exception(f"Invalid for-loop update on line {line_num}")

    token = update_tokens[0]

    if token.endswith("++"):
        var = token[:-2]
        op = "addi"
    elif token.endswith("--"):
        var = token[:-2]
        op = "subi"
    else:
        raise Exception(f"Invalid for-loop update '{token}' on line {line_num}")

    if var not in variables:
        raise Exception(f"Variable '{var}' not declared on line {line_num}")

    out_file.write(f"load {variables[var]}\n")
    out_file.write("copy r1\n")
    out_file.write(f"{op} r1 1\n")
    out_file.write("copy r1\n")
    out_file.write(f"store {variables[var]}\n")

def parse_func_header(name_token):
    # name_token example: add(a,b)
    if "(" not in name_token:
        return name_token, []

    func_name = name_token[:name_token.index("(")]
    params_text = name_token[name_token.index("(") + 1:name_token.index(")")]

    if params_text.strip() == "":
        return func_name, []

    params = [p.strip() for p in params_text.split(",")]
    return func_name, params

# Array access helpers
def parse_array_access(token, arrays, line_num):
    """Parse A[5] or A[i] into (array_name, index_token)."""
    if "[" not in token or "]" not in token:
        raise Exception(f"Invalid array access '{token}' on line {line_num}")

    array_name = token[:token.index("[")]
    start_index = token.index("[") + 1
    end_index = token.index("]")
    index_token = token[start_index:end_index].strip()

    if array_name not in arrays:
        raise Exception(f"Array '{array_name}' not declared on line {line_num}")

    if index_token == "":
        raise Exception(f"Missing array index in '{token}' on line {line_num}")

    return array_name, index_token


def emit_array_load(token, target_reg, arrays, variables, out_file, line_num):
    """Load an array element into ACC and copy it into target_reg."""
    array_name, index_token = parse_array_access(token, arrays, line_num)

    base = arrays[array_name]["addr"]
    length = arrays[array_name]["length"]
    index_value = parse_integer_literal(index_token)

    # Constant index: keep the existing immediate-address form.
    if index_value is not None:
        if index_value < 0 or index_value >= length:
            raise Exception(
                f"Array index {index_value} out of bounds for '{array_name}' "
                f"on line {line_num}"
            )

        final_address = base + index_value
        out_file.write(
            f"; accessing {array_name}[{index_value}] at memory location {final_address}\n"
        )
        out_file.write(f"load {final_address}\n")
        out_file.write(f"copy {target_reg}\n")
        return

    # Variable index: use register-indirect addressing.
    if index_token in variables:
        out_file.write(
            f"; accessing {array_name}[{index_token}] using register-indirect load\n"
        )

        # ACC = runtime index
        out_file.write(f"load {variables[index_token]}\n")

        # target_reg = runtime index
        out_file.write(f"copy {target_reg}\n")

        # target_reg = ARRAY_BASE + runtime index
        if base != 0:
            out_file.write(f"addi {target_reg} {base}\n")
            out_file.write(f"copy {target_reg}\n")

        # ACC = RAM[target_reg]
        out_file.write(f"loadr {target_reg}\n")

        # Preserve the loaded value in the expression register.
        out_file.write(f"copy {target_reg}\n")
        return

    raise Exception(
        f"Invalid array index '{index_token}' in '{token}' on line {line_num}"
    )


# Compiler Code
try:
    with open(filename, "r") as file, open("assembly.txt", "w") as out_file:
        lines = file.readlines()

        # FIRST PASS: Variable Allocations


        print(".data")
        out_file.write(".data\n")

        for line_num, line in enumerate(lines, start=1):
            lexer = shlex.shlex(line, posix=True)
            lexer.commenters = ";"
            lexer.whitespace_split = True
            fields = list(lexer)

            if not fields:
                continue

            if fields[0] == "let":
                if len(fields) < 4 or fields[2] != "=":
                    raise Exception(f"Invalid variable declaration on line {line_num}")
                
                var_name = fields[1]
                var_value = fields[3]

                if var_name in variables:
                    raise Exception(f"Variable '{var_name}' already declared on line {line_num}")
                
                # arrays: let x[] = 1, 2, 3
                if fields[1].endswith("[]"):
                    var_name = fields[1]
                    array_values = fields[3:]
                    array_values = [int(v.strip(" ,")) for v in array_values]

                    array_name = var_name.replace("[]", "")

                    arrays[array_name] = {
                        "type": "array",
                        "addr": variable_address,
                        "length": len(array_values)
                    }

                    for v in array_values:
                        out_file.write(f".word {v}\n")
                        variable_address += 1
                # regular variable declaration 
                else:
                    variable_contents.append(var_value)

                    out_file.write(f".word {var_value}\n")

                    variables[var_name] = variable_address
                    variable_address += 1

        # SECOND PASS: Code Generation

        print("\n.text")
        out_file.write("\n.text\n")

        label_counter = 0
        if_stack = []
        while_stack = []
        for_stack = []

        uses_print_num = False

        tty_column = 0

        for line_num, line in enumerate(lines, start=1):
            line = line.replace(",", " , ")
            lexer = shlex.shlex(line, posix=True)
            lexer.commenters = ";"
            lexer.whitespace_split = True
            fields = list(lexer)

            if not fields:
                continue

            reg_num = 1

            # Skip declarations during code generation
            if fields[0] == "let":
                continue


            # PIXEL DRAWING
            if fields[0] == "pixel":
                # Allows either:
                # pixel 10 20 224
                # pixel 10, 20, 224
                pixel_args = [
                    field
                    for field in fields[1:]
                    if field != ","
                ]

                if len(pixel_args) != 3:
                    raise Exception(
                        f"Invalid pixel statement on line {line_num}. "
                        "Expected: pixel x, y, color"
                    )

                x_operand = pixel_args[0]
                y_operand = pixel_args[1]
                color_operand = pixel_args[2]

                # Compile-time bounds checking when values are constants.
                x_value = parse_integer_literal(x_operand)
                y_value = parse_integer_literal(y_operand)
                color_value = parse_integer_literal(color_operand)

                if x_value is not None and not (0 <= x_value < 80):
                    raise Exception(
                        f"Pixel X coordinate {x_value} out of range "
                        f"on line {line_num}; expected 0-79"
                    )

                if y_value is not None and not (0 <= y_value < 60):
                    raise Exception(
                        f"Pixel Y coordinate {y_value} out of range "
                        f"on line {line_num}; expected 0-59"
                    )

                if color_value is not None and not (0 <= color_value <= 255):
                    raise Exception(
                        f"Pixel color {color_value} out of range "
                        f"on line {line_num}; expected 0-255"
                    )

                out_file.write(
                    f"\n; Draw pixel ({x_operand}, {y_operand}) "
                    f"with color {color_operand}\n"
                )

                # Set X.
                emit_operand_to_acc(
                    x_operand,
                    variables,
                    out_file,
                    line_num
                )
                out_file.write(f"storeio {GFX_X_PORT}\n")

                # Set Y.
                emit_operand_to_acc(
                    y_operand,
                    variables,
                    out_file,
                    line_num
                )
                out_file.write(f"storeio {GFX_Y_PORT}\n")

                # Set color.
                emit_operand_to_acc(
                    color_operand,
                    variables,
                    out_file,
                    line_num
                )
                out_file.write(f"storeio {GFX_COLOR_PORT}\n")

                # Trigger the draw command.
                out_file.write("addi r0 1\n")
                out_file.write(f"storeio {GFX_DRAW_PORT}\n")

                continue
            
            # FUNCTION CREATION
            # func test = {
            #...
            #}

            # Check if in function block
            if in_func_block:
                if "}" in fields:
                    if not function_has_return:
                        out_file.write("rsr\n")

                    current_function_params = {}
                    function_has_return = False
                    in_func_block = False
                    continue
            
            # Find start of function
            if fields[0] == "func":
                if "=" not in fields or "{" not in fields:
                    raise Exception(f"Invalid function syntax on line: {line_num}")

                eq_index = fields.index("=")
                func_name = fields[1]
                params = fields[2:eq_index]

                if len(params) > 3:
                    raise Exception(f"Function '{func_name}' has too many parameters on line {line_num}")

                if not emitted_main_jump:
                    out_file.write("jump MAINSTART\n")
                    emitted_main_jump = True

                function_names[func_name] = f"FUNC{func_name}"
                function_params[func_name] = params

                current_function_params.clear()
                current_function_params.update({
                    param: index + 1
                    for index, param in enumerate(params)
                })

                in_func_block = True

                out_file.write(f"\n; Start of function {func_name}\n")
                out_file.write(f": FUNC{func_name}\n")
                continue

            # Find start of the main code
            if (
                emitted_main_jump
                and not in_func_block
                and fields[0] not in ["func", "}"]
            ):
                out_file.write("\n: MAINSTART\n")
                emitted_main_jump = False

            # FUNCTION CALL GENERATION
            if fields[0] == "call":
                call_text = " ".join(fields[1:]).replace(" ", "")

                if "(" in call_text:
                    func_name = call_text[:call_text.index("(")]
                    args_text = call_text[call_text.index("(") + 1:call_text.index(")")]

                    if args_text == "":
                        args = []
                    else:
                        args = args_text.split(",")
                else:
                    func_name = fields[1]
                    args = []

                if func_name not in function_names:
                    raise Exception(f"Function '{func_name}' not declared on line {line_num}")

                expected_params = function_params.get(func_name, [])

                if len(args) != len(expected_params):
                    raise Exception(
                        f"Function '{func_name}' expects {len(expected_params)} arguments, got {len(args)} on line {line_num}"
                    )

                for index, arg in enumerate(args):
                    srf_num = index + 1

                    if arg in variables:
                        out_file.write(f"load {variables[arg]}\n")
                        out_file.write("copy r1\n")
                        out_file.write(f"ssrf r{srf_num}\n")

                    elif arg == "RETVAL":
                        out_file.write("rsrf r0\n")
                        out_file.write("copy r1\n")
                        out_file.write(f"ssrf r{srf_num}\n")

                    elif arg.isdigit():
                        out_file.write(f"addi r0 {arg}\n")
                        out_file.write("copy r1\n")
                        out_file.write(f"ssrf r{srf_num}\n")

                    else:
                        raise Exception(f"Invalid argument '{arg}' on line {line_num}")

                out_file.write(f"jsr {function_names[func_name]}\n")
                continue

                        # Interrupt Declaration
            # interrup INT2 = function
            if fields[0] == "interrupt":
                if len(fields) != 4:
                    raise Exception(
                        f"Invalid interrupt declaration on line {line_num}. "
                        "Expected: interrupt INT_CODE = LABEL"
                        )

                if fields[1] not in ivt_labels:
                    raise Exception(
                        f"{fields[1]} is not a valid interrupt code: INT0 - INT7 on line: {line_num}")
                if fields[3] not in function_names:
                    raise Exception(
                        f"{fields[3]} is not a valid function name on line: {line_num}")

                out_file.write(f".ivt {fields[1]} FUNC{fields[3]}")

            # ASSEMBLY PASS THROUGH GENERATION
            # asm = {
            #....
            #}           
            # inside the assembly block
            if in_asm_block:
                # Check if this line marks the end of the block
                if "}" in fields:
                    in_asm_block = False
                    continue
                
                out_file.write(f"{line.strip()}\n")
                continue

            # Find start of block
            if fields[0] == "asm":
                # Check for standard opening syntax on this line
                if len(fields) < 3 or fields[1] != "=" or fields[2] != "{":
                    raise Exception(f"Invalid syntax for assembly passthrough on line: {line_num}")
                
                # If the block opens and closes on the exact same line
                if fields[-1] == "}":
                    for field in fields[3:-1]:
                        if field != ",":  
                            out_file.write(f"{field} ")
                    out_file.write("\n")
                else:
                    # Enable multiline block
                    in_asm_block = True
                continue


            # FUNCTION RETURN GENERATION
            if fields[0] == "return":
                function_has_return = True

                if len(fields) < 2:
                    raise Exception(f"Missing return value on line {line_num}")

                for field in fields[1:]:
                    result = re.sub(r"\[.*?\]", "", field)

                    if (
                        field not in variables
                        and field != "RETVAL"
                        and not field.isdigit()
                        and field not in valid_operators
                        and field not in ["(", ")"]
                        and result not in arrays
                        and field not in current_function_params
                    ):
                        raise Exception(f"Invalid return token '{field}' on line {line_num}")

                postfix_tokens = parse_to_postfix(fields[1:], variables)

                stack = deque()
                reg_num = 1

                for token in postfix_tokens:
                    result = re.sub(r"\[.*?\]", "", token)

                    if token.isdigit() or token in variables or token == "RETVAL" or token in current_function_params:
                        target_reg = f"r{reg_num}"
                        check_register_overflow(reg_num, line_num)

                        load_operand_to_reg(token, target_reg, variables, out_file)

                        stack.append(target_reg)
                        reg_num += 1

                    elif token in valid_operators:
                        right_reg = stack.pop()
                        left_reg = stack.pop()

                        out_file.write(f"addi {right_reg} 0\n")

                        match token:
                            case "+":
                                out_file.write(f"add {left_reg}\n")
                            case "-":
                                out_file.write(f"sub {left_reg}\n")
                            case "*":
                                out_file.write(f"mult {left_reg}\n")
                            case "/":
                                out_file.write(f"div {left_reg}\n")

                        out_file.write(f"copy {left_reg}\n")
                        stack.append(left_reg)

                    elif result in arrays:
                        target_reg = f"r{reg_num}"
                        check_register_overflow(reg_num, line_num)

                        emit_array_load(
                            token,
                            target_reg,
                            arrays,
                            variables,
                            out_file,
                            line_num
                        )

                        stack.append(target_reg)
                        reg_num += 1

                    else:
                        raise Exception(f"Invalid return token '{token}' on line {line_num}")

                final_reg = stack.pop()

                out_file.write(f"addi {final_reg} 0\n")
                out_file.write("ssrf r0\n")
                out_file.write("rsr\n")
                continue

            # FOR LOOP GENERATION
            if fields[0] == "for":
                label_counter += 1

                start_label = f"FORSTART{label_counter}"
                body_label = f"FORBODY{label_counter}"
                end_label = f"FOREND{label_counter}"

                comma1 = fields.index(",")
                comma2 = fields.index(",", comma1 + 1)

                init_tokens = fields[1:comma1]
                cond_tokens = fields[comma1 + 1:comma2]
                update_tokens = fields[comma2 + 1:]

                # Initialization: i = 0

                if len(init_tokens) != 3 or init_tokens[1] != "=":
                    raise Exception(f"Invalid for-loop initialization on line {line_num}")

                init_var = init_tokens[0]
                init_value = init_tokens[2]

                if init_var not in variables:
                    raise Exception(f"Variable '{init_var}' not declared on line {line_num}")

                if init_value in variables:
                    out_file.write(f"load {variables[init_value]}\n")
                    out_file.write("copy r1\n")
                    out_file.write(f"store {variables[init_var]}\n")
                elif init_value.isdigit():
                    out_file.write(f"addi r0 {init_value}\n")
                    out_file.write("copy r1\n")
                    out_file.write(f"store {variables[init_var]}\n")
                else:
                    raise Exception(f"Invalid for-loop init value '{init_value}' on line {line_num}")

                # Condition: i < 10

                if len(cond_tokens) != 3:
                    raise Exception(f"Invalid for-loop condition on line {line_num}")

                left_comp = cond_tokens[0]
                comp_op = cond_tokens[1]
                right_comp = cond_tokens[2]

                for_stack.append((start_label, end_label, update_tokens))

                out_file.write(f"\n: {start_label}\n")

                # r2 = left side
                if left_comp in variables:
                    out_file.write(f"load {variables[left_comp]}\n")
                    out_file.write("copy r5\n")
                elif left_comp.isdigit():
                    out_file.write(f"addi r0 {left_comp}\n")
                    out_file.write("copy r5\n")
                else:
                    raise Exception(f"Invalid comparison value '{left_comp}' on line {line_num}")

                # ACC = right side
                if right_comp in variables:
                    out_file.write(f"load {variables[right_comp]}\n")
                elif right_comp.isdigit():
                    out_file.write(f"addi r0 {right_comp}\n")
                else:
                    raise Exception(f"Invalid comparison value '{right_comp}' on line {line_num}")

                match comp_op:
                    case "==":
                        out_file.write(f"beq r5 {body_label}\n")
                    case "!=":
                        out_file.write(f"bne r5 {body_label}\n")
                    case "<":
                        out_file.write(f"blt r5 {body_label}\n")
                    case _:
                        raise Exception(f"Unsupported comparison operator '{comp_op}' on line {line_num}")

                out_file.write(f"jump {end_label}\n")
                out_file.write(f": {body_label}\n")

                continue

            # END FOR LOOP GENERATION
            elif fields[0] == "efor":
                if not for_stack:
                    raise Exception(f"efor without matching for on line {line_num}")

                start_label, end_label, update_tokens = for_stack.pop()

                emit_increment(update_tokens, variables, out_file, line_num)

                out_file.write(f"jump {start_label}\n")
                out_file.write(f": {end_label}\n")
                continue
            
            # WHILE LOOP GENERATION
            if fields[0] == "while":
                if len(fields) < 4:
                    raise Exception(f"Invalid while statement on line {line_num}")

                label_counter += 1

                left_comp = fields[1]
                comp_op = fields[2]
                right_comp = fields[3]

                start_label = f"WHILESTART{label_counter}"
                body_label = f"WHILEBODY{label_counter}"
                end_label = f"WHILEEND{label_counter}"

                while_stack.append((start_label, end_label))

                out_file.write(f"\n: {start_label}\n")

                left_reg = "r1"
                right_backup = "r2"

                if right_comp in variables:
                    out_file.write(f"load {variables[right_comp]}\n")
                    out_file.write(f"copy {right_backup}\n")
                elif right_comp.isdigit():
                    out_file.write(f"addi r0 {right_comp}\n")
                    out_file.write(f"copy {right_backup}\n")
                else:
                    raise Exception(f"Invalid comparison value '{right_comp}' on line {line_num}")

                if left_comp in variables:
                    out_file.write(f"load {variables[left_comp]}\n")
                    out_file.write(f"copy {left_reg}\n")
                elif left_comp.isdigit():
                    out_file.write(f"addi r0 {left_comp}\n")
                    out_file.write(f"copy {left_reg}\n")
                else:
                    raise Exception(f"Invalid comparison value '{left_comp}' on line {line_num}")

                out_file.write(f"addi {right_backup} 0\n")

                match comp_op:
                    case "==":
                        out_file.write(f"beq {left_reg} {body_label}\n")
                    case "!=":
                        out_file.write(f"bne {left_reg} {body_label}\n")
                    case "<":
                        out_file.write(f"blt {left_reg} {body_label}\n")
                    case _:
                        raise Exception(f"Unsupported comparison operator '{comp_op}' on line {line_num}")

                out_file.write(f"jump {end_label}\n")
                out_file.write(f": {body_label}\n")
                continue
            
            # END WHILE LOOP GENERATION
            elif fields[0] == "ewhile":
                if not while_stack:
                    raise Exception(f"ewhile without matching while on line {line_num}")

                start_label, end_label = while_stack.pop()

                out_file.write(f"jump {start_label}\n")
                out_file.write(f": {end_label}\n")
                continue
            
            # IF STATEMENT GENERATION
            if fields[0] == "if":
                if len(fields) < 4:
                    raise Exception(f"Invalid if statement on line {line_num}")

                label_counter += 1

                left_comp = fields[1]
                comp_op = fields[2]
                right_comp = fields[3]

                true_label = f"IFTRUE{label_counter}"
                end_label = f"IFEND{label_counter}"
                if_stack.append(end_label)

                left_reg = "r1"
                right_backup = "r2"

                # Load RIGHT side into ACC, then save it into r2
                if right_comp in variables:
                    out_file.write(f"load {variables[right_comp]}\n")
                    out_file.write(f"copy {right_backup}\n")
                elif right_comp.isdigit():
                    out_file.write(f"addi r0 {right_comp}\n")
                    out_file.write(f"copy {right_backup}\n")
                else:
                    raise Exception(f"Invalid comparison value '{right_comp}' on line {line_num}")

                # Load LEFT side into ACC, then save it into r1
                if left_comp in variables:
                    out_file.write(f"load {variables[left_comp]}\n")
                    out_file.write(f"copy {left_reg}\n")
                elif left_comp.isdigit():
                    out_file.write(f"addi r0 {left_comp}\n")
                    out_file.write(f"copy {left_reg}\n")
                else:
                    raise Exception(f"Invalid comparison value '{left_comp}' on line {line_num}")

                # Restore RIGHT side into ACC
                out_file.write(f"addi {right_backup} 0\n")

                out_file.write("\n; --- IF Statement Condition Check ---\n")

                match comp_op:
                    case "==":
                        out_file.write(f"beq {left_reg} {true_label}\n")
                    case "!=":
                        out_file.write(f"bne {left_reg} {true_label}\n")
                    case "<":
                        out_file.write(f"blt {left_reg} {true_label}\n")
                    case _:
                        raise Exception(f"Unsupported comparison operator '{comp_op}' on line {line_num}")

                out_file.write(f"jump {end_label}\n\n")
                out_file.write(f": {true_label}\n")
                continue

            # END IF GENERATION    
            elif fields[0] == "endif":
                if not if_stack:
                    raise Exception(f"endif without matching if on line {line_num}")

                end_label = if_stack.pop()
                out_file.write(f"\n: {end_label}\n")
                continue

            # HALT GENERATION
            if fields[0] == "halt":
                out_file.write("halt\n")
                continue
            
            # PRINT GENERATION
            if fields[0] == "print":
                if len(fields) < 2:
                    raise Exception(f"Missing print argument on line {line_num}")

                # Printing variables 
                elif fields[1] in variables:
                    out_file.write(f"load {variables[fields[1]]}\n")
                    out_file.write("copy r1\n")
                    out_file.write("addi r1 0\n")
                    out_file.write("ssrf r0\n")
                    out_file.write("jsr printNum\n")
                    uses_print_num = True

                # Priniting digits
                elif fields[1].isdigit():
                    out_file.write(f"addi r0 {fields[1]}\n")
                    out_file.write("ssrf r0\n")
                    out_file.write("jsr printNum\n")
                    uses_print_num = True

                # Printing arrays
                elif "[" in fields[1] and "]" in fields[1]:
                    emit_array_load(
                        fields[1],
                        "r1",
                        arrays,
                        variables,
                        out_file,
                        line_num
                    )

                    out_file.write("addi r1 0\n")
                    out_file.write("ssrf r0\n")
                    out_file.write("jsr printNum\n")
                    uses_print_num = True
                
                # Printing function return value
                elif fields[1] == "RETVAL":
                    out_file.write("rsrf r0\n")
                    out_file.write("copy r1\n")
                    out_file.write("addi r1 0\n")
                    out_file.write("ssrf r0\n")
                    out_file.write("jsr printNum\n")
                    uses_print_num = True               
                else:
                    tty_column = emit_tty_text(
                        fields[1],
                        out_file,
                        tty_column
                    )

                continue

            # ASSIGNMENTS
            if len(fields) >= 3 and fields[1] == "=" and ((fields[0] in variables )or (re.sub(r"\[.*?\]", "", fields[0]) in arrays)):
                access_array = False
                stack = deque()

                for field in fields[2:]:
                    result = re.sub(r"\[.*?\]", "", field)
                    if result in arrays:
                        # save copy of the token
                        array_copy = field

                    if (
                        field not in variables
                        and not field.isdigit()
                        and field not in valid_operators
                        and field not in ["(", ")"]
                        and result not in arrays
                        and field != "RETVAL"
                    ):
                        raise Exception(f"Variable or token '{field}' not declared on line {line_num}")

                postfix_tokens = parse_to_postfix(fields[2:], variables)

                stack = deque()
                reg_num = 1

                # Writing to an array
                array_target = None

                if re.sub(r"\[.*?\]", "", fields[0]) in arrays:
                    access_array = True
                    array_name_access, array_index_token = parse_array_access(
                        fields[0],
                        arrays,
                        line_num
                    )
                    array_target = (array_name_access, array_index_token)
                        
                # Writing to a variable 
                for token in postfix_tokens:
                    result = re.sub(r"\[.*?\]", "", token)
                    # Variables and raw ints
                    if token.isdigit() or token in variables or token == "RETVAL":

                        target_reg = f"r{reg_num}"
                        check_register_overflow(reg_num, line_num)

                        load_operand_to_reg(token, target_reg, variables, out_file)

                        stack.append(target_reg)
                        reg_num += 1                       

                    # Math operators
                    elif token in valid_operators: 
                        right_reg = stack.pop()
                        left_reg = stack.pop()

                        # Load right operand into accumulator
                        out_file.write(f"addi {right_reg} 0\n")

                        # Apply operation using left register
                        match token:
                            case "+":
                                out_file.write(f"add {left_reg}\n")
                            case "-":
                                out_file.write(f"sub {left_reg}\n")
                            case "*":
                                out_file.write(f"mult {left_reg}\n")
                            case "/":
                                out_file.write(f"div {left_reg}\n")

                        # Store result back into left register
                        out_file.write(f"copy {left_reg}\n")

                        # Reuse left register as the result
                        stack.append(left_reg)

                    # Array data retrieval
                    elif token in arrays or re.sub(r"\[.*?\]", "", token) in arrays:
                        target_reg = f"r{reg_num}"
                        check_register_overflow(reg_num, line_num)

                        emit_array_load(
                            token,
                            target_reg,
                            arrays,
                            variables,
                            out_file,
                            line_num
                        )

                        stack.append(target_reg)
                        reg_num += 1
                    else:
                        raise Exception(f"Invalid token '{token}' on line {line_num}")

                final_reg = stack.pop()

                if access_array:
                    array_name_access, array_index_token = array_target
                    base = arrays[array_name_access]["addr"]
                    length = arrays[array_name_access]["length"]
                    index_value = parse_integer_literal(array_index_token)

                    # Constant array index: keep immediate store.
                    if index_value is not None:
                        if index_value < 0 or index_value >= length:
                            raise Exception(
                                f"Array index {index_value} out of bounds for "
                                f"'{array_name_access}' on line {line_num}"
                            )

                        final_address = base + index_value
                        out_file.write(f"addi {final_reg} 0\n")
                        out_file.write(f"store {final_address}\n")

                    # Variable array index: calculate effective address in a
                    # fresh register, restore the RHS value, and use storer.
                    elif array_index_token in variables:
                        address_reg = f"r{reg_num}"
                        check_register_overflow(reg_num, line_num)

                        out_file.write(
                            f"; storing to {array_name_access}[{array_index_token}] "
                            f"using register-indirect store\n"
                        )

                        # ACC = runtime index
                        out_file.write(f"load {variables[array_index_token]}\n")

                        # address_reg = runtime index
                        out_file.write(f"copy {address_reg}\n")

                        # address_reg = ARRAY_BASE + runtime index
                        if base != 0:
                            out_file.write(f"addi {address_reg} {base}\n")
                            out_file.write(f"copy {address_reg}\n")

                        # Restore the expression result to ACC.
                        out_file.write(f"addi {final_reg} 0\n")

                        # RAM[address_reg] = ACC
                        out_file.write(f"storer {address_reg}\n")

                    else:
                        raise Exception(
                            f"Invalid array index '{array_index_token}' in "
                            f"'{fields[0]}' on line {line_num}"
                        )

                else:
                    out_file.write(f"store {variables[fields[0]]}\n")

                continue
            if not in_asm_block and not in_func_block and (fields[0] != "interrupt"):
                raise Exception(f"Unknown statement on line {line_num}: {' '.join(fields)}")
            else:
                continue

        # Error handling for control statements
        if if_stack:
            raise Exception("Missing endif for one or more if statements")
        
        if while_stack:
            raise Exception("Missing ewhile for one or more while loops")
        
        if for_stack:
            raise Exception("Missing efor for one or more for loops")
        
        if uses_print_num:
            emit_print_num_subroutine(out_file)

except FileNotFoundError:
    print(f"Code file '{filename}' not found.")

except Exception as e:
    print(f"\nCOMPILER ERROR: {e}")
    sys.exit(1)