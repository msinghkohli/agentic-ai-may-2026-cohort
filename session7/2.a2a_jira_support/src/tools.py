import os
from crewai.tools import tool
from pageindex_open import PIO
from .config import INDEX_DIR, DOCUMENTS_DIR, MODEL_ID

# Ensure indexes directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

# File Paths for Repair and Service Policy
repair_pdf = os.path.join(DOCUMENTS_DIR, "repair_service_policy.pdf")
repair_md = os.path.join(INDEX_DIR, "repair_service_policy.md")
repair_json = os.path.join(INDEX_DIR, "repair_service_policy.tree.json")

# File Paths for Product Lineup Specifications
product_pdf = os.path.join(DOCUMENTS_DIR, "product_lineup_specifications.pdf")
product_md = os.path.join(INDEX_DIR, "product_lineup_specifications.md")
product_json = os.path.join(INDEX_DIR, "product_lineup_specifications.tree.json")

# Initialize PIO instances
print("Initializing PageIndex (PIO) for Repair Policy...")
pio_repair = PIO(repair_pdf, model_name=MODEL_ID)
if os.path.exists(repair_md) and os.path.exists(repair_json):
    pio_repair.load_index(repair_md, repair_json)
else:
    pio_repair.build_index(save_files=False)
    pio_repair.save_index(repair_md, repair_json)

print("Initializing PageIndex (PIO) for Product specifications...")
pio_product = PIO(product_pdf, model_name=MODEL_ID)
if os.path.exists(product_md) and os.path.exists(product_json):
    pio_product.load_index(product_md, product_json)
else:
    pio_product.build_index(save_files=False)
    pio_product.save_index(product_md, product_json)


@tool("Search Repair and Service Policy")
def search_repair_policy(query: str) -> str:
    """Search the Repair & Service Policy document.
    Use this tool to find information about warranty policies, repair types (in-warranty vs out-of-warranty),
    cracked screen fees, service requirements, and return/repair rules.
    """
    try:
        return pio_repair.query(query, top_k=1)
    except Exception as e:
        return f"Error querying Repair & Service Policy: {e}"


@tool("Search Product Specifications and Lineup")
def search_product_specifications(query: str) -> str:
    """Search the Product Lineup & Specifications document.
    Use this tool to find details, technical specifications, display sizes, batteries, cameras, and features
    of Orange Electronics products (e.g., Orange Phone series, Orange Tab, Orange Book, Orange Watch, Orange Buds).
    """
    try:
        return pio_product.query(query, top_k=1)
    except Exception as e:
        return f"Error querying Product Specifications: {e}"
