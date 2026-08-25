import pandas as pd
import os
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "../../../data/professor_updated1.csv")
save_path = os.path.join(script_dir, "../../../data/interests_with_aliases.csv")


# 1. Clean interest text (remove non-breaking spaces, trailing dots/ellipses)
def clean_interest(text):
    text = text.replace('\xa0', ' ').strip()
    text = re.sub(r'[\.\…]+$', '', text).strip()
    return text

# 2. Function to map domain aliases and generate heuristic key phrases
def generate_aliases(interest):
    clean_text = clean_interest(interest)
    low_text = clean_text.lower()
    aliases = set()
    
    # Specific Domain Knowledge & Abbreviation Mappings
    known_mappings = {
        'computer vision': ['CV', 'Image Recognition', 'CNNs', 'Visual Perception', 'Object Detection'],
        'deep learning': ['DL', 'Deep Neural Networks', 'Representation Learning', 'Transformers', 'Convolutional Networks'],
        'machine learning': ['ML', 'Statistical Learning', 'Predictive Modeling', 'Supervised Learning', 'Pattern Recognition'],
        '3d computer vision': ['3D Vision', '3D Perception', 'Stereo Vision', 'Point Clouds', '3D Scene Reconstruction'],
        '3d shape analysis': ['3D Mesh Processing', '3D Geometric Modeling', 'Shape Descriptors', 'Point Cloud Analysis'],
        '5g and beyond': ['5G Communications', 'B5G', 'Next-Gen Wireless', '6G Networks'],
        '6g': ['6G Wireless', 'Terahertz Communications', 'Next-Gen Networks'],
        'ai/ml accelerator': ['Hardware Accelerators', 'NPU', 'TPU', 'AI Chips', 'Edge AI Hardware'],
        'additive manufacturing': ['3D Printing', 'Rapid Prototyping', 'Laser Powder Bed Fusion', 'Direct Energy Deposition'],
        'air pollution': ['Air Quality Monitoring', 'Particulate Matter', 'Aerosol Dynamics', 'Emission Control'],
        'antenna design': ['RF Antennas', 'Microstrip Antennas', 'Phased Array', 'Electromagnetic Radiators'],
        'bim': ['Building Information Modeling', 'Digital Twin in Construction', '3D CAD Modeling'],
        'bioelectronics': ['Biosensors', 'Biochips', 'Electrophysiology Devices', 'Implantable Electronics'],
        'biometrics': ['Facial Recognition', 'Fingerprint Verification', 'Iris Scanning', 'Behavioral Biometrics'],
        'brain-computer interface': ['BCI', 'Neural Interface', 'EEG Decoding', 'Neuromodulation'],
        'cfd': ['Computational Fluid Dynamics', 'Fluid Flow Simulation', 'Navier-Stokes Solvers'],
        'edge ai': ['Edge Computing', 'TinyML', 'On-Device AI', 'Edge Inference'],
        'image processing': ['Digital Image Processing', 'DIP', 'Image Enhancement', 'Segmentation'],
        'life cycle assessment': ['LCA', 'Environmental Impact Assessment', 'Cradle-to-Grave Analysis'],
        'scientific computations': ['Numerical Analysis', 'High-Performance Computing', 'HPC', 'Computational Science'],
        'water electrolysers': ['Hydrogen Generation', 'PEM Electrolysis', 'Water Splitting', 'Electrochemical Hydrogen']
    }
    
    # Direct dictionary check
    if low_text in known_mappings:
        for a in known_mappings[low_text]:
            aliases.add(a)

    # Automatic Acronym / Abbreviation Generation (e.g. Computer Vision -> CV)
    words = re.findall(r'\b[A-Za-z0-9]+\b', clean_text)
    if len(words) >= 2 and not clean_text.isupper():
        acronym = "".join([w[0].upper() for w in words if w.lower() not in ['and', 'of', 'in', 'for', 'with', 'the', 'to', 'or']])
        if len(acronym) >= 2:
            aliases.add(acronym)
            
    # Pattern-based expansion for domain keywords
    if 'learning' in low_text or 'ai' in low_text or 'intelligence' in low_text:
        aliases.add('Artificial Intelligence')
        aliases.add('Machine Intelligence')
    if 'vision' in low_text or 'image' in low_text:
        aliases.add('Visual Recognition')
        aliases.add('Image Analysis')
    if 'network' in low_text or 'communication' in low_text or 'wireless' in low_text:
        aliases.add('Telecommunications')
        aliases.add('Wireless Systems')
    if 'nano' in low_text:
        aliases.add('Nanotechnology')
        aliases.add('Nanoscale Science')
    if 'materials' in low_text or 'material' in low_text:
        aliases.add('Materials Science')
        aliases.add('Advanced Materials')
    if 'bio' in low_text:
        aliases.add('Biomedical Engineering')
        aliases.add('Biotechnology')
    if 'robot' in low_text or 'control' in low_text:
        aliases.add('Robotics & Automation')
        aliases.add('Autonomous Systems')
    if 'energy' in low_text or 'solar' in low_text or 'battery' in low_text or 'fuel' in low_text:
        aliases.add('Clean Energy')
        aliases.add('Renewable Energy Systems')

    # Fallback to research topic phrasing if no alias was derived
    if not aliases:
        aliases.add(f"{clean_text} Research")
        aliases.add(f"{clean_text} Technology")

    aliases.discard(clean_text)
    return clean_text, ", ".join(sorted(list(aliases)))


# 4. Generate Aliases for all entries
def generate_phrase():
    # 3. Read input CSV and extract unique interests
    df = pd.read_csv(csv_path)
    col_name = 'Interests' if 'Interests' in df.columns else 'Interest'

    raw_unique = (
        df[col_name].str.lower()
        .dropna()
        .str.split(',')
        .explode()
        .str.strip()
        .loc[lambda x: x != '']
        .unique()
    )

    results = []
    for item in raw_unique:
        cleaned, alias_str = generate_aliases(item)
        results.append({'Interest': cleaned, 'Aliases': alias_str})

    # 5. Create DataFrame, deduplicate and save to CSV
    df_out = pd.DataFrame(results)
    df_out = df_out.drop_duplicates(subset=['Interest']).sort_values(by='Interest').reset_index(drop=True)

    df_out.to_csv(save_path, index=False)
    print(f"      [OK] Exported {len(df_out)} rows to interests_with_aliases.csv")


if __name__ == "__main__":
    generate_phrase()
