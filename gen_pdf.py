from pdf_generator import CVRenderer
import json

with open("data/v5-devops-engineer.json") as f:
    profile = json.load(f)

renderer = CVRenderer(profile)
renderer.render("/app/output/v5-devops-engineer_classic_v4.pdf", "classic")
print(f"Generated PDF with {len(profile.get('experience', []))} experiences")