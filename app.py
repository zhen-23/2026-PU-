import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from flask import Flask, render_template, request
from datetime import datetime
import random

# 1. Firebase 初始化 (支援本地與 Vercel 部署)
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

# --- 路由設定 ---

@app.route("/movie", methods=["GET", "POST"])
def movie():
    keyword = ""
    movie_list = []
    if request.method == "POST":
        keyword = request.form.get("keyword")
        url = "http://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAll")

        for item in result:
            title_tag = item.select_one(".filmTitle a")
            if title_tag:
                name = title_tag.text.strip()
                if keyword in name:
                    # 1. 抓取海報網址
                    img_tag = item.find("img")
                    picture = img_tag.get("src").replace(" ", "") if img_tag else ""
                    
                    # 2. 抓取電影連結
                    link = "http://www.atmovies.com.tw" + title_tag.get("href")
                    
                    # 3. 上映日期及片長之字串處理 (老師的版本 6 邏輯)
                    runtime_div = item.find("div", class_="runtime")
                    if runtime_div:
                        show = runtime_div.text.replace("上映日期：", "")
                        show = show.replace("片長：", "")
                        show = show.replace("分", "")
                        
                        # 依照截圖切割字串
                        showDate = show[0:10]      # 前 10 碼是日期
                        showLength = show[13:].strip()  # 13 碼之後是片長
                    else:
                        showDate = "暫無資訊"
                        showLength = "暫無資訊"

                    movie_list.append({
                        "name": name, 
                        "link": link, 
                        "picture": picture,
                        "showDate": showDate, 
                        "showLength": showLength
                    })
            
    return render_template("movie.html", movies=movie_list, keyword=keyword)

@app.route("/movie_info")
def movie_info():
    name = request.args.get("m")
    link = request.args.get("link")
    
    # 1. 爬取詳細頁面資訊 (這部分是新的邏輯)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(link, headers=headers)
        res.encoding = "utf-8"
        sp = BeautifulSoup(res.text, "html.parser")
        
        # 2. 抓取片長 (根據開眼電影網結構)
        info_block = sp.select_one(".film_block")
        runtime = "暫無資訊"
        if info_block and "片長：" in info_block.text:
            # 擷取「片長：」後面的數字
            runtime = info_block.text.split("片長：")[1].split("分")[0].strip() + " 分鐘"
    except:
        runtime = "讀取失敗"

    # 3. 回傳給 HTML (不需要傳遞 description)
    return render_template("movie_info.html", name=name, link=link, runtime=runtime)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        # 使用 .strip() 避免空格導致搜尋不到
        keyword = request.form.get("keyword").strip()
        collection_ref = db.collection("靜宜資管2026a")
        docs = collection_ref.get()

        for doc in docs:
            user = doc.to_dict()
            # 使用 .get 避免 KeyError，並進行關鍵字模糊比對
            name = user.get("name", "")
            if keyword in name:
                results.append({
                    "name": name,
                    "lab": user.get("lab", "尚未設定")
                })

    return render_template("search.html", results=results, keyword=keyword)

@app.route("/read")
def read():
    db = firestore.client()
    temp = ""
    collection_ref = db.collection("靜宜資管2026a")
    # 設定跟老師一樣的順序：按 lab 數字從大到小排序，限制 4 筆
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    
    for doc in docs:
        temp += str(doc.to_dict()) + "<br>"
    return temp

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    now_str = f"{now.year}年{now.month}月{now.day}日"
    return render_template("today.html", datetime=now_str)

@app.route("/me")
def about():
    
    return render_template("me.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        opt = request.form["opt"]
        y = int(request.form["y"])      
        result = f"您輸入的是：{x}{opt}{y}"
        
        if opt == "/" and y == 0:
            result += "，除數不能為0"
        else:
            match opt:
                case "+": r = x + y
                case "-": r = x - y
                case "*": r = x * y
                case "/": r = x / y
                case _: return "未知運算符號"
            result += f"={r}<br><a href=/>返回首頁</a>"          
        return result
    return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    result = None
    if action == 'toss':
        x1, x2 = random.randint(0, 1), random.randint(0, 1)
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": f"/static/{x1}.jpg",
            "cup2": f"/static/{x2}.jpg",
            "message": msg
        }
    return render_template('cup.html', result=result)

@app.route("/math2", methods=["GET", "POST"])
def math2():
    result = None
    if request.method == "POST":
        x = int(request.form.get("x"))
        opt = request.form.get("opt")
        y = int(request.form.get("y"))
        match opt:
            case "∧": result = x ** y
            case "√": result = x ** (1/y) if y != 0 else "數學上不存在「0 次方根」"
            case _: result = "請輸入∧(次方)或√(根號)"
    return render_template("math2.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
