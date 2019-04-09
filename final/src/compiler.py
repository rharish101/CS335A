#!/usr/bin/env python3
"""Compiler for Go to MIPS."""
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
    return ir_code


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
