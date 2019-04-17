package main

import "fmt"

type node struct {
	val int
	l   *node
	r   *node
	check_l bool
	check_r bool 
}

func bst(head node) {
	if(head.check_l){
		bst(*(head.l))
	}
	println(head.val)
	if(head.check_r){
		bst(*(head.r))
	}
}

func main() {

	var a1 node
	a1.val = 1
	a1.check_l = false
	a1.check_r = false
	var a2 node
	a2.val = 2
	a2.check_l = false
	a2.check_r = false
	var a3 node
	a3.val = 3
	a3.check_l = false
	a3.check_r = false
	var a4 node
	a4.val = 4
	a4.check_r = false
	a4.check_l = false
	var a5 node
	a5.val = 5
	a5.check_r =false
	a5.check_l = false

	a1.l = &a2
	a1.check_l = true
	a1.r = &a3
	a1.check_r = true
	a2.l = &a4
	a2.check_l = true
	a2.r = &a5
	a2.check_r = true
	
	bst(a1)
}