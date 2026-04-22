import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
 
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

collection_ref = db.collection("靜宜資管2026a")
docs = collection_ref.get()

keyword = input("您要查詢老師名字的關鍵字?")
for doc in docs:
    user = doc.to_dict()
    if keyword in user["name"]:
        print(f"{user['name']}老師的研究是在{user['lab']}")
