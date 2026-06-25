# project_storage.py
import os
import re
import json


SAVE_DIR = "saved_projects"


def safe_filename(text):
    text = str(text).strip()
    text = re.sub(r"[^a-zA-Z0-9ก-๙_-]", "_", text)
    return text


def get_project_filepath(user_id, project_name):
    os.makedirs(SAVE_DIR, exist_ok=True)

    user_id = safe_filename(user_id)
    project_name = safe_filename(project_name)

    return os.path.join(SAVE_DIR, f"{user_id}_{project_name}.json")


def save_project(user_id, project_name, data):
    filepath = get_project_filepath(user_id, project_name)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def load_project(user_id, project_name):
    filepath = get_project_filepath(user_id, project_name)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data, filepath