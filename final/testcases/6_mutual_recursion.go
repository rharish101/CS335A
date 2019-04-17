package main

func foo (a int)
func bar (a int)

func foo (a int) {
    if (a > 0) {
        println(a)
        bar(a - 1)
    }
}

func bar (a int) {
    if (a > 0) {
        println(a)
        foo(a - 1)
    }
}

func main() {
    foo(3)
}
