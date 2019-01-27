Lexer for Go
============

This is a lexer for Go written in Python for CS335A by project group 8.

The lexer is run as an executable script as follows:
  $ src/lexer.py --cfg=tests/cfg1/some-cfg tests/input1/some-input --output=some.html
OR
  $ python3 src/lexer.py --cfg=tests/cfg1/some-cfg tests/input1/some-input --output=some.html

It is recommended to run it with python3.

The only requirement for the lexer is the python library PLY, which can be installed as follows:
  # pip install ply

If root access is not available for installing PLY, then create a virtualenv and install it as follows:
  $ virtualenv -p=python3 ply_venv
  $ source ply_venv/bin/activate
  $ pip install ply

Now, the lexer can be tested. After testing, deactivate the virtualenv as follows:
  $ deactivate
