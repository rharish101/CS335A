package main

type Vertex struct {
	X, Y float64
	}

func add(v Vertex, a [5]int) float64 {
		println(v.X,v.Y)
		for(i:=0;i<5;i++){
			println(a[i])
		}
		return v.X
	}



func main() {
	a := [5]int{4,2,1,5,6}
	v := Vertex{3.5, 4.5}
	add(v,a)
}
