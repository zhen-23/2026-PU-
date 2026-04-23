import requests
from bs4 import BeautifulSoup
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request
from datetime import datetime
import random

# Firebase 初始化
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

# --- 【電影功能區】 ---

@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:] 

    db = firestore.client()
    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
        
        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]      
        showLength = show[13:]     

        doc = {
            "title": title, "picture": picture, "hyperlink": hyperlink,
            "showDate": showDate, "showLength": showLength, "lastUpdate": lastUpdate
        }
        db.collection("電影").document(movie_id).set(doc)
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

# 修正：讓電影查詢對應 input.html 的 MovieTitle
@app.route("/search_movie", methods=["GET", "POST"])
def search_movie():
    if request.method == "POST":
        # 這裡要跟 input.html 裡面的 name="MovieTitle" 一樣
        movie_title = request.form.get("MovieTitle") 
        if not movie_title:
            return "請輸入片名！"
            
        db = firestore.client()
        docs = db.collection("電影").get()
        info = ""
        for doc in docs:
            data = doc.to_dict()
            if movie_title in data.get("title", ""):
                info += f"<h3>{data['title']}</h3>"
                info += f"<img src='http://www.atmovies.com.tw{data['picture']}' width='200'><br>"
                info += f"片長：{data['showLength']} 分鐘<br>"
                info += f"上映日期：{data['showDate']}<br>"
                info += f"<a href='{data['hyperlink']}' target='_blank'>影片介紹</a><br><hr>"
        return info if info else "抱歉，找不到相關電影。"
    return render_template("input.html")

# --- 【老師查詢功能區】 ---

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    if request.method == "POST":
        # 避免 strip() 報錯，先檢查有沒有拿到值
        keyword = request.form.get("keyword")
        if keyword:
            keyword = keyword.strip()
            collection_ref = db.collection("靜宜資管2026a")
            docs = collection_ref.get()
            for doc in docs:
                user = doc.to_dict()
                name = user.get("name", "")
                if keyword in name:
                    results.append({"name": name, "lab": user.get("lab", "尚未設定")})
        return render_template("search.html", results=results, keyword=keyword)
    return render_template("search.html", results=results)

# --- 【原本的其他功能】 ---

@app.route("/read")
def read():
    db = firestore.client()
    temp = ""
    docs = db.collection("靜宜資管2026a").order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    for doc in docs:
        temp += str(doc.to_dict()) + "<br>"
    return temp

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=f"{now.year}年{now.month}月{now.day}日")

@app.route("/me")
def about():
    return render_template("me.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x, opt, y = int(request.form["x"]), request.form["opt"], int(request.form["y"])
        if opt == "/" and y == 0: return "除數不能為0"
        match opt:
            case "+": r = x + y
            case "-": r = x - y
            case "*": r = x * y
            case "/": r = x / y
        return f"結果：{r}<br><a href='/'>返回首頁</a>"
    return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    result = None
    if action == 'toss':
        x1, x2 = random.randint(0, 1), random.randint(0, 1)
        msg = "聖筊" if x1 != x2 else ("笑筊" if x1 == 0 else "陰筊")
        result = {"cup1": f"/static/{x1}.jpg", "cup2": f"/static/{x2}.jpg", "message": msg}
    return render_template('cup.html', result=result)

if __name__ == "__main__":
    app.run(debug=True)
