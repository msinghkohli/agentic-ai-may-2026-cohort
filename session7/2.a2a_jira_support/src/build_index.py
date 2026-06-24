import os
from pageindex_open import PIO
from . config import INDEX_DIR, DOCUMENTS_DIR, MODEL_ID

def main():
    print("Building PageIndex tree structures...")
    os.makedirs(INDEX_DIR, exist_ok=True)

    repair_pdf = os.path.join(DOCUMENTS_DIR, "repair_service_policy.pdf")
    repair_md = os.path.join(INDEX_DIR, "repair_service_policy.md")
    repair_json = os.path.join(INDEX_DIR, "repair_service_policy.tree.json")

    product_pdf = os.path.join(DOCUMENTS_DIR, "product_lineup_specifications.pdf")
    product_md = os.path.join(INDEX_DIR, "product_lineup_specifications.md")
    product_json = os.path.join(INDEX_DIR, "product_lineup_specifications.tree.json")

    print(f"Indexing {repair_pdf}...")
    pio_repair = PIO(repair_pdf, model_name=MODEL_ID)
    pio_repair.build_index(save_files=False)
    pio_repair.save_index(repair_md, repair_json)
    print(f"Saved indexes to {INDEX_DIR}")

    print(f"Indexing {product_pdf}...")
    pio_product = PIO(product_pdf, model_name=MODEL_ID)
    pio_product.build_index(save_files=False)
    pio_product.save_index(product_md, product_json)
    print(f"Saved indexes to {INDEX_DIR}")

    print("Index build completed successfully.")

if __name__ == "__main__":
    main()
