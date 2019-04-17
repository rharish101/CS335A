Compiler for Go
========================

This is a compiler for a modified (*) Go written in Python for CS335A by project group 8.

The compiler is run as follows:
  $ ./compiler.py ../tests/some.go --output=some.s

It is HIGHLY recommended to run it with python3.

The only requirement for the compiler is the python library PLY, which can be installed as follows:
  # pip install ply

If root access is not available for installing PLY, then create a virtualenv and install it as follows:
  $ virtualenv -p=python3 ply_venv
  $ source ply_venv/bin/activate
  $ pip install ply

Now, the compiler can be tested. After testing, deactivate the virtualenv as follows:
  $ deactivate

The output can be run using the QtSPIM MIPS simulator.
