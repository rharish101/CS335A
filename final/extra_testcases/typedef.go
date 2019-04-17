package main

type info1 struct {
	info int
}

type person struct {
	info1
	name int
	age  int
}
type custom person
type custom1 custom

func main(){
	a := custom1{info1{2},3,4}
	println(a.name,a.info1.info,a.age)
}