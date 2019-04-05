package main

type info struct {
	info string
}

type person struct {
	info
	name string
	age  int
}

func main(){
	a := person{info{"vishwas"},"name",2}
}