package main

type info struct {
	info int
}

type person struct {
	info
	name int
	age  int
}

func main(){
	a := person{info{4},5,2}
	println(a.name,a.age)
}