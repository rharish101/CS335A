package main

import "fmt"

func main() {
	var a [3][3]int
	var b [3][3]int
	var res [3][3]int

	c := 0
	for (i := 0; i < 3; i++) {
		for (j := 0; j < 3; j++) {
			scanln(&c)
			a[i][j] = c
		}
	}

	for (i := 0; i < 3; i++) {
		for (j := 0; j < 3; j++) {
			scanln(&c)
			b[i][j] = c
		}
	}

	for (i := 0; i < 3; i++) {
		for (j := 0; j < 3; j++) {
			c = 0
			for (k := 0; k < 3; k++) {
				d := a[i][k]
				e := b[k][j]
				c += d * e
			}
			res[i][j] = c
		}
	}

	for (i := 0; i < 3; i++) {
		println(res[i][0], res[i][1], res[i][2])
	}
}