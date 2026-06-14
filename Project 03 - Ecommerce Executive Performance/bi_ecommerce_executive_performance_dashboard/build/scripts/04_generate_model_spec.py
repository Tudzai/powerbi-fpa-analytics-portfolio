from pathlib import Path

root = Path(__file__).resolve().parents[2]
for rel in ["model/relationship_map.md", "model/dax_measures.md", "build/config/page_map.json", "build/config/visual_map.json"]:
    path = root / rel
    print(f"{rel}: {'OK' if path.exists() else 'MISSING'}")
