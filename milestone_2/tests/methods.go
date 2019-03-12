package main

import (
	"fmt"
	"math"
)
type Vertex struct {
	X, Y float64
	}

func (v Vertex) add() float64 {
		return math.Sqrt(v.X*v.X + v.Y*v.Y)
	}



func main() {
	v := Vertex{3, 4}
	result := v.add()
	// fmt.Println(v.add())
	
	
	
}
