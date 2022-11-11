import requests
import time
import json

start = time.time()
res = requests.post('http://127.0.0.1:8000/', json={"text": "Fast API"})
end = time.time()
print(end - start)
print(res.text)
