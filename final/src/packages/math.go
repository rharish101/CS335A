package main

var Pi float32 = 22 / 7

func _shift(x float32) float32 {
	for (x < -Pi) {
		x += 2 * Pi
	}
	for (x > Pi) {
		x -= 2 * Pi
	}
	return x
}

func Sin(x float32) float32 {
	x = _shift(x)
	sin := x - x*x*x/6 + x*x*x*x*x/120
	return sin
}

func Cos(x float32) float32 {
	x = _shift(x)
	cos := 1 - x*x/2 + x*x*x*x/24
	return cos
}
