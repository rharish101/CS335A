//shows functions, their activation records and semantic checking on operations using their return types

package main
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

func temp(x int,y int){
	var d int_t = 4
	var b uint = 3
    b,b = temp2(b, b)
    println(b,b)
	c := uint(d) + b
	a := c
	var z uint = 20
	d = 3
	primes := [3]uint{2, 3, 4}
	e :=  add(temp1(2, 3), 3)
	println(e)
	primes1 := [3]int{2, 3, 4}
	primes[primes1[2]] = z
	var val uint = add(2, 3)

	primes[e] = 23
}

func main(){
	temp(2,3)
}
