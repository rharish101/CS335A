# CS335A: Compiler Design - Project

This is the repository for the group project for CS335A: Compiler Design

## Group Members

* [Harish Rajagopal](https://github.com/rharish101)
* [Vishwas Lathi](https://github.com/vishwaslathi)
* [Siddharth Nohria](https://github.com/siddharthnohria)

## Info

* *Source Language*: Go (modified)
* *Target Language*: MIPS (using the SPIM simulator)
* *Implementation Language*: Python 3.7

## Features
* Most basic C-like features, like:
  * Native datatypes
  * Variables and expressions
  * Control statements (for, while, if-else)
  * Arrays
  * Functions (including recursion)
  * Pointers
  * Structs
  * Libraries (using file imports)
  * Basic I/O (`println`, `scanln`)
* Composite literals
* Struct embedding, a.k.a composition of structs
* Typedefs and aliases (kept separate)
* Overloading of "+" for string concatenation
* Multi-level pointers (`***ptr`)
* Multiple returns from functions
* Multiple assignments on the same line (eg. `a, b = b, a`)
* Switch statements
* Short declarations (for automatic type inference)
* Short-circuit evaluation

All Golang features not mentioned above are not implemented.

### Source Modifications
* All `for` loops, `if` statements and `switch` statements must have their clause inside brackets.
* During embedding of structs, the embedded struct should be accessed as a struct attribute only.  
  For example:
  ```
  type struct foo {
    a int
  }
  type struct bar {
    foo
    b int
  }
  item := bar{foo{a: 3}, b: 5}
  ```
  Here, `item.foo.a` is valid, but `item.a` is **INVALID**
