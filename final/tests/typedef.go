package main

type info1 struct {
	info string
}

type person struct {
	info1
	name string
	age  int
}
type custom person
type custom1 custom

func main(){
	a := custom1{info1{"vishwas"},"name",2}
}