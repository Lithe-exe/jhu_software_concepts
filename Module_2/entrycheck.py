import json

with open("applicant_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(len(data))
