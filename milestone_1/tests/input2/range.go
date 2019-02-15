package main

import "fmt"

func main() {
	numbers := [9]int{0, 1, 2, 3, 4, 5, 6, 7, 8}
	for (i := range numbers) {
		fmt.Println("Slice item", i, "is", numbers[i])
	}
}
