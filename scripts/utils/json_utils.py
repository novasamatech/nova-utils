import json

def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        f.write('\n')
