package main

// Yo
/* Hello "world" program
   In Go*/

var c int64  =  2

type person struct {
    name string
    age  int
}

type T struct {
    f1     string "f one"
    f2     string
    f3     string `f `
    f4, f5 int64  `f four and five`
}
func add(x int, y int64)uint {
	return x+y
}

func temp(x int,y int ){
	var d uint= 4
	var b uint = 3
	c := d + b
	a  := c
	var z uint = 20
	d = 3
	primes := [6]uint{2, 3, 5, 7, 11, 13}
	s:= "string"
	e := 4*5 + c + primes[2] + add(2,3)
	primes1 := [2]int{2,3,4}
	primes[primes1[2]] = z

	primes[e] = 23



	// var k int64 = 3
	// k = primes[2]

	// a = e
	{

		z := 4
		s = "string1"
	}
}

func main() {
	
	// s := "string"
	// var a int = 4
	// b := a + 4*5 
	// a:=3+4
	// b :=a*5
	// c:=a-b


}
