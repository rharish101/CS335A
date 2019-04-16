package main

func main() {
	var wflg, tflg int = 0,0 
	var dflg int = 0
	var c rune
	switch(c) {
	case 'w':
		fallthrough
	case 'W':
		wflg = 1
	case 't':
		fallthrough
	case 'T':
		tflg = 1
	case 'd':
		dflg = 1
	}
}
