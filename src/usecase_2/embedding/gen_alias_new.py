import ast
import json
import os
import re
import pandas as pd

from src.logger import logger

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(
    script_dir, "../../../data/professor_all_with_interests.csv"
)
save_path = os.path.join(
    script_dir, "../../../data/interest_domains_with_aliases.csv"
)


# 1. Clean interest domain text
def clean_interest(text: str) -> str:
    text = text.replace("\xa0", " ").strip()
    text = re.sub(r"[\.\…]+$", "", text).strip()
    return text


# 2. Function to map domain aliases and generate heuristic key phrases
def generate_aliases(interest: str):
    clean_text = clean_interest(interest)
    low_text = clean_text.lower()
    aliases = set()

    # Domain Knowledge & Abbreviation Mappings
    known_mappings = {
        "computer vision": [
            "CV",
            "Image Recognition",
            "CNNs",
            "Visual Perception",
            "Object Detection",
        ],
        "deep learning": [
            "DL",
            "Deep Neural Networks",
            "Representation Learning",
            "Transformers",
            "Convolutional Networks",
        ],
        "machine learning": [
            "ML",
            "Statistical Learning",
            "Predictive Modeling",
            "Supervised Learning",
            "Pattern Recognition",
        ],
        "3d computer vision": [
            "3D Vision",
            "3D Perception",
            "Stereo Vision",
            "Point Clouds",
            "3D Scene Reconstruction",
        ],
        "high energy physics": [
            "HEP",
            "Particle Physics",
            "Quantum Field Theory",
            "Collider Physics",
        ],
        "particle physics": [
            "Subatomic Physics",
            "Standard Model",
            "High Energy Physics",
        ],
        "materials science": [
            "Materials Engineering",
            "Advanced Materials",
            "Condensed Matter Physics",
        ],
        "environmental remediation": [
            "Environmental Cleanup",
            "Pollution Abatement",
            "Soil & Water Remediation",
        ],
        "biomedical engineering": [
            "BME",
            "Bioengineering",
            "Medical Devices",
            "Biomedical Technology",
        ],
        "water treatment and filtration": [
            "Water Purification",
            "Membrane Filtration",
            "Wastewater Treatment",
        ],
        "tissue engineering": [
            "Regenerative Medicine",
            "Scaffold Engineering",
            "Cellular Engineering",
        ],
        "cfd": [
            "Computational Fluid Dynamics",
            "Fluid Flow Simulation",
            "Navier-Stokes Solvers",
        ],
        "edge ai": ["Edge Computing", "TinyML", "On-Device AI", "Edge Inference"],
        "life cycle assessment": [
            "LCA",
            "Environmental Impact Assessment",
            "Cradle-to-Grave Analysis",
        ],
    }

    # Direct dictionary lookup
    if low_text in known_mappings:
        for a in known_mappings[low_text]:
            aliases.add(a)

    # Automatic Acronym / Abbreviation Generation (e.g. High Energy Physics -> HEP)
    words = re.findall(r"\b[A-Za-z0-9]+\b", clean_text)
    if len(words) >= 2 and not clean_text.isupper():
        acronym = "".join(
            [
                w[0].upper()
                for w in words
                if w.lower()
                not in ["and", "of", "in", "for", "with", "the", "to", "or", "&"]
            ]
        )
        if len(acronym) >= 2:
            aliases.add(acronym)

    # Keyword / Pattern-based expansion
    if (
        "learning" in low_text
        or "ai" in low_text
        or "intelligence" in low_text
    ):
        aliases.add("Artificial Intelligence")
        aliases.add("Machine Intelligence")
    if "vision" in low_text or "image" in low_text:
        aliases.add("Visual Recognition")
        aliases.add("Image Analysis")
    if (
        "network" in low_text
        or "communication" in low_text
        or "wireless" in low_text
    ):
        aliases.add("Telecommunications")
        aliases.add("Wireless Systems")
    if "physics" in low_text:
        aliases.add("Physical Sciences")
        aliases.add("Applied Physics")
    if "chem" in low_text or "synthesis" in low_text:
        aliases.add("Chemical Sciences")
        aliases.add("Applied Chemistry")
    if "bio" in low_text or "disease" in low_text:
        aliases.add("Biological Sciences")
        aliases.add("Life Sciences")
    if "materials" in low_text or "polymer" in low_text or "nano" in low_text:
        aliases.add("Materials Science")
        aliases.add("Advanced Materials")
    if "energy" in low_text or "fuel" in low_text or "solar" in low_text:
        aliases.add("Clean Energy")
        aliases.add("Energy Systems")
    if "water" in low_text or "pollution" in low_text or "environ" in low_text:
        aliases.add("Environmental Engineering")
        aliases.add("Sustainability")

    # Fallback to general academic phrasing if no alias was generated
    if not aliases:
        aliases.add(f"{clean_text} Research")
        aliases.add(f"{clean_text} Technology")
        logger.debug(
            f"No pattern alias matched for '{clean_text}'; using fallback."
        )

    aliases.discard(clean_text)
    return clean_text, ", ".join(sorted(list(aliases)))


# 3. Helper function to safely parse list strings in CSV columns
def parse_domain_list(val):
    if pd.isna(val) or not val:
        return []
    if isinstance(val, list):
        return val
    val_str = str(val).strip()
    # Try parsing stringified Python list or JSON array
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            return ast.literal_eval(val_str)
        except Exception:
            try:
                return json.loads(val_str)
            except Exception:
                pass
    # Fallback for comma-separated items
    return [item.strip().lower() for item in val_str.split(",") if item.strip().lower()]


# 4. Main function to extract domains and generate aliases
def generate_domain_aliases():
    logger.info(f"Loading professor interest domains from {csv_path}...")
    df = pd.read_csv(csv_path)

    target_col = (
        "Interest Domains"
        if "Interest Domains" in df.columns
        else ("Interests" if "Interests" in df.columns else "Interest")
    )

    # Flatten list entries and retrieve unique raw domain strings
    all_domains = []
    for val in df[target_col].dropna():
        domains = parse_domain_list(val)
        all_domains.extend([d for d in domains if isinstance(d, str) and d.strip()])

    unique_domains = sorted(list(set(all_domains)))
    logger.info(
        f"Found {len(unique_domains)} unique interest domains. Generating aliases..."
    )

    results = []
    for item in unique_domains:
        cleaned, alias_str = generate_aliases(item)
        results.append({"Interest": cleaned.lower(), "Aliases": alias_str.lower()})

    # Save DataFrame, deduplicate and output to CSV
    df_out = pd.DataFrame(results)
    before = len(df_out)
    df_out = (
        df_out.drop_duplicates(subset=["Interest"])
        .sort_values(by="Interest")
        .reset_index(drop=True)
    )

    if before != len(df_out):
        logger.debug(
            f"Dropped {before - len(df_out)} duplicate domain rows after cleaning."
        )

    df_out.to_csv(save_path, index=False)
    logger.info(
        f"[OK] Exported {len(df_out)} rows to {os.path.basename(save_path)}"
    )


if __name__ == "__main__":
    generate_domain_aliases()