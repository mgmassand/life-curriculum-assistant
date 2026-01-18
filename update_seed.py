import re

# Read the existing file
with open('app/db/seed.py', 'r') as f:
    content = f.read()

# Add the athletic imports
old_imports = "from app.models.resource import Resource"
new_imports = """from app.models.resource import Resource
from app.models.athletic import (
    Sport,
    AthleticAgeStage,
    AthleticDomain,
    AthleticMilestone,
    TrainingPlan,
)"""
content = content.replace(old_imports, new_imports)

# Write the updated file
with open('app/db/seed.py', 'w') as f:
    f.write(content)

print("Imports added")
