package main

type help struct {
	b int
}

type info1 struct {
	info int
}

type person struct {
	info1
	name help
	age  int
}

func temp(x int, y int) {
	//embeddings
	gu := help{4}
	r := person{info1{5}, gu, 2}
	println(r.age)

	// inline structs
	emp3 := struct {
		a, b int
		age, salary int
	}{
		a: 89,
		b:  100,
		age: 7,
		salary: 5000,
	}
	println(emp3.age)
}

func main() {
	temp(2, 3)
}
