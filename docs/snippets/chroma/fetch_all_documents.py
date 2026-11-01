import requests

CHROMA_URL = "http://localhost:8000"
TENANT = "default_tenant"
DATABASE = "default_database"
COLLECTION = "notes"

url = f"{CHROMA_URL}/api/v2/tenants/{TENANT}/databases/{DATABASE}/collections/{COLLECTION}/get"

payload = {
    "include": ["documents", "metadatas", "ids"],
    "limit": 5  # just get first 5
}

res = requests.post(url, json=payload)
if res.status_code == 200:
    data = res.json()
    if data.get("documents"):
        print("✅ Found data in Chroma:")
        for doc in data["documents"]:
            print("-", doc)
    else:
        print("⚠️ No documents found in collection")
else:
    print("❌ Error:", res.status_code, res.text)
