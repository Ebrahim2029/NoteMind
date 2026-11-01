import os
import chromadb 

http_url = os.getenv("CHROMA_HTTP_URL")
print("Chroma URL:", http_url)


client = chromadb.HttpClient(host=http_url)
print("Chroma client:", client)
