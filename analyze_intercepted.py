import json
from collections import Counter
with open('intercepted.json') as f:
    data = json.load(f)
counts = Counter(f"{d['action'][0]} on {d['tile']} with {str(d['winv'])}" for d in data)
for k, v in counts.most_common(10):
    print(f"{v} times: {k}")
