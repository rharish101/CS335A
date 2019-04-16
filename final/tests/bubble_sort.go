package main

var arr [5]int = [5]int{4,2,1,5,6}

type bag struct {
    arr [5]int
}

func BubbleSort(source *bag)  {
   L := 5
   items := (*source).arr
   for(i:=0;i<5;i++){
      println(items[i])
   }
   for  (i:=0;i<L;i++){
      for (j:=0;j<(L-1-i);j++){
         if (items[j] > items[j+1]){
            temp := items[j]
            items[j] = items[j+1]
            items[j+1] = temp
         }
      }
   }
   for(i:=0;i<5;i++){
      println(items[i])
   }

}

func main(){
	a := [5]int{4,2,1,5,6}
	b := bag{arr: a}
	BubbleSort(&b)
   // for(i:=0;i<5;i++){
   //    println(a[i])
   // }
}
