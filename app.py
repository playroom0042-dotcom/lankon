from flask import Flask, render_template_string
import pandas as pd
import numpy as np
import math
import os

app = Flask(__name__)

def poisson(l, k):
    return (l**k * np.exp(-l)) / math.factorial(k)

def analyze():
    try:
        df = pd.read_excel("matches.xlsx")
    except:
        return []

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

        if home_win > 0.6:
            pick = f"{home} QALİB"
            risk = "BANKER"
        elif away_win > 0.6:
            pick = f"{away} QALİB"
            risk = "BANKER"
        elif over25 > 0.65:
            pick = "2.5 ÜST"
            risk = "RİSKLİ"
        elif btts > 0.65:
            pick = "QOL-QOL VAR"
            risk = "RİSKLİ"
        else:
            pick = "İKİLİ ŞANS"
            risk = "TƏHLÜKƏSİZ"

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


@app.route("/")
def home():
    data = analyze()

    return render_template_string("""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
    margin:0;
    background: radial-gradient(circle at top, #0f172a, #020617);
    color:white;
    font-family:Arial;
    text-align:center;
}

h1 {
    color:#22c55e;
    text-shadow:0 0 15px #22c55e;
}

.card {
    background:rgba(17,24,39,0.85);
    margin:10px auto;
    padding:15px;
    border-radius:15px;
    max-width:400px;
    transition:0.3s;
}

.card:hover {
    transform:scale(1.05);
    box-shadow:0 0 25px #22c55e;
}

canvas {
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

<audio id="sound">
<source src="https://www.soundjay.com/misc/sounds/whistle-01.mp3">
</audio>

{% if data|length == 0 %}
<p>📂 matches.xlsx əlavə et</p>
{% endif %}

{% for m in data %}
<div class="card">
<h3>{{m.match}}</h3>
<p>1: {{m.home}}% | X: {{m.draw}}% | 2: {{m.away}}%</p>
<p>2.5 ÜST: {{m.over25}}% | QOL-QOL: {{m.btts}}%</p>
<p>Hesab: {{m.score}}</p>
<p><b>{{m.pick}}</b> ({{m.risk}})</p>
</div>
{% endfor %}

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<script>
document.body.addEventListener("click", () => {
    document.getElementById("sound").play();
});

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({canvas: document.getElementById("bg"), alpha:true});

renderer.setSize(window.innerWidth, window.innerHeight);

const geometry = new THREE.SphereGeometry(1, 32, 32);
const texture = new THREE.TextureLoader().load("https://i.imgur.com/8yKQF0K.png");
const material = new THREE.MeshStandardMaterial({ map: texture });

const ball = new THREE.Mesh(geometry, material);
scene.add(ball);

const light = new THREE.PointLight(0xffffff, 1);
light.position.set(5,5,5);
scene.add(light);

camera.position.z = 5;

function animate() {
    requestAnimationFrame(animate);
    ball.rotation.y += 0.01;
    ball.rotation.x += 0.005;
    renderer.render(scene, camera);
}

animate();
</script>

</body>
</html>
""", data=data)


app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))