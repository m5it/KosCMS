from pathlib import Path; p = Path("webcms/admin/admin_api.py"); lines = p.read_text().splitlines()
for i, line in enumerate(lines, 1):
    if any(k in line for k in ["def _get_model_list", "def _get_model_by_id", "def _current_user_id", "def _serialize_page"]):
        print(f"{i:4d}: {line}")