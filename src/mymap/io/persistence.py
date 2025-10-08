
import json

def save_to_file(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
