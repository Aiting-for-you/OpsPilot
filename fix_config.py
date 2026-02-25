# Fix Pydantic v2 Config in schemas.py
import re

with open('opspilot/api/schemas.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: class Config:
#         json_schema_extra = {
#             ...
#         }
# Replace with: model_config = ConfigDict(...)

# Use simple string replacement for each known pattern
patterns = [
    # First pattern (already fixed manually)
    ('class Config:\n        json_schema_extra = {\n            "example": {\n                "user_input": "帮我查询华南地区的供应商",\n                "context": {"user_id": "user-001"}\n            }\n        }',
     'model_config = ConfigDict(json_schema_extra={\n            "example": {\n                "user_input": "帮我查询华南地区的供应商",\n                "context": {"user_id": "user-001"}\n            }\n        })'),
    # ToolCallRequest pattern
    ('class Config:\n        json_schema_extra = {\n            "example": {\n                "tool_name": "query_supplier",\n                "params": {"region": "华南"},\n                "task_id": "task-001"\n            }\n        }',
     'model_config = ConfigDict(json_schema_extra={\n            "example": {\n                "tool_name": "query_supplier",\n                "params": {"region": "华南"},\n                "task_id": "task-001"\n            }\n        })'),
]

for old, new in patterns:
    content = content.replace(old, new)

# Write back
with open('opspilot/api/schemas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")