package main

func main() {
	arr := [4][2]int{{2, 1}, {3, 5}, {9, 77}, {23, 8}}
    for (i := 0; i < 4; i++) {
        println(arr[i][0], arr[i][1])
    }
}
