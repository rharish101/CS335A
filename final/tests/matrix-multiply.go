package main;

 
func main(){
  var c,d,k,sum int;
  var first, second, multiply [5][5]int
  i := 0
  var one [5] int
  j:=0
  for(h:=0;h<5;h++){
    one[h] = j
    j++
    println(one[h])
  }
  for (c = 0 ; c < 5 ; c++){
    for ( d = 0 ; d < 4 ; d++ ){
      first[c][d] = i
      second[c][d] = i
      i = i+1
      println(first[c][d],second[c][d])
    }
  }

  for(c=0;c<5;c++){
    for(d=0;d<5;d++){
      sum=0
      for(k=0;k<5;k++){
        sum = sum + (first[c][k])*(second[k][d])
      }
      multiply[c][d]=sum
    }
  }
  for(i:=0;i<5;i++){
    for(j:=0;j<5;j++){
      println(multiply[i][j])
    }
  }

}