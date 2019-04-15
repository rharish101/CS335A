package main

func main() {
	var arr [4][2]int
    for (i := 0; i < 4; i++) {
        scanln(&arr[i][0], &arr[i][1])
    }
    for (i := 0; i < 4; i++) {
        println(arr[i][0], arr[i][1])
    }
}
