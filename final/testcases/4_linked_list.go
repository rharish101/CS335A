package main

import "fmt"

type ll struct {
	a    int
	next *ll
	check bool
}

func main() {
	var a1 ll
	var a2 ll
	var a3 ll
	var a4 ll

	a1.a = 2
	a2.a = 2
	a3.a = 3
	a4.a = 5

	a1.check = false
	a2.check = false
	a3.check = false
	a4.check = false

	a1.next = &a2
	a1.check = true
	a2.next = &a3
	a2.check = true
	a3.next = &a4
	a3.check = true


	head := &a1

	found := false
	for (;;){
		if ((*head).a == 3) {
			found = true
			break
		}
		head = (*head).next
	}

	if (found) {
		println("Found\n")
	} else {
		println("Not found\n")
	}
}