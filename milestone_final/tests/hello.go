package main

// Yo
/* Hello "world" program
   In Go*/
//contains most of the functionalities that our language supports
var c int64 = 2

type help struct {
	b string
}

type info struct {
	info string
}

type person struct {
	info
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

func FibonacciRecursion(n int) int {
    if( n <= 1 ){
        return n
    }
    return FibonacciRecursion(n-1) + FibonacciRecursion(n-2)
}

func Factorial(n uint64)(result uint64) {
	if (n > 0) {
		var result uint64 = n * Factorial(n-1)
		return result
	}
	return 1
}

func loop(){
	var sum int = 0
		for(i:=0;i<100;i++){
			sum += i
		}

		// infinte loop
		for(;;){
			
		}
}

func temp(x int, y int) {
	oneD := [2]int{1, 2}
	threeD := [5][2][3]int{{{0, 0, 0}, {0, 0, 0}}, {{1, 1, 1}, {2, 2, 2}}, {{2, 2, 2}, {4, 4, 4}}, {{3, 3, 3}, {6, 6, 6}}, {{4, 4, 4}, {8, 8, 8}}}
	threeD[2][0][1] = 7
	add := oneD[1] + threeD[2][1][2]
	gu := help{"vishwas"}
	r := person{info{"info"},gu, 2}
	struct_array := [1][2]person{{r, r}}
	harish := struct_array[1][2]
	item := harish.name

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
	t := person{info : info{"info"},age: 2, name: help{"vishwas"}}
	t1 := check{"string", 2}
	t2 := person1{ check1{4},check1{2},3}
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
