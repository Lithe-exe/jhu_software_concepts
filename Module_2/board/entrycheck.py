import json
def check_data_counts():
    with open("applicant_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    with open("raw_applicant_data.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    return print("raw_applicant_data entries: " + str(len(raw_data)) + "\n""(Cleaned) applicant_data entries: " +str(len(data)))