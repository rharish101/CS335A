package main

// Yo
/* Hello "world" program
   In Go*/

var c int64 = 2

type help struct {
	b string
}

type person struct {
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
	age  check1
	age1 int
}

type T struct {
	f1     string "f one"
	f2     string
	f3     string `f `
	f4, f5 int64  `f four and five`
}
type int_t uint

func temp1(x uint, y uint) uint {
	return x
}

func temp2(x uint, y uint) (uint, uint) {
	return x, y
}

func add(x uint, y uint) uint {
	return x + y
}

func temp(x int, y int) {
	oneD := [2]int{1, 2}
	threeD := [5][2][3]int{{{0, 0, 0}, {0, 0, 0}}, {{1, 1, 1}, {2, 2, 2}}, {{2, 2, 2}, {4, 4, 4}}, {{3, 3, 3}, {6, 6, 6}}, {{4, 4, 4}, {8, 8, 8}}}
	threeD[2][0][1] = 7
	add := oneD[1] + threeD[2][1][2]
	gu := help{"vishwas"}
	r := person{gu, 2}
	struct_array := [1][2]person{{r, r}}
	harish := struct_array[1][2]
	item := harish.name
	/*	name1 := struct_array[1].b*/

	f := [3]int{1, 2, 3}
	var g [3]int
	g = f
	tp := 2
	emp3 := struct {
		firstName, lastName string
		age, salary         int
	}{
		firstName: "Andreah",
		lastName:  "Nikola",
		age:       tp,
		salary:    5000,
	}

	waste := emp3.age

	m := 2
	n := &m
	t := person{age: 2, name: help{"vishwas"}}
	t1 := check{"string", 2}
	t2 := person1{check1{2}, 3}
	t2.age1 = 4
	t.age = 2
	t.age++
	k := t.age + *n

	var d int_t = 4
	var b uint = 3
	b, b = temp2(b, b)
	c := uint(d) + b

	a := c
	var z uint = 20
	d = 3
	primes := [3]uint{2, 3, 4}

	s := "string"

	e := 4*5 + c + primes[2] + add(temp1(2, 3), 3)
	primes1 := [3]int{2, 3, 4}
	primes[primes1[2]] = z
	var val uint = add(2, 3)

	primes[e] = 23
}

func main() {
	s := "string"
	var a int = 4
	b := a + 4*5
	c := a - b
}
