#!/usr/bin/env python3
"""Compiler for Go to MIPS."""
from go_classes import *
from intermediate import process_code
from argparse import ArgumentParser
import logging


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

    indent = 0
    for i, line in enumerate(ir_code.strip().split("\n")):
        if i in global_line_indices:
            continue

        if line.startswith("func begin"):
            mips += " " * indent + "{}:\n".format(line.split()[-1])
            indent += 4
            # Move all global declarations into the main function
            if line.startswith("func begin main"):
                for item in global_lines:
                    mips += " " * indent + item + "\n"

        elif line == "func end":
            mips += "\n"
            indent -= 4

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
