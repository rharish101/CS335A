#!/usr/bin/env python3
"""Compiler for Go to MIPS."""
from go_classes import *
from intermediate import process_code
from argparse import ArgumentParser
import logging
import re


def infer_type(item, table):
    """Infer the type from the given string operand and return it."""
    if "[" not in item:
        for record in table.activation_record:
            if record[0] == item:
                return record[1]
        raise Exception('"{}" not a valid operand'.format(item))

    root = re.search(r"[\w_]+", item).group()
    for record in table.activation_record:
        if record[0] == root:
            dtype = record[1]

    remaining = item[item.index("[") :]
    while remaining != "":
        end = remaining.index("]")
        if isinstance(dtype, GoType) and dtype.name != "string":
            # This is most probably a struct
            dtype = table.get_struct_obj(dtype.name)

        if isinstance(dtype, GoArray):
            dtype = dtype.dtype
        elif isinstance(dtype, GoStruct):
            index_val = int(remaining[1:end])
            index = 0
            for struct_field in dtype.vars:
                if index == index_val:
                    dtype = struct_field[1].dtype
                    break
                index += table.get_size(struct_field[1].dtype)
        elif isinstance(dtype, GoType) and dtype.name == "string":
            dtype = GoType("byte", size=1)
        else:
            raise ValueError("What is this?: {}".format(dtype.name))
        remaining = remaining[end + 1 :]
    return dtype


def size2instr(size, mode, is_float=False, is_unsigned=False):
    """Return appropriate instruction for the given size.

    Args:
        dtype (`GoType`): The dtype
        table (`SymbTable`): The symbol table
        mode (str): One of ["load", "store"]
        is_float: Whether the operand is a float
        is_unsigned: Whether the operand is unsigned

    Returns:
        str: The appropriate instruction

    """
    if mode not in ["load", "store"]:
        raise ValueError('Mode must be one of "load" or "store"')

    if is_unsigned and mode == "load":
        suffix = "u"
    else:
        suffix = ""

    if is_float:
        if size == 4:
            return mode[0] + ".s"
        else:
            return mode[0] + ".d"
    else:
        if size == 1:
            return mode[0] + "b" + suffix
        elif size == 2:
            return mode[0] + "h" + suffix
        else:
            return mode[0] + "w"


