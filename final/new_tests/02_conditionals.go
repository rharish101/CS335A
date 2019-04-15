package main


func main() {
	var a int
	scanln(&a)
	if (a <= 10) {
		if (a <= 5) {
			println(a)
		} else {
			println(a-1)
		}
	} else {
		println(a+1)
	}
}