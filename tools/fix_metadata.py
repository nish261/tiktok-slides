import json
from pathlib import Path
from collections import defaultdict
import sys

def fix_metadata(path):
    p = Path(path)
    if not p.exists():
        print(f"{path} not found")
        return
    
    print(f"Fixing metadata at {p.absolute()}")
    with open(p) as f:
        data = json.load(f)
        
    # 1. Assign 'all' to unassigned images
    count = 0
    for img, details in data.get("images", {}).items():
        if details.get("product") is None:
            details["product"] = "all"
            count += 1
    print(f"Assigned 'all' to {count} images.")
            
    # 2. Recalculate counts
    # counts[content_type][product_name] = count
    counts = defaultdict(lambda: defaultdict(int))
    
    # Count images (non-all)
    for img_name, img_data in data.get("images", {}).items():
        ct = img_data.get("content_type")
        prod = img_data.get("product")
        if ct and prod and prod != "all":
            counts[ct][prod] += 1

    # Count 'all' images per content type
    all_counts = defaultdict(int)
    for img_name, img_data in data.get("images", {}).items():
        ct = img_data.get("content_type")
        prod = img_data.get("product")
        if ct and prod == "all":
            all_counts[ct] += 1
            
    # Update counts in data['products']
    for ct, products_list in data.get("products", {}).items():
        for prod_info in products_list:
            name = prod_info["name"]
            # Calculate exactly as validator does
            actual = counts[ct][name] + all_counts[ct]
            prod_info["current_count"] = actual
            print(f"Updated {ct}/{name} count to {actual}")

    with open(p, "w") as f:
        json.dump(data, f, indent=2)
        
    print("Metadata updated.")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "tiktok-slides/sample_content/metadata.json"
    fix_metadata(path)