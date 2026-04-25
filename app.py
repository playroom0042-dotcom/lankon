from flask import Flask, render_template_string, request, redirect
import pandas as pd
import numpy as np
import math
import os

app = Flask(__name__)

# ================= ANALİZ =================
def poisson(l, k):
    return (l**k * np.exp(-l)) / math.factorial(k)

def analyze():
    df = pd.read_excel("matches.xlsx")
    results = []

    for _, r in df.iterrows():
        home = r["Home"]
        away = r["Away"]

        tempo_h = r["Home_Shots"]*0.6 + r["Home_Corners"]*0.4
        tempo_a = r["Away_Shots"]*0.6 + r["Away_Corners"]*0.4
        total = tempo_h + tempo_a + 1e-6

        lh = r["Home_xG"]*(tempo_h/total)*2.4
        la = r["Away_xG"]*(tempo_a/total)*2.4

        prob = np.zeros((6,6))
        for i in range(6):
            for j in range(6):
                prob[i,j] = poisson(lh,i)*poisson(la,j)

        home_win = np.tril(prob,-1).sum()
        draw = np.trace(prob)
        away_win = np.triu(prob,1).sum()

        over25 = sum(prob[i,j] for i in range(6) for j in range(6) if i+j>=3)
        btts = sum(prob[i,j] for i in range(1,6) for j in range(1,6))

        score = np.unravel_index(np.argmax(prob), prob.shape)

        pick = "İKİLİ ŞANS"
        risk = "SAFE"

        if home_win > 0.6:
            pick = f"{home} QALİB"
            risk = "LOW"
        elif away_win > 0.6:
            pick = f"{away} QALİB"
            risk = "LOW"
        elif over25 > 0.65:
            pick = "2.5 ÜST"
            risk = "MEDIUM"
        elif btts > 0.65:
            pick = "QOL-QOL VAR"
            risk = "MEDIUM"

        results.append({
            "match": f"{home} vs {away}",
            "home": round(home_win*100),
            "draw": round(draw*100),
            "away": round(away_win*100),
            "over25": round(over25*100),
            "btts": round(btts*100),
            "score": f"{score[0]}-{score[1]}",
            "pick": pick,
            "risk": risk
        })

    return results


# ================= MAIN PAGE =================
@app.route("/")
def home():
    data = analyze()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elnurun Analizi</title>

<style>
body{
background:#020617;
color:white;
font-family:Arial;
text-align:center;
}

h1{color:#22c55e}

.card{
background:#111827;
margin:10px;
padding:15px;
border-radius:12px;
transition:0.3s;
}

.card:hover{
transform:scale(1.03);
box-shadow:0 0 20px #22c55e;
}

canvas{
position:fixed;
top:0;
left:0;
z-index:-1;
}
</style>
</head>

<body>

<canvas id="bg"></canvas>

<h1>⚽ Elnurun Analizi ⚽</h1>
<a href="/admin" style="color:#22c55e;">Admin Panel</a>

{% for m in data %}
<div class="card">
<h3>{{m.match}}</h3>
<p>1: {{m.home}}% | X: {{m.draw}}% | 2: {{m.away}}%</p>
<p>2.5 ÜST: {{m.over25}}% | QOL-QOL: {{m.btts}}%</p>
<p>Hesab: {{m.score}}</p>
<b>{{m.pick}}</b>
</div>
{% endfor %}

<script>
const c=document.getElementById("bg");
const ctx=c.getContext("2d");
c.width=window.innerWidth;
c.height=window.innerHeight;

let balls=[];
for(let i=0;i<20;i++){
balls.push({x:Math.random()*c.width,y:Math.random()*c.height,r:5,dy:1+Math.random()*2});
}

function draw(){
ctx.clearRect(0,0,c.width,c.height);
balls.forEach(b=>{
ctx.beginPath();
ctx.arc(b.x,b.y,b.r,0,Math.PI*2);
ctx.fillStyle="#22c55e";
ctx.fill();
b.y+=b.dy;
if(b.y>c.height)b.y=0;
});
requestAnimationFrame(draw);
}
draw();
</script>

</body>
</html>
""", data=data)


# ================= ADMIN PANEL =================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        file = request.files["file"]
        file.save("matches.xlsx")
        return redirect("/")

    return """
    <h2>Admin Panel</h2>
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file">
    <button type="submit">Yüklə</button>
    </form>
    """


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))