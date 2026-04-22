import requests
from bs4 import BeautifulSoup

url = "https://tcyang2026-a.vercel.app/about"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.find(id="h2text")

print(result)