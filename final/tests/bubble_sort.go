package main

func BubbleSort(items [5]int)  {

   L := 5
   for  (i:=0;i<L;i++){
      for (j:=0;j<(L-1-i);j++){
         if (items[j] > items[j+1]){
            items[j], items[j+1] = items[j+1], items[j]
         }
      }
   }

}

func main(){
	a := [5]int{4,2,1,5,6}
	BubbleSort(a)
}