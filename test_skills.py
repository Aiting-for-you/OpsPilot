#!/usr/bin/env python3
"""Test skills storage"""
import sys
sys.path.insert(0, 'backend')

from opspilot.api.skills_storage import get_skills_storage

s = get_skills_storage()
s.reload()

print('Skills loaded:', list(s._skills_cache.keys()))
for skill_id, skill in s._skills_cache.items():
    print(f'  - {skill_id}: {skill.get("name")}, category: {skill.get("category")}')
    if 'scripts' in skill:
        print(f'    Scripts: {skill["scripts"]}')
