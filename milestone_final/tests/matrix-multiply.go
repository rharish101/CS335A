package main;

 
func main(){
  var c,d,k,sum int;
  var first, second, multiply [5][5]int;
  i := 0
  for (c = 0 ; c < 5 ; c++){
    for ( d = 0 ; d < 4 ; d++ ){
      first[c][d] = i
      second[c][d] = i
      i++
    }
  }

  for(c=0;c<5;c++){
    for(d=0;d<5;d++){
      sum=0
      for(k=0;k<5;k++){
        sum += (first[c][k])*(second[k][d])
      }
      multiply[c][d]=sum
    }
  }

}