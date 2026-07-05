#!/usr/bin/env python3
import json

data = {
    "project": "Data Collection Workout",
    "tasks_completed": 11,
    "tools_tested": 24,
    "categories": [
        {"id": 1, "name": "File I/O", "status": "complete"},
        {"id": 2, "name": "Directory Ops", "status": "complete"},
        {"id": 3, "name": "Content Search", "status": "complete"},
        {"id": 4, "name": "File Editing", "status": "complete"},
        {"id": 5, "name": "Execution", "status": "complete"},
        {"id": 6, "name": "Info Tools", "status": "complete"},
        {"id": 7, "name": "Web Tools", "status": "complete"},
        {"id": 8, "name": "Tips", "status": "complete"},
        {"id": 9, "name": "Multi-Tool Flows", "status": "complete"},
        {"id": 10, "name": "Mixed Output", "status": "complete"},
        {"id": 11, "name": "Tool Result Usage", "status": "in_progress"},
        {"id": 12, "name": "Error Handling", "status": "pending"}
    ],
    "metrics": {
        "files_created": 25,
        "tips_used": 7,
        "errors_encountered": 4,
        "errors_recovered": 4
    }
}

print(json.dumps(data, indent=2))