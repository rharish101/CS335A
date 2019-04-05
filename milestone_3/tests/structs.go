//shows typedef/aliasing in structs, operation of fields of structs, inline structs, array of structs, pointers to structs and embeddings
package main 

type help struct {
	b string
}

type info1 struct {
	info string
}

type person struct {
	info1
	name help
	age  int
}
type custom person
type custom1 custom
type check struct {
	name string
	age  int
}
type check1 struct {
	age int
}
type person1 struct {
	check1
	age  check1
	age1 int
}

type T struct {
	f1     string "f one"
	f2     string
	f3     string `f `
	f4, f5 int64  `f four and five`
}

func temp(x int, y int){
	gu := help{"vishwas"}
	r := person{info1{"info"},gu, 2}
	struct_array := [1][2]person{{r, r}}
	harish := &struct_array[1][2]
	deref := *harish
	item := deref.name
	item1 := deref.info1.info
	name1 := struct_array[1][2].name

	//inline structs
		emp3 := struct {
		firstName, lastName string
		age, salary         int
	}{
		firstName: "Andreah",
		lastName:  "Nikola",
		age:       2,
		salary:    5000,
	}

	waste := emp3.age

	t := person{info1 : info1{"info"},age: 2, name: help{"vishwas"}}
	t1 := check{"string", 2}
	t2 := person1{ check1{4},check1{2},3}
	t2.age1 = 4
	t.age = 2
	t.age++
	n := &t.age
	k := t.age + *n
}