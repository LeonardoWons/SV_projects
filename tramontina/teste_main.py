import time
import requests

url = "http://10.16.135.22/api/"

pc = {"placa": "ISA8F54",
      "timestamp": int(time.time())
     }

pe = {"placa": "XXX8X54",
      "timestamp": int(time.time())
     }

try:
    r = requests.post(url, json=pe, timeout=5)
    print(r.status_code)
    print(r.text)

except Exception as e:
    print(e)

