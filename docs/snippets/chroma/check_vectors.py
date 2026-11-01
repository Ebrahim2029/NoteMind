import requests

CHROMA_URL = "http://localhost:8000"
TENANT = "default_tenant"
DATABASE = "default_database"
# Replace with your collection UUID from /collections
COLLECTION_ID = "635c4581-5b24-4a80-95e5-c1ef54b0f769"


url = f"{CHROMA_URL}/api/v2/tenants/{TENANT}/databases/{DATABASE}/collections/{COLLECTION_ID}/count"

res = requests.get(url)
if res.status_code == 200:
    count = res.json()  # ✅ this is already an int
    print("✅ Collection count:", count)
else:
    print("❌ Error:", res.status_code, res.text)
