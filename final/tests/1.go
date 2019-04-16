package main

type bag struct {
    arr [5]int
}

func main(){
	a := [5]int{4,2,1,5,6}
	b := bag{arr: a}
	b.arr[1] = 1
	println(b.arr[1])
}
