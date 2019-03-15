IR Code Generator for Go
========================

This is an IR code generator for a modified (*) Go written in Python for CS335A by project group 8.

The IR code generator is run as follows:
  $ ./intermediate.py ../tests/some.go --output=somefolder

It is HIGHLY recommended to run it with python3.

The only requirement for the IR code generator is the python library PLY, which can be installed as follows:
  # pip install ply

If root access is not available for installing PLY, then create a virtualenv and install it as follows:
  $ virtualenv -p=python3 ply_venv
  $ source ply_venv/bin/activate
  $ pip install ply

Now, the IR code generator can be tested. After testing, deactivate the virtualenv as follows:
  $ deactivate

The csv files for the symbol table and the txt files for the 3AC code will be saved in a folder ("somefolder" in the above example)

==============================
NOTE:
==============================
*: The modification to Go is as follows:
  Parentheses are necessary for the expressions in if statements, for loops, and switch-case statements.
  Labeled statements and gotos are now unsupported.