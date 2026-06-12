import re

import requests

r = requests.get(
    "https://finance.yahoo.com/quote/AAPL",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=10,
)
m = re.search(r'"marketCap":\{"raw":(\d+)', r.text)
print(m.group(1) if m else "Not found")