def ir2mips(table, ir_code):
    """Convert 3AC to MIPS assembly using the given symbol table.

    Args:
        table (`SymbTable`): The symbol table
        ir_code (str): The 3AC

    Returns:
        str: The MIPS assembly code for the given 3AC

    """
    # Store global variables in the data segment
    mips = ".data:\n"
    for collection in [table.variables, table.intermediates]:
        for var in collection:
            mips += " " * 4 + ".align 2\n"
            mips += " " * 4 + var + ": "
            dtype = collection[var]
            size = table.get_size(dtype)
            mips += ".space {}\n".format(size)
    mips += "\n"

    mips += ".text\n.globl main\n\n"

    # Get all lines in the global scope
    global_lines = []
    global_line_indices = set()
    outside_func = True
    for i, line in enumerate(ir_code.strip().split("\n")):
        if line.startswith("func begin"):
            outside_func = False
        if outside_func:
            global_lines.append(line)
            global_line_indices.add(i)
        if line.startswith("func end"):
            outside_func = True

    # For labelling branches as: "__branch_{}".format(branch_count)
    branch_count = 0
    indent = 0
    act_record = {}
    curr_table = table
    for i, line in enumerate(ir_code.strip().split("\n")):
        if i in global_line_indices:
            continue

        # TODO: Callee saving
        if line.startswith("func begin"):
            func_name = line.split()[-1]
            mips += " " * indent + "{}:\n".format(line.split()[-1])
            indent += 4

            if "." in func_name:
                rec_name = func_name.split(".")[0]
                meth_name = func_name.split(".")[1]
                curr_table = table.get_method((meth_name, rec_name), "body")
                act_record = dict(curr_table.activation_record)
            else:
                curr_table = table.get_func(func_name, "body")[0]
                act_record = dict(curr_table.activation_record)

            # Move all global declarations into the main function
            if func_name == "main":
                for item in global_lines:
                    mips += " " * indent + item + "\n"

        # TODO: Callee retrieving
        elif line == "func end":
            mips += "\n"
            indent -= 4
            act_record = {}
            curr_table = table

        elif "=" in line and "call" not in line:
            mips += " " * indent + "# " + line + "\n"
            if ":" in line:
                mips += (
                    " " * indent
                    + ":".join(line.split(":")[:-1])
                    + ": sll $0, $0, 0\n"
                )

            lhs = line.split(":")[-1].split(" = ")[0].strip()
            lhs_dtype = infer_type(lhs, curr_table)

            rhs = line.split(":")[-1].split(" = ")[1].strip().split()
            if len(rhs) == 1:
                indices = [0]
                # For cases when rhs is a constant
                rhs_dtype = infer_type(lhs, curr_table)
            elif len(rhs) == 3:
                indices = [0, 2]
                rhs_dtype = infer_type(rhs[0], curr_table)
            else:
                indices = [1]
                rhs_dtype = infer_type(rhs[1], curr_table)

            rhs_size = curr_table.get_size(rhs_dtype)
            if isinstance(rhs_dtype, GoArray) or isinstance(
                rhs_dtype, GoPointType
            ):
                is_float = False
                is_unsigned = True
            elif "float" in rhs_dtype.name:
                is_float = True
                is_unsigned = False
            else:
                is_float = False
                if "uint" in rhs_dtype.name:
                    is_unsigned = True
                else:
                    is_unsigned = False

            for reg, i in enumerate(indices):
                if re.match(r"\d+", rhs[i]):
                    if is_float:
                        mips += " " * indent + "{} $f{}, {}\n".format(
                            size2instr(rhs_size, "load", is_float=True),
                            reg * 2,
                            rhs[i],
                        )
                    else:
                        mips += " " * indent + "ori $t{}, $0, {}\n".format(
                            reg, rhs[i]
                        )

                elif rhs[i][0] == "*":
                    offset = act_record[rhs[i][1:]].activation_offset
                    mips += " " * indent + "lw $t{}, {}($fp)\n".format(
                        reg, offset
                    )
                    instr = size2instr(rhs_size, "load", is_float, is_unsigned)
                    if is_float:
                        target = "$f{}".format(reg * 2)
                    else:
                        target = "$t{}".format(reg)
                    mips += " " * indent + "{} {}, ($t{})\n".format(
                        instr, target, reg
                    )

                elif rhs[i][0] == "&":
                    offset = act_record[rhs[i][1:]].activation_offset
                    mips += " " * indent + "addi $t{}, $fp, {}\n".format(
                        reg, offset
                    )

                elif "[" not in rhs[i]:
                    offset = act_record[rhs[i]].activation_offset
                    if is_float:
                        target = "$f{}".format(reg * 2)
                    else:
                        target = "$t{}".format(reg)
                    mips += " " * indent + "{} {}, {}($fp)\n".format(
                        size2instr(rhs_size, "load", is_float, is_unsigned),
                        target,
                        offset,
                    )

                else:
                    # Split the pointer and the index
                    items = re.search(r"([\w_]+)\[([^\]]+)\]", rhs[i]).groups()
                    offset = act_record[items[0]].activation_offset
                    if re.match(r"\d+", items[1]) is None:
                        # The index is a variable
                        ind_offset = act_record[items[1]].activation_offset
                        mips += " " * indent + "lw $t{}, {}($fp)\n".format(
                            reg, offset
                        )
                        mips += " " * indent + "lw $t{}, {}($fp)\n".format(
                            reg + 1, ind_offset
                        )
                        mips += (
                            " " * indent
                            + "add $t{0:}, $t{0:}, $t{1:}\n".format(
                                reg, reg + 1
                            )
                        )
                    else:
                        # The index is a number
                        mips += " " * indent + "lw $t{}, {}($fp)\n".format(
                            reg, offset
                        )
                        mips += (
                            " " * indent
                            + "addi $t{0:}, $t{0:}, {1:}\n".format(
                                reg, items[1]
                            )
                        )
                    if is_float:
                        target = "$f{}".format(reg * 2)
                    else:
                        target = "$t{}".format(reg)
                    mips += " " * indent + "{} {}, ($t{})\n".format(
                        size2instr(rhs_size, "load", is_float, is_unsigned),
                        target,
                        reg,
                    )

            if len(rhs) == 3:
                if is_float:
                    if rhs_size > 4:
                        suffix = ".d"
                    else:
                        suffix = ".s"
                    op2instr = {
                        "+": "add." + suffix,
                        "-": "sub." + suffix,
                        "*": "mul." + suffix,
                        "/": "div." + suffix,
                    }
                    regs = ["$f0", "$f2"]
                else:
                    op2instr = {
                        "+": "addu",
                        "-": "subu",
                        "|": "or",
                        "^": "xor",
                        "<<": "sllv",
                        ">>": "srlv" if is_unsigned else "srav",
                        "&": "and",
                        "==": "seq",
                        "!=": "sne",
                        "<": "sltu" if is_unsigned else "slt",
                        "<=": "sleu" if is_unsigned else "sle",
                        ">": "sgtu" if is_unsigned else "sgt",
                        ">=": "sgeu" if is_unsigned else "sge",
                    }
                    regs = ["$t0", "$t1"]

                if rhs[1] in op2instr:
                    mips += " " * indent + "{0:} {1:}, {1:}, {2:}\n".format(
                        op2instr[rhs[1]], *regs
                    )

                elif rhs[1] == "&^":  # int only
                    mips += " " * indent + "and $t0, $t0, $t1\n"
                    mips += " " * indent + "nor $t0, $t0, $t0\n"

                elif rhs[1] == "||":  # bool only
                    # Set result to 1 in $t2 (to preserve $t0) by default.
                    # The branch will NOT set it to 0.
                    mips += " " * indent + "ori $t2, $0, 1\n"
                    mips += " " * indent + "bne $t0, $0, __branch_{}\n".format(
                        branch_count
                    )
                    mips += " " * indent + "bne $t1, $0, __branch_{}\n".format(
                        branch_count
                    )
                    mips += " " * indent + "ori $t2, $0, 0\n"
                    mips += (
                        " " * indent
                        + "__branch_{}: or $t0, $t2, $0\n".format(branch_count)
                    )

                elif rhs[1] == "&&":  # bool only
                    # Set result to 0 in $t2 (to preserve $t0) by default.
                    # The branch will NOT set it to 1.
                    mips += " " * indent + "ori $t2, $0, 0\n"
                    mips += " " * indent + "beq $t0, $0, __branch_{}\n".format(
                        branch_count
                    )
                    mips += " " * indent + "beq $t1, $0, __branch_{}\n".format(
                        branch_count
                    )
                    mips += " " * indent + "ori $t2, $0, 1\n"
                    # Copy $t2 to $t0
                    mips += (
                        " " * indent
                        + "__branch_{}: or $t0, $t2, $0\n".format(branch_count)
                    )

                elif rhs[1] in ["==", "!=", "<", "<=", ">", ">="]:
                    # float only; int already handled
                    if rhs_size > 4:
                        suffix = ".d"
                    else:
                        suffix = ".s"
                    if rhs[1] in ["==", "!="]:
                        mips += " " * indent + "c.eq{} $f0, $f2\n"
                    elif rhs[1] in ["<", ">="]:
                        mips += " " * indent + "c.lt{} $f0, $f2\n"
                    elif rhs[1] in ["<=", ">"]:
                        mips += " " * indent + "c.le{} $f0, $f2\n"

                    # Set result to 1 by default.
                    # The branch will NOT set it to 0.
                    mips += " " * indent + "ori $t0, $0, 1\n"
                    if rhs[1] in ["==", "<", "<="]:
                        instr = "bc1t"
                    else:
                        instr = "bc1f"
                    mips += " " * indent + "{} __branch_{}\n".format(
                        instr, branch_count
                    )
                    mips += " " * indent + "ori $t0, $0, 0\n"
                    # Branch to noop, to preserve indentation
                    mips += (
                        " " * indent
                        + "__branch_{}: sll $0, $0, 0\n".format(branch_count)
                    )
                    branch_count += 1

                elif rhs[1] == "*":  # int only; float already handled
                    if is_unsigned:
                        instr = "multu"
                    else:
                        instr = "mult"
                    mips += " " * indent + "{} $t0, $t1\n".format(instr)
                    mips += " " * indent + "mflo $t0\n"

                elif rhs[1] in ["/", "%"]:  # int only; float already handled
                    mips += " " * indent + "div $t0, $t1\n"
                    if rhs[1] == "/":
                        mips += " " * indent + "mflo $t0\n"
                    else:
                        mips += " " * indent + "mfhi $t0\n"

            elif len(rhs) == 2:
                suffixes = []
                regs = []
                for item_dtype in [lhs_dtype, rhs_dtype]:
                    if (
                        hasattr(item_dtype, "name")
                        and "float" in item_dtype.name
                    ):
                        regs.append("$f0")
                        if curr_table.get_size(item_dtype) > 4:
                            suffixes.append(".d")
                        else:
                            suffixes.append(".s")
                    else:
                        suffixes.append(".w")
                        regs.append("$t0")
                # Ignoring uint/int casts
                if suffixes[0] != suffixes[1]:
                    mips += " " * indent + "cvt{}{} {}, {}\n".format(
                        *suffixes, *regs
                    )

            if "[" not in lhs:  # No indexing in LHS
                lhs_offset = act_record[lhs].activation_offset
                dest = "{}($fp)".format(lhs_offset)
            elif re.match(r".*\[.+\[", lhs) is None:  # Single indexing in LHS
                offset = act_record[lhs.split("[")[0]].activation_offset
                mips += " " * indent + "lw $t1, {}($fp)\n".format(offset)
                index_str = lhs.split("[")[1][:-1]
            else:  # Indexing in LHS
                remaining = lhs
                while re.match(r".*\[.+\[", remaining) is not None:
                    split = remaining.index("]") + 1
                    before = remaining[:split]
                    remaining = remaining[split:]

                    if before[0] != "[":  # First iteration
                        offset = act_record[
                            before.split("[")[0]
                        ].activation_offset
                        mips += " " * indent + "lw $t1, {}($fp)\n".format(
                            offset
                        )
                        index_str = before.split("[")[1][:-1]
                    else:
                        index_str = before[1:-1]

                    if re.match(r"\d+", index_str):  # Numeric index
                        mips += " " * indent + "lw $t1, {}($t1)\n".format(
                            index_str
                        )
                    else:  # Index is a variable
                        ind_offset = act_record[index_str].activation_offset
                        mips += " " * indent + "lw $t2, {}($fp)\n".format(
                            ind_offset
                        )
                        mips += " " * indent + "add $t1, $t1, $t2\n"
                        mips += " " * indent + "lw $t1, ($t1)\n"
                index_str = remaining[1:-1]

            if "[" in lhs:  # Indexing in LHS
                dest = "($t1)"
                if re.match(r"\d+", index_str):  # Numeric index
                    mips += " " * indent + "addi $t1, $t1, {}\n".format(
                        index_str
                    )
                else:  # Index is a variable
                    ind_offset = act_record[index_str].activation_offset
                    mips += " " * indent + "lw $t2, {}($fp)\n".format(
                        ind_offset
                    )
                    mips += " " * indent + "add $t1, $t1, $t2\n".format(
                        index_str
                    )

            lhs_size = curr_table.get_size(lhs_dtype)
            if isinstance(lhs_dtype, GoArray) or isinstance(
                lhs_dtype, GoPointType
            ):
                is_float = False
                is_unsigned = True
            elif "float" in lhs_dtype.name:
                is_float = True
                is_unsigned = False
            else:
                is_float = False
                if "uint" in lhs_dtype.name:
                    is_unsigned = True
                else:
                    is_unsigned = False

            mips += " " * indent + "{} {}, {}\n".format(
                size2instr(lhs_size, "store", is_float, is_unsigned),
                "$f0" if is_float else "$t0",
                dest,
            )

        # TODO: Check other cases:
        #   * Function calling (call and param)
        #   * Return
        #   * if
        #   * goto
        else:
            mips += " " * indent + line + "\n"
    return mips.strip()


if __name__ == "__main__":
    argparser = ArgumentParser(description="Compiler for Go to MIPS")
    argparser.add_argument("input", type=str, help="input file")
    argparser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="output name for the MIPS assembly code",
    )
    argparser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug output"
    )
    args = argparser.parse_args()
    if args.output is None:
        # Output name is source filename (w/o extension) + ".s"
        args.output = (
            ".".join(args.input.split("/")[-1].split(".")[:-1]) + ".s"
        )

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    table, ir_code = process_code(args.input)
    mips = ir2mips(table, ir_code)
    with open(args.output, "w") as out_file:
        out_file.write(mips)
