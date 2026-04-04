function a(){
let t=f.value.toLowerCase();
if(t.includes("good")) r.innerHTML="Positive";
else if(t.includes("bad")) r.innerHTML="Negative";
else r.innerHTML="Neutral";
}