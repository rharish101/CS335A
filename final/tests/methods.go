package main

import (
	"fmt"
	"math"
)
type Vertex struct {
	X, Y float64
	}

func (v Vertex) add() float64 {
		s := "string"
		var a int = 4
		b := a + 4*5
		c:=a-b
		d := 4.5
		return d
	}



func main() {
	v := Vertex{3.5, 4.5}
	result := v.add()
	var a float64  = result + 2.5	
}
