Parser for Go
============

This is a parser for Go written in Python for CS335A by project group 8.

The parser is built using GNU Make as follows:
  $ make

The parser is then run as follows:
  $ ./myASTGenerator tests/input2/some.go --output=some.dot

It is HIGHLY recommended to run it with python3.

The only requirement for the parser is the python library PLY, which can be installed as follows:
  # pip install ply

If root access is not available for installing PLY, then create a virtualenv and install it as follows:
  $ virtualenv -p=python3 ply_venv
  $ source ply_venv/bin/activate
  $ pip install ply

Now, the parser can be tested. After testing, deactivate the virtualenv as follows:
  $ deactivate

To visualize the graph, use the "dot" tool from "graphviz" as follows:
  $ dot -Tps some.dot -o some.ps
