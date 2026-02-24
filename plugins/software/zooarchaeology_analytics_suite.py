"""
ZOOARCHAEOLOGY ANALYTICS SUITE v1.0 - COMPLETE ANALYSIS SOFTWARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ FAUNAL IDENTIFICATION: Taxa · Elements · Sides · Portions · von den Driesch codes
✓ TAPHONOMY: Behrensmeyer weathering · burning stages · surface condition
✓ BUTCHERY: Mark types · anatomical mapping · pattern analysis
✓ QUANTIFICATION: NISP · MNI · MNE · MAU · %survivorship
✓ STATISTICS: Context comparison · chi-square · richness · evenness
✓ AGING: Epiphyseal fusion · tooth wear (Grant, Payne) · dental eruption
✓ FTIR INTEGRATION: Crystallinity index · carbonate content · alteration assessment
✓ REPORTING: Publication-ready tables · charts · export to CSV/Excel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "zooarchaeology_analytics_suite",
    "name": "Zooarchaeology Analytics Suite",
    "icon": "📊",
    "description": "NISP · MNI · Taphonomy · Butchery · Aging · FTIR · Behrensmeyer · von den Driesch",
    "version": "1.0.0",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": ["openpyxl", "reportlab", "plotly"],
    "author": "Zooarch Team",
    "compact": True,
    "window_size": "1300x700"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import math
import json
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# OPTIONAL DEPENDENCIES
# ============================================================================

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ============================================================================
# ZOOARCHAEOLOGICAL REFERENCE DATABASES
# ============================================================================

# ===== TAXONOMIC REFERENCE =====
TAXA_DATABASE = {
    # Domestic mammals
    "Bos taurus": {"common": "Cattle", "size": "large", "order": "Artiodactyla", "family": "Bovidae"},
    "Ovis aries": {"common": "Sheep", "size": "medium", "order": "Artiodactyla", "family": "Bovidae"},
    "Capra hircus": {"common": "Goat", "size": "medium", "order": "Artiodactyla", "family": "Bovidae"},
    "Ovis/Capra": {"common": "Sheep/Goat", "size": "medium", "order": "Artiodactyla", "family": "Bovidae"},
    "Sus scrofa": {"common": "Pig", "size": "medium", "order": "Artiodactyla", "family": "Suidae"},
    "Equus caballus": {"common": "Horse", "size": "large", "order": "Perissodactyla", "family": "Equidae"},
    "Equus asinus": {"common": "Donkey", "size": "medium", "order": "Perissodactyla", "family": "Equidae"},
    "Camelus dromedarius": {"common": "Dromedary", "size": "large", "order": "Artiodactyla", "family": "Camelidae"},
    "Canis familiaris": {"common": "Dog", "size": "medium", "order": "Carnivora", "family": "Canidae"},
    "Felis catus": {"common": "Cat", "size": "small", "order": "Carnivora", "family": "Felidae"},

    # Wild mammals
    "Gazella gazella": {"common": "Mountain Gazelle", "size": "small", "order": "Artiodactyla", "family": "Bovidae"},
    "Dama mesopotamica": {"common": "Persian Fallow Deer", "size": "medium", "order": "Artiodactyla", "family": "Cervidae"},
    "Capreolus capreolus": {"common": "Roe Deer", "size": "small", "order": "Artiodactyla", "family": "Cervidae"},
    "Cervus elaphus": {"common": "Red Deer", "size": "large", "order": "Artiodactyla", "family": "Cervidae"},
    "Lepus capensis": {"common": "Cape Hare", "size": "small", "order": "Lagomorpha", "family": "Leporidae"},
    "Vulpes vulpes": {"common": "Red Fox", "size": "small", "order": "Carnivora", "family": "Canidae"},

    # Birds
    "Gallus gallus": {"common": "Chicken", "size": "small", "order": "Galliformes", "family": "Phasianidae"},
    "Meleagris gallopavo": {"common": "Turkey", "size": "medium", "order": "Galliformes", "family": "Phasianidae"},
    "Columba livia": {"common": "Rock Dove", "size": "small", "order": "Columbiformes", "family": "Columbidae"},
    "Struthio camelus": {"common": "Ostrich", "size": "very large", "order": "Struthioniformes", "family": "Struthionidae"},

    # Fish
    "Sparus aurata": {"common": "Gilthead Seabream", "size": "small", "order": "Perciformes", "family": "Sparidae"},
    "Dicentrarchus labrax": {"common": "European Seabass", "size": "medium", "order": "Perciformes", "family": "Moronidae"},

    # Unidentified
    "Mammalia indet.": {"common": "Unidentified Mammal", "size": "unknown", "order": "Mammalia", "family": "indet."},
    "Aves indet.": {"common": "Unidentified Bird", "size": "unknown", "order": "Aves", "family": "indet."},
    "Pisces indet.": {"common": "Unidentified Fish", "size": "unknown", "order": "Pisces", "family": "indet."},
    "Unidentified": {"common": "Unidentified", "size": "unknown", "order": "unknown", "family": "unknown"}
}

# ===== SKELETAL ELEMENT DATABASE =====
ELEMENT_DATABASE = {
    # Cranial elements
    "Horncore": {"category": "cranial", "element_group": "head", "paired": True, "epiphyses": []},
    "Antler": {"category": "cranial", "element_group": "head", "paired": True, "epiphyses": []},
    "Skull": {"category": "cranial", "element_group": "head", "paired": False, "epiphyses": []},
    "Maxilla": {"category": "cranial", "element_group": "head", "paired": True, "epiphyses": []},
    "Mandible": {"category": "cranial", "element_group": "head", "paired": True, "epiphyses": ["symphysis"]},
    "Tooth": {"category": "dental", "element_group": "tooth", "paired": True, "epiphyses": []},
    "Hyoid": {"category": "cranial", "element_group": "head", "paired": True, "epiphyses": []},

    # Axial elements
    "Atlas": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": []},
    "Axis": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": []},
    "Cervical vertebra": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": ["proximal", "distal"]},
    "Thoracic vertebra": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": ["proximal", "distal"]},
    "Lumbar vertebra": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": ["proximal", "distal"]},
    "Sacrum": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": []},
    "Caudal vertebra": {"category": "axial", "element_group": "vertebra", "paired": False, "epiphyses": ["proximal", "distal"]},
    "Rib": {"category": "axial", "element_group": "rib", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Sternum": {"category": "axial", "element_group": "sternum", "paired": False, "epiphyses": []},

    # Forelimb elements
    "Scapula": {"category": "forelimb", "element_group": "shoulder", "paired": True, "epiphyses": ["distal"]},
    "Humerus": {"category": "forelimb", "element_group": "upper forelimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Radius": {"category": "forelimb", "element_group": "lower forelimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Ulna": {"category": "forelimb", "element_group": "lower forelimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Carpal": {"category": "forelimb", "element_group": "carpal", "paired": True, "epiphyses": []},
    "Metacarpal": {"category": "forelimb", "element_group": "metapodial", "paired": True, "epiphyses": ["proximal", "distal"]},

    # Hindlimb elements
    "Pelvis": {"category": "hindlimb", "element_group": "pelvis", "paired": True, "epiphyses": ["acetabulum"]},
    "Femur": {"category": "hindlimb", "element_group": "upper hindlimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Patella": {"category": "hindlimb", "element_group": "knee", "paired": True, "epiphyses": []},
    "Tibia": {"category": "hindlimb", "element_group": "lower hindlimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Fibula": {"category": "hindlimb", "element_group": "lower hindlimb", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Tarsal": {"category": "hindlimb", "element_group": "tarsal", "paired": True, "epiphyses": []},
    "Astragalus": {"category": "hindlimb", "element_group": "tarsal", "paired": True, "epiphyses": []},
    "Calcaneus": {"category": "hindlimb", "element_group": "tarsal", "paired": True, "epiphyses": ["proximal"]},
    "Metatarsal": {"category": "hindlimb", "element_group": "metapodial", "paired": True, "epiphyses": ["proximal", "distal"]},

    # Feet
    "Metapodial": {"category": "feet", "element_group": "metapodial", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Phalanx 1": {"category": "feet", "element_group": "phalanx", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Phalanx 2": {"category": "feet", "element_group": "phalanx", "paired": True, "epiphyses": ["proximal", "distal"]},
    "Phalanx 3": {"category": "feet", "element_group": "phalanx", "paired": True, "epiphyses": []},
    "Sesamoid": {"category": "feet", "element_group": "sesamoid", "paired": True, "epiphyses": []},

    # Indeterminate
    "Long bone fragment": {"category": "indet", "element_group": "long bone", "paired": False, "epiphyses": []},
    "Flat bone fragment": {"category": "indet", "element_group": "flat bone", "paired": False, "epiphyses": []},
    "Indeterminate": {"category": "indet", "element_group": "indet", "paired": False, "epiphyses": []}
}

# ===== VON DEN DRIESCH (1976) MEASUREMENT CODES =====
VON_DEN_DRIESCH = {
    # General
    "GL": "Greatest length",
    "GLl": "Greatest length lateral",
    "GLm": "Greatest length medial",
    "GLP": "Greatest length of processus articularis",
    "GLF": "Greatest length of facies articularis",

    # Widths
    "Bp": "Breadth proximal",
    "Bd": "Breadth distal",
    "Dp": "Depth proximal",
    "Dd": "Depth distal",
    "SD": "Smallest breadth of diaphysis",
    "DD": "Smallest depth of diaphysis",

    # Scapula
    "SLC": "Smallest length of collum scapulae",
    "GLP": "Greatest length of processus articularis",
    "LG": "Length of glenoid cavity",
    "BG": "Breadth of glenoid cavity",

    # Humerus
    "BT": "Breadth trochlea",
    "HT": "Height trochlea",
    "Bd": "Breadth distal",

    # Radius
    "BFp": "Breadth of facies articularis proximalis",
    "Bp": "Breadth proximal",
    "Bd": "Breadth distal",

    # Ulna
    "LO": "Length of olecranon",
    "SDO": "Smallest depth of olecranon",
    "DPA": "Depth of processus anconaeus",
    "BPC": "Breadth of processus coronoideus",

    # Pelvis
    "LA": "Length of acetabulum",
    "LAR": "Length of acetabulum on rim",
    "SB": "Smallest breadth of ilium shaft",

    # Femur
    "Bp": "Breadth proximal",
    "DC": "Depth of caput",
    "Bd": "Breadth distal",

    # Tibia
    "Bp": "Breadth proximal",
    "Bd": "Breadth distal",
    "Dd": "Depth distal",

    # Astragalus
    "GLl": "Greatest length lateral",
    "GLm": "Greatest length medial",
    "Bd": "Breadth distal",
    "Dl": "Depth lateral",
    "Dm": "Depth medial",

    # Calcaneus
    "GL": "Greatest length",
    "GB": "Greatest breadth"
}

# ===== BEHRENSMEYER (1978) WEATHERING STAGES =====
WEATHERING_STAGES = {
    "0 - Fresh": {
        "code": 0,
        "description": "Greasy, cracking not present, perhaps with skin and muscle tissue",
        "diagnostic": "No cracking or flaking",
        "image_ref": "Behrensmeyer_1978_fig2a"
    },
    "1 - Slight cracking": {
        "code": 1,
        "description": "Cracking parallel to fiber structure (longitudinal) in long bones",
        "diagnostic": "Fine cracks, usually in bands",
        "image_ref": "Behrensmeyer_1978_fig2b"
    },
    "2 - Flaking": {
        "code": 2,
        "description": "Flaking of outer surface, cracks are present and usually mosaic",
        "diagnostic": "Exfoliation, crack edges angular",
        "image_ref": "Behrensmeyer_1978_fig2c"
    },
    "3 - Rough": {
        "code": 3,
        "description": "Bone surface rough, fibrous texture, weathering penetrates 1-1.5mm",
        "diagnostic": "Fibrous, splintery texture",
        "image_ref": "Behrensmeyer_1978_fig2d"
    },
    "4 - Splintering": {
        "code": 4,
        "description": "Splintering of bone, surface coarse and rough, weathering penetrates deep",
        "diagnostic": "Large splinters, fragments loose",
        "image_ref": "Behrensmeyer_1978_fig2e"
    },
    "5 - Crumbling": {
        "code": 5,
        "description": "Bone crumbling in situ, original shape difficult to determine",
        "diagnostic": "Unidentifiable fragments",
        "image_ref": "Behrensmeyer_1978_fig2f"
    }
}

# ===== BURNING STAGES =====
BURNING_STAGES = {
    "unburned": {
        "code": 0,
        "color": "cream/white",
        "temperature": "ambient",
        "description": "No evidence of heating, natural bone color"
    },
    "slightly burned": {
        "code": 1,
        "color": "tan/brown",
        "temperature": "<200°C",
        "description": "Patchy discoloration, organic material still present"
    },
    "carbonized": {
        "code": 2,
        "color": "black",
        "temperature": "200-400°C",
        "description": "Uniform black color, organic material charred"
    },
    "calcined": {
        "code": 3,
        "color": "white/grey",
        "temperature": ">600°C",
        "description": "Complete organic loss, bone mineral altered, brittle"
    }
}

# ===== BUTCHERY MARK TYPES =====
BUTCHERY_TYPES = {
    "cut": {
        "description": "Fine linear marks from slicing with sharp blade",
        "associated": "Skinning, disarticulation, filleting",
        "morphology": "V-shaped cross-section, length variable, fine"
    },
    "chop": {
        "description": "Broad, deep marks from heavy blade or cleaver",
        "associated": "Dismemberment, splitting",
        "morphology": "Broad U-shape, often with associated impact"
    },
    "saw": {
        "description": "Regular parallel striations from sawing",
        "associated": "Butchery with metal saws (historic/modern)",
        "morphology": "Regular, parallel, uniform"
    },
    "percussion": {
        "description": "Impact marks from hammerstone or tool",
        "associated": "Marrow extraction",
        "morphology": "Conchoidal scars, impact points, notches"
    },
    "scrape": {
        "description": "Shallow, broad marks from scraping periosteum",
        "associated": "Periosteum removal before breaking",
        "morphology": "Broad, shallow, multiple parallel"
    },
    "gnawing": {
        "description": "Tooth marks from carnivores or rodents",
        "associated": "Carnivore/rodent activity",
        "morphology": "Pits, punctures, furrows, scoring"
    }
}

# ===== FUSION STAGES (Silver 1969, modified) =====
FUSION_STAGES = {
    "unfused": {
        "description": "Epiphysis completely separate, no fusion line",
        "code": "U",
        "age_interpretation": "Juvenile/immature"
    },
    "fusing": {
        "description": "Epiphysis partially fused, fusion line visible",
        "code": "F",
        "age_interpretation": "Subadult/young adult"
    },
    "fused": {
        "description": "Complete fusion, fusion line obliterated",
        "code": "FD",
        "age_interpretation": "Adult"
    },
    "indeterminate": {
        "description": "Cannot determine fusion state",
        "code": "I",
        "age_interpretation": "Unknown"
    }
}

# ===== TOOTH WEAR STAGES =====
# Grant (1982) mandibular wear stages
GRANT_MANDIBULAR_STAGES = {
    "a": "Just coming into wear",
    "b": "Anterior and posterior crescents separate",
    "c": "Anterior and posterior crescents meet",
    "d": "Enamel still complete, dentine islands present",
    "e": "Enamel continuous except for narrow isthmus",
    "f": "Enamel isolated in two small lakes",
    "g": "Enamel as small isolated islands",
    "h": "Dentine only, enamel rim present",
    "j": "Dentine only, enamel incomplete",
    "k": "Root only"
}

# Payne (1973, 1987) for caprines
PAYNE_STAGES = {
    "Stage 1": "0-2 months: dP4 in wear, M1 unworn/unerupted",
    "Stage 2": "2-6 months: M1 in early wear",
    "Stage 3": "6-12 months: M1 well in wear, M2 unworn/unerupted",
    "Stage 4": "1-2 years: M2 in wear, M3 unworn/unerupted",
    "Stage 5": "2-3 years: M3 in early wear",
    "Stage 6": "3-4 years: M3 well in wear",
    "Stage 7": "4-6 years: M3 moderate wear",
    "Stage 8": "6-8 years: M3 heavy wear",
    "Stage 9": "8-10 years: M3 very heavy wear"
}

# ===== EPIPHYSEAL FUSION SEQUENCE (after Silver 1969, Zeder 2006) =====
FUSION_SEQUENCE = {
    "early_fusing": {
        "elements": ["Scapula (distal)", "Pelvis (acetabulum)", "Humerus (distal)", "Radius (proximal)"],
        "age_range": "6-10 months"
    },
    "middle_fusing": {
        "elements": ["Phalanx 1", "Phalanx 2", "Metacarpal (distal)", "Metatarsal (distal)", "Tibia (distal)"],
        "age_range": "18-24 months"
    },
    "late_fusing": {
        "elements": ["Humerus (proximal)", "Radius (distal)", "Ulna (proximal)", "Ulna (distal)", "Femur (proximal)", "Femur (distal)", "Tibia (proximal)", "Calcaneus", "Vertebrae"],
        "age_range": "30-48 months"
    }
}

# ============================================================================
# QUANTIFICATION CLASSES
# ============================================================================

class NISPCalculator:
    """Number of Identified Specimens calculations"""

    @staticmethod
    def calculate(records: List[Dict]) -> Dict:
        """Calculate NISP by various categories"""

        # By taxon
        taxon_nisp = {}
        for r in records:
            taxon = r.get('taxon', 'Unidentified')
            taxon_nisp[taxon] = taxon_nisp.get(taxon, 0) + 1

        # By context
        context_nisp = {}
        for r in records:
            ctx = r.get('context_type', 'unknown')
            context_nisp[ctx] = context_nisp.get(ctx, 0) + 1

        # By element
        element_nisp = {}
        for r in records:
            elem = r.get('element', 'Indeterminate')
            element_nisp[elem] = element_nisp.get(elem, 0) + 1

        # By taxon within context
        context_taxon = {}
        for r in records:
            ctx = r.get('context_type', 'unknown')
            taxon = r.get('taxon', 'Unidentified')
            if ctx not in context_taxon:
                context_taxon[ctx] = {}
            context_taxon[ctx][taxon] = context_taxon[ctx].get(taxon, 0) + 1

        return {
            'total_nisp': len(records),
            'taxon_nisp': taxon_nisp,
            'context_nisp': context_nisp,
            'element_nisp': element_nisp,
            'context_taxon': context_taxon,
            'taxon_percentages': {
                t: (c / len(records)) * 100
                for t, c in taxon_nisp.items()
            }
        }


class MNICalculator:
    """Minimum Number of Individuals calculations"""

    @staticmethod
    def calculate(records: List[Dict], element_col: str = 'element',
                 side_col: str = 'side', taxon_col: str = 'taxon') -> Dict:
        """
        Calculate MNI using paired elements and side counts
        Standard zooarchaeological method: largest number of the most frequent element for each taxon
        """

        # Group by taxon
        taxa = {}
        for r in records:
            taxon = r.get(taxon_col, 'Unidentified')
            if taxon not in taxa:
                taxa[taxon] = []
            taxa[taxon].append(r)

        mni_results = {}
        total_mni = 0

        for taxon, taxon_records in taxa.items():
            # Count elements by side
            element_counts = {}

            for r in taxon_records:
                elem = r.get(element_col, 'Indeterminate')
                side = r.get(side_col, 'indet')

                if elem not in element_counts:
                    element_counts[elem] = {'left': 0, 'right': 0, 'axial': 0}

                if side == 'left':
                    element_counts[elem]['left'] += 1
                elif side == 'right':
                    element_counts[elem]['right'] += 1
                else:  # axial or indet
                    element_counts[elem]['axial'] += 1

            # Calculate MNI for each element (max of left/right, plus axial)
            element_mni = {}
            for elem, counts in element_counts.items():
                if elem in ELEMENT_DATABASE and ELEMENT_DATABASE[elem]['paired']:
                    # Paired element: MNI = max(left, right)
                    element_mni[elem] = max(counts['left'], counts['right'])
                else:
                    # Axial/unpaired: MNI = axial count
                    element_mni[elem] = counts['axial']

            # Species MNI = max(element MNIs)
            if element_mni:
                mni = max(element_mni.values())
                mni_results[taxon] = {
                    'mni': mni,
                    'by_element': element_mni,
                    'elements_used': max(element_mni, key=element_mni.get)
                }
                total_mni += mni

        return {
            'by_taxon': mni_results,
            'total_mni': total_mni
        }


class MNECalculator:
    """Minimum Number of Elements calculations"""

    @staticmethod
    def calculate(records: List[Dict]) -> Dict:
        """Calculate MNE for skeletal elements"""

        # Group by element and portion
        element_portions = {}

        for r in records:
            elem = r.get('element', 'Indeterminate')
            portion = r.get('portion', 'fragment')

            key = f"{elem}_{portion}"
            element_portions[key] = element_portions.get(key, 0) + 1

        # Calculate MNE (simplified - actual MNE requires overlap criteria)
        mne = {}
        for key, count in element_portions.items():
            elem = key.split('_')[0]
            if elem not in mne:
                mne[elem] = 0
            mne[elem] += count

        return {
            'mne': mne,
            'total_mne': sum(mne.values())
        }


class MAUCalculator:
    """Minimum Animal Units calculations"""

    @staticmethod
    def calculate(mne: Dict, element_frequencies: Dict) -> Dict:
        """Calculate MAU = MNE / frequency in complete skeleton"""

        mau = {}
        for elem, count in mne.items():
            if elem in element_frequencies:
                mau[elem] = count / element_frequencies[elem]
            else:
                mau[elem] = count  # fallback

        # Normalize to %MAU (highest MAU = 100%)
        if mau:
            max_mau = max(mau.values())
            percent_mau = {e: (v / max_mau * 100) for e, v in mau.items()}
        else:
            percent_mau = {}

        return {
            'mau': mau,
            'percent_mau': percent_mau
        }


class DiversityCalculator:
    """Diversity indices for zooarchaeological assemblages"""

    @staticmethod
    def richness(taxon_counts: Dict) -> int:
        """Number of taxa"""
        return len(taxon_counts)

    @staticmethod
    def shannon(taxon_counts: Dict) -> float:
        """Shannon-Wiener diversity index H' = -Σ p_i ln(p_i)"""
        total = sum(taxon_counts.values())
        if total == 0:
            return 0

        h = 0
        for count in taxon_counts.values():
            p = count / total
            if p > 0:
                h -= p * math.log(p)

        return h

    @staticmethod
    def simpson(taxon_counts: Dict) -> float:
        """Simpson's diversity index D = Σ p_i²"""
        total = sum(taxon_counts.values())
        if total == 0:
            return 0

        d = 0
        for count in taxon_counts.values():
            p = count / total
            d += p * p

        return d

    @staticmethod
    def evenness(taxon_counts: Dict) -> float:
        """Pielou's evenness J' = H' / ln(richness)"""
        richness = DiversityCalculator.richness(taxon_counts)
        if richness <= 1:
            return 0

        h = DiversityCalculator.shannon(taxon_counts)
        return h / math.log(richness)


class ContextComparison:
    """Statistical comparison between contexts"""

    @staticmethod
    def chi_square(context1_counts: Dict, context2_counts: Dict) -> Dict:
        """Chi-square test for independence"""
        if not HAS_SCIPY:
            return {'error': 'scipy required for chi-square test'}

        # Get all unique taxa
        all_taxa = set(context1_counts.keys()) | set(context2_counts.keys())

        # Build contingency table
        table = []
        for taxon in sorted(all_taxa):
            row = [
                context1_counts.get(taxon, 0),
                context2_counts.get(taxon, 0)
            ]
            table.append(row)

        # Chi-square test
        try:
            chi2, p, dof, expected = stats.chi2_contingency(table)

            # Interpret p-value
            if p < 0.001:
                interpretation = "Highly significant difference (p < 0.001)"
            elif p < 0.01:
                interpretation = "Very significant difference (p < 0.01)"
            elif p < 0.05:
                interpretation = "Significant difference (p < 0.05)"
            else:
                interpretation = "No significant difference (p ≥ 0.05)"

            return {
                'chi2': chi2,
                'p_value': p,
                'dof': dof,
                'interpretation': interpretation,
                'expected': expected.tolist()
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def similarity_indices(context1_counts: Dict, context2_counts: Dict) -> Dict:
        """Calculate similarity indices between contexts"""

        # Jaccard index (presence/absence)
        taxa1 = set(context1_counts.keys())
        taxa2 = set(context2_counts.keys())
        intersection = len(taxa1 & taxa2)
        union = len(taxa1 | taxa2)
        jaccard = intersection / union if union > 0 else 0

        # Brainerd-Robinson coefficient
        total1 = sum(context1_counts.values())
        total2 = sum(context2_counts.values())

        if total1 == 0 or total2 == 0:
            br = 0
        else:
            # Convert to percentages
            pct1 = {t: (v / total1 * 100) for t, v in context1_counts.items()}
            pct2 = {t: (v / total2 * 100) for t, v in context2_counts.items()}

            # Calculate BR
            br_sum = 0
            all_taxa = set(pct1.keys()) | set(pct2.keys())
            for taxon in all_taxa:
                br_sum += abs(pct1.get(taxon, 0) - pct2.get(taxon, 0))
            br = 200 - br_sum

        return {
            'jaccard': jaccard,
            'brainerd_robinson': br,
            'shared_taxa': intersection,
            'total_taxa1': len(taxa1),
            'total_taxa2': len(taxa2)
        }


class FTIRInterpreter:
    """Interpret FTIR data for bone alteration"""

    @staticmethod
    def interpret_crystallinity(ci: float) -> Dict:
        """
        Crystallinity Index (Splitting Factor)
        Fresh bone: CI < 3.0
        Heated bone: CI increases with temperature
        Diagenetically altered: CI > 4.0
        """
        if ci < 3.0:
            return {
                'status': 'Well preserved',
                'interpretation': 'Low crystallinity, minimal diagenetic alteration',
                'confidence': 'high',
                'recommendation': 'Suitable for isotopic/chemical analysis'
            }
        elif ci < 3.5:
            return {
                'status': 'Slightly altered',
                'interpretation': 'Moderate crystallinity, some diagenetic overprint',
                'confidence': 'moderate',
                'recommendation': 'Caution for isotopic analysis'
            }
        elif ci < 4.0:
            return {
                'status': 'Moderately altered',
                'interpretation': 'Elevated crystallinity, significant diagenetic alteration',
                'confidence': 'low',
                'recommendation': 'Not suitable for isotopic analysis'
            }
        else:
            return {
                'status': 'Highly altered',
                'interpretation': 'High crystallinity, severe diagenesis or burning',
                'confidence': 'very low',
                'recommendation': 'Unsuitable for most analyses'
            }

    @staticmethod
    def interpret_carbonate(ratio: float) -> Dict:
        """
        Carbonate content (C/P ratio)
        Fresh bone: C/P ~0.1-0.2
        Diagenesis: C/P decreases
        """
        if ratio > 0.15:
            return {
                'status': 'Fresh',
                'interpretation': 'Well-preserved carbonate, minimal diagenesis',
                'preservation': 'good'
            }
        elif ratio > 0.1:
            return {
                'status': 'Moderate',
                'interpretation': 'Some carbonate loss, moderate preservation',
                'preservation': 'fair'
            }
        else:
            return {
                'status': 'Depleted',
                'interpretation': 'Significant carbonate loss, poor preservation',
                'preservation': 'poor'
            }

    @staticmethod
    def interpret_heating(ci: float, oh_band: bool = True) -> Dict:
        """
        Interpret heating based on FTIR
        """
        if ci > 4.5 and not oh_band:
            return {
                'status': 'Calcined',
                'temperature': '>600°C',
                'description': 'Complete organic loss, mineral recrystallization'
            }
        elif ci > 4.0:
            return {
                'status': 'Carbonized',
                'temperature': '300-600°C',
                'description': 'Organic matter charred, increased crystallinity'
            }
        elif ci > 3.5:
            return {
                'status': 'Heated',
                'temperature': '<300°C',
                'description': 'Some heating, minor crystallinity increase'
            }
        else:
            return {
                'status': 'Unheated',
                'temperature': 'ambient',
                'description': 'No evidence of heating'
            }


# ============================================================================
# MAIN PLUGIN - ZOOARCHAEOLOGY ANALYTICS SUITE
# ============================================================================

class ZooarchaeologyAnalyticsSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data storage
        self.records: List[Dict] = []
        self.filtered_records: List[Dict] = []

        # Quantification results
        self.nisp_results = {}
        self.mni_results = {}
        self.mne_results = {}
        self.mau_results = {}

        # UI Variables
        self.status_var = tk.StringVar(value="Zooarchaeology Analytics Suite v1.0 - Ready")
        self.record_count_var = tk.StringVar(value="0 records")

        # Filter variables
        self.filter_taxon_var = tk.StringVar(value="All")
        self.filter_context_var = tk.StringVar(value="All")
        self.filter_element_var = tk.StringVar(value="All")

        # Tree and display
        self.tree = None
        self.stats_text = None
        self.notebook = None

        self._check_dependencies()

    def _check_dependencies(self):
        self.has_scipy = HAS_SCIPY
        self.has_mpl = HAS_MPL
        self.has_openpyxl = HAS_OPENPYXL

    def open_window(self):
        """Open main plugin window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Zooarchaeology Analytics Suite v1.0")
        self.window.geometry("1300x700")
        self.window.minsize(1200, 650)

        self._build_ui()
        self.window.lift()

    def _build_ui(self):
        """Build the main interface with notebook tabs"""

        # ============ HEADER ============
        header = tk.Frame(self.window, bg="#2c3e50", height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📊", font=("Arial", 18),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Zooarchaeology Analytics Suite", font=("Arial", 13, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="v1.0 · NISP·MNI·Taphonomy·Butchery·Aging·FTIR", font=("Arial", 9),
                bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=10)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 9), bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # ============ TOOLBAR ============
        toolbar = tk.Frame(self.window, bg="#34495e", height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        ttk.Button(toolbar, text="📂 Import Data",
                  command=self._import_data).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📤 Export Results",
                  command=self._export_results).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📊 Calculate All",
                  command=self._calculate_all).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📈 Generate Charts",
                  command=self._generate_charts).pack(side=tk.LEFT, padx=2, pady=2)

        # Filter frame
        filter_frame = tk.Frame(toolbar, bg="#34495e")
        filter_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(filter_frame, text="Taxon:", bg="#34495e", fg="white",
                font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.filter_taxon = ttk.Combobox(filter_frame, textvariable=self.filter_taxon_var,
                                        width=15, state="readonly")
        self.filter_taxon.pack(side=tk.LEFT, padx=2)
        self.filter_taxon.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        tk.Label(filter_frame, text="Context:", bg="#34495e", fg="white",
                font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.filter_context = ttk.Combobox(filter_frame, textvariable=self.filter_context_var,
                                          width=12, state="readonly")
        self.filter_context.pack(side=tk.LEFT, padx=2)
        self.filter_context.bind('<<ComboboxSelected>>', lambda e: self._apply_filters())

        # ============ NOTEBOOK TABS ============
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Data Table
        self._create_data_tab()

        # Tab 2: NISP/MNI Quantification
        self._create_quantification_tab()

        # Tab 3: Taphonomy
        self._create_taphonomy_tab()

        # Tab 4: Butchery Analysis
        self._create_butchery_tab()

        # Tab 5: Aging/Fusion
        self._create_aging_tab()

        # Tab 6: FTIR Interpretation
        self._create_ftir_tab()

        # Tab 7: Context Comparison
        self._create_comparison_tab()

        # ============ STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#2c3e50", height=24)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.record_count_label = tk.Label(status_bar, textvariable=self.record_count_var,
                                          font=("Arial", 8), bg="#2c3e50", fg="white")
        self.record_count_label.pack(side=tk.LEFT, padx=8)

        deps_status = []
        if self.has_scipy: deps_status.append("📊 scipy")
        if self.has_mpl: deps_status.append("📈 matplotlib")
        tk.Label(status_bar, text=" · ".join(deps_status) if deps_status else "All dependencies OK",
                font=("Arial", 7), bg="#2c3e50", fg="white").pack(side=tk.RIGHT, padx=8)

    def _create_data_tab(self):
        """Tab 1: Data table with all records"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📋 Data Table")

        # Treeview frame
        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Columns
        columns = ('ID', 'Taxon', 'Element', 'Side', 'Portion', 'Weathering', 'Burning', 'Butchery', 'Context')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

        col_widths = [80, 150, 120, 60, 80, 100, 80, 60, 100]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        # Scrollbars
        yscroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Manual entry frame
        entry_frame = tk.LabelFrame(tab, text="Quick Add Record", font=("Arial", 9, "bold"),
                                    bg="white", padx=10, pady=10)
        entry_frame.pack(fill=tk.X, padx=5, pady=5)

        # Entry fields row
        fields_frame = tk.Frame(entry_frame, bg="white")
        fields_frame.pack(fill=tk.X, pady=5)

        self.quick_taxon = ttk.Combobox(fields_frame, values=list(TAXA_DATABASE.keys()), width=20)
        self.quick_taxon.grid(row=0, column=1, padx=5)
        self.quick_taxon.set("Select taxon")

        self.quick_element = ttk.Combobox(fields_frame, values=list(ELEMENT_DATABASE.keys()), width=20)
        self.quick_element.grid(row=0, column=3, padx=5)
        self.quick_element.set("Select element")

        tk.Label(fields_frame, text="Taxon:", bg="white").grid(row=0, column=0, padx=5)
        tk.Label(fields_frame, text="Element:", bg="white").grid(row=0, column=2, padx=5)

        tk.Label(fields_frame, text="Side:", bg="white").grid(row=1, column=0, padx=5, pady=5)
        self.quick_side = ttk.Combobox(fields_frame, values=['left', 'right', 'axial', 'indet'], width=10)
        self.quick_side.grid(row=1, column=1, padx=5, pady=5)
        self.quick_side.set('indet')

        tk.Label(fields_frame, text="Context:", bg="white").grid(row=1, column=2, padx=5, pady=5)
        self.quick_context = ttk.Entry(fields_frame, width=20)
        self.quick_context.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(entry_frame, text="➕ Add Record",
                  command=self._add_quick_record).pack(pady=5)

    def _create_quantification_tab(self):
        """Tab 2: NISP/MNI quantification"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 NISP/MNI")

        # Control buttons
        ctrl_frame = tk.Frame(tab, bg="#f8f9fa", height=40)
        ctrl_frame.pack(fill=tk.X)
        ctrl_frame.pack_propagate(False)

        ttk.Button(ctrl_frame, text="🔄 Calculate NISP",
                  command=self._calculate_nisp).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="🔄 Calculate MNI",
                  command=self._calculate_mni).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="🔄 Calculate MNE/MAU",
                  command=self._calculate_mne).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ctrl_frame, text="📈 Diversity Indices",
                  command=self._calculate_diversity).pack(side=tk.LEFT, padx=5, pady=5)

        # Results display
        self.quant_text = tk.Text(tab, wrap=tk.WORD, font=("Courier", 10),
                                   bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.quant_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_taphonomy_tab(self):
        """Tab 3: Taphonomic analysis"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚠️ Taphonomy")

        # Behrensmeyer weathering reference
        weather_frame = tk.LabelFrame(tab, text="Behrensmeyer (1978) Weathering Stages",
                                      font=("Arial", 10, "bold"), padx=10, pady=10)
        weather_frame.pack(fill=tk.X, padx=5, pady=5)

        weather_text = tk.Text(weather_frame, height=8, wrap=tk.WORD, font=("Arial", 9))
        weather_text.pack(fill=tk.X)

        for stage, data in WEATHERING_STAGES.items():
            weather_text.insert(tk.END, f"{stage}: {data['description']}\n")
        weather_text.config(state=tk.DISABLED)

        # Burning stages
        burn_frame = tk.LabelFrame(tab, text="Burning Stages", font=("Arial", 10, "bold"),
                                   padx=10, pady=10)
        burn_frame.pack(fill=tk.X, padx=5, pady=5)

        burn_text = tk.Text(burn_frame, height=4, wrap=tk.WORD, font=("Arial", 9))
        burn_text.pack(fill=tk.X)

        for stage, data in BURNING_STAGES.items():
            burn_text.insert(tk.END, f"{stage}: {data['color']} - {data['temperature']} - {data['description']}\n")
        burn_text.config(state=tk.DISABLED)

        # Taphonomic summary
        summary_frame = tk.LabelFrame(tab, text="Taphonomic Summary", font=("Arial", 10, "bold"),
                                      padx=10, pady=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(summary_frame, text="📊 Generate Taphonomic Summary",
                  command=self._taphonomy_summary).pack(pady=5)

        self.taph_text = tk.Text(summary_frame, wrap=tk.WORD, font=("Courier", 10),
                                  height=10, bg="white")
        self.taph_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_butchery_tab(self):
        """Tab 4: Butchery analysis"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔪 Butchery")

        # Butchery types reference
        type_frame = tk.LabelFrame(tab, text="Butchery Mark Types", font=("Arial", 10, "bold"),
                                   padx=10, pady=10)
        type_frame.pack(fill=tk.X, padx=5, pady=5)

        type_text = tk.Text(type_frame, height=6, wrap=tk.WORD, font=("Arial", 9))
        type_text.pack(fill=tk.X)

        for mark, data in BUTCHERY_TYPES.items():
            type_text.insert(tk.END, f"{mark}: {data['description']} - {data['associated']}\n")
        type_text.config(state=tk.DISABLED)

        # Butchery analysis
        analysis_frame = tk.LabelFrame(tab, text="Butchery Analysis", font=("Arial", 10, "bold"),
                                       padx=10, pady=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(analysis_frame, text="📊 Analyze Butchery Patterns",
                  command=self._butchery_analysis).pack(pady=5)

        self.butchery_text = tk.Text(analysis_frame, wrap=tk.WORD, font=("Courier", 10),
                                      height=10, bg="white")
        self.butchery_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_aging_tab(self):
        """Tab 5: Aging/fusion analysis"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📅 Aging")

        # Fusion sequence reference
        fusion_frame = tk.LabelFrame(tab, text="Epiphyseal Fusion Sequence (Silver 1969)",
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        fusion_frame.pack(fill=tk.X, padx=5, pady=5)

        fusion_text = tk.Text(fusion_frame, height=6, wrap=tk.WORD, font=("Arial", 9))
        fusion_text.pack(fill=tk.X)

        for stage, data in FUSION_SEQUENCE.items():
            fusion_text.insert(tk.END, f"{stage.replace('_', ' ').title()}: {data['age_range']}\n")
            for elem in data['elements'][:3]:
                fusion_text.insert(tk.END, f"  • {elem}\n")
        fusion_text.config(state=tk.DISABLED)

        # Aging analysis
        aging_frame = tk.LabelFrame(tab, text="Age Profile Analysis", font=("Arial", 10, "bold"),
                                    padx=10, pady=10)
        aging_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(aging_frame, text="📊 Generate Age Profile",
                  command=self._age_analysis).pack(pady=5)

        self.aging_text = tk.Text(aging_frame, wrap=tk.WORD, font=("Courier", 10),
                                   height=10, bg="white")
        self.aging_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_ftir_tab(self):
        """Tab 6: FTIR interpretation"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🧪 FTIR")

        # Input frame
        input_frame = tk.LabelFrame(tab, text="FTIR Data Input", font=("Arial", 10, "bold"),
                                    padx=10, pady=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(input_frame, text="Crystallinity Index (CI/SF):").grid(row=0, column=0, padx=5, pady=5)
        self.ftir_ci = tk.Entry(input_frame, width=10)
        self.ftir_ci.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Carbonate/Phosphate Ratio (C/P):").grid(row=1, column=0, padx=5, pady=5)
        self.ftir_cp = tk.Entry(input_frame, width=10)
        self.ftir_cp.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="OH Band Present?").grid(row=2, column=0, padx=5, pady=5)
        self.ftir_oh = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Yes", variable=self.ftir_oh).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="🔬 Interpret FTIR",
                  command=self._interpret_ftir).grid(row=3, column=0, columnspan=2, pady=10)

        # Results frame
        results_frame = tk.LabelFrame(tab, text="FTIR Interpretation", font=("Arial", 10, "bold"),
                                      padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ftir_text = tk.Text(results_frame, wrap=tk.WORD, font=("Courier", 10),
                                  height=10, bg="white")
        self.ftir_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_comparison_tab(self):
        """Tab 7: Context comparison"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Context Comparison")

        # Control frame
        ctrl_frame = tk.Frame(tab, bg="#f8f9fa", height=40)
        ctrl_frame.pack(fill=tk.X)
        ctrl_frame.pack_propagate(False)

        tk.Label(ctrl_frame, text="Context 1:", bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.comp_ctx1 = ttk.Combobox(ctrl_frame, width=20)
        self.comp_ctx1.pack(side=tk.LEFT, padx=5)

        tk.Label(ctrl_frame, text="Context 2:", bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.comp_ctx2 = ttk.Combobox(ctrl_frame, width=20)
        self.comp_ctx2.pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl_frame, text="📊 Compare Contexts",
                  command=self._compare_contexts).pack(side=tk.LEFT, padx=10)

        # Results frame
        results_frame = tk.LabelFrame(tab, text="Comparison Results", font=("Arial", 10, "bold"),
                                      padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.comp_text = tk.Text(results_frame, wrap=tk.WORD, font=("Courier", 10),
                                  height=20, bg="white")
        self.comp_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ============================================================================
    # DATA IMPORT METHODS
    # ============================================================================

    def _import_data(self):
        """Import data from CSV/Excel"""
        path = filedialog.askopenfilename(
            title="Import Zooarchaeological Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("JSON", "*.json")]
        )

        if not path:
            return

        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            elif path.endswith('.xlsx'):
                if not self.has_openpyxl:
                    messagebox.showerror("Error", "openpyxl required for Excel files")
                    return
                df = pd.read_excel(path)
            else:
                with open(path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.records = data
                self._update_ui()
                return

            # Convert DataFrame to records
            self.records = df.to_dict('records')

            self._update_ui()
            self.status_var.set(f"✅ Imported {len(self.records)} records")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _add_quick_record(self):
        """Add a quick record from the entry form"""
        record = {
            'id': f"REC_{len(self.records)+1:04d}",
            'taxon': self.quick_taxon.get(),
            'element': self.quick_element.get(),
            'side': self.quick_side.get(),
            'portion': 'complete',  # default
            'weathering_stage': '0 - Fresh',
            'burning_stage': 'unburned',
            'butchery_present': False,
            'context_type': self.quick_context.get() or 'unknown',
            'date_added': datetime.now().isoformat()
        }

        self.records.append(record)
        self._update_tree()
        self.record_count_var.set(f"{len(self.records)} records")
        self.status_var.set(f"✅ Added record {record['id']}")

        # Clear form
        self.quick_taxon.set("Select taxon")
        self.quick_element.set("Select element")
        self.quick_context.set("")

    def _update_ui(self):
        """Update UI after data import"""
        self._update_tree()
        self._update_filters()
        self.record_count_var.set(f"{len(self.records)} records")

    def _update_tree(self):
        """Update the data table"""
        if not self.tree:
            return

        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add records
        for r in self.records[-1000:]:  # Show last 1000 for performance
            self.tree.insert('', 0, values=(
                r.get('id', '')[:8],
                r.get('taxon', '')[:20],
                r.get('element', '')[:15],
                r.get('side', ''),
                r.get('portion', ''),
                r.get('weathering_stage', '')[:10],
                r.get('burning_stage', '')[:10],
                '✓' if r.get('butchery_present', False) else '',
                r.get('context_type', '')[:10]
            ))

    def _update_filters(self):
        """Update filter dropdowns"""
        # Get unique taxa
        taxa = set(r.get('taxon', 'Unidentified') for r in self.records)
        contexts = set(r.get('context_type', 'unknown') for r in self.records)

        self.filter_taxon['values'] = ['All'] + sorted(taxa)
        self.filter_context['values'] = ['All'] + sorted(contexts)

        self.comp_ctx1['values'] = sorted(contexts)
        self.comp_ctx2['values'] = sorted(contexts)

    def _apply_filters(self):
        """Apply filters to records"""
        taxon = self.filter_taxon_var.get()
        context = self.filter_context_var.get()

        self.filtered_records = []
        for r in self.records:
            if taxon != 'All' and r.get('taxon') != taxon:
                continue
            if context != 'All' and r.get('context_type') != context:
                continue
            self.filtered_records.append(r)

    # ============================================================================
    # QUANTIFICATION METHODS
    # ============================================================================

    def _calculate_all(self):
        """Calculate all quantification metrics"""
        self._calculate_nisp()
        self._calculate_mni()
        self._calculate_mne()
        self._calculate_diversity()
        self.status_var.set("✅ All calculations complete")

    def _calculate_nisp(self):
        """Calculate NISP"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            self.quant_text.delete(1.0, tk.END)
            self.quant_text.insert(tk.END, "No records to analyze")
            return

        self.nisp_results = NISPCalculator.calculate(records)

        # Format output
        output = []
        output.append("=" * 60)
        output.append("NISP (Number of Identified Specimens)")
        output.append("=" * 60)
        output.append(f"Total specimens: {self.nisp_results['total_nisp']}")
        output.append("")

        output.append("BY TAXON:")
        output.append("-" * 40)
        for taxon, count in sorted(self.nisp_results['taxon_nisp'].items(),
                                   key=lambda x: x[1], reverse=True):
            pct = self.nisp_results['taxon_percentages'][taxon]
            output.append(f"  {taxon:<30} {count:3d} ({pct:5.1f}%)")

        output.append("")
        output.append("BY CONTEXT:")
        output.append("-" * 40)
        for ctx, count in sorted(self.nisp_results['context_nisp'].items(),
                                 key=lambda x: x[1], reverse=True):
            pct = (count / self.nisp_results['total_nisp']) * 100
            output.append(f"  {ctx:<20} {count:3d} ({pct:5.1f}%)")

        self.quant_text.delete(1.0, tk.END)
        self.quant_text.insert(tk.END, "\n".join(output))

    def _calculate_mni(self):
        """Calculate MNI"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            return

        self.mni_results = MNICalculator.calculate(records)

        # Append to quant_text
        self.quant_text.insert(tk.END, "\n\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, "MNI (Minimum Number of Individuals)\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, f"Total MNI: {self.mni_results['total_mni']}\n\n")

        for taxon, data in self.mni_results['by_taxon'].items():
            self.quant_text.insert(tk.END, f"{taxon}: MNI = {data['mni']} ")
            self.quant_text.insert(tk.END, f"(based on {data['elements_used']})\n")

    def _calculate_mne(self):
        """Calculate MNE and MAU"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            return

        self.mne_results = MNECalculator.calculate(records)

        # Element frequencies in complete skeleton (simplified)
        elem_freq = {
            'Mandible': 2, 'Maxilla': 2, 'Scapula': 2, 'Humerus': 2,
            'Radius': 2, 'Ulna': 2, 'Metacarpal': 2, 'Pelvis': 2,
            'Femur': 2, 'Tibia': 2, 'Metatarsal': 2, 'Astragalus': 2,
            'Calcaneus': 2, 'Phalanx 1': 8, 'Phalanx 2': 8, 'Phalanx 3': 8
        }

        self.mau_results = MAUCalculator.calculate(self.mne_results['mne'], elem_freq)

        # Append to quant_text
        self.quant_text.insert(tk.END, "\n\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, "MNE/MAU (Minimum Number of Elements/Animal Units)\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, f"Total MNE: {self.mne_results['total_mne']}\n\n")
        self.quant_text.insert(tk.END, "Element     MNE    MAU    %MAU\n")
        self.quant_text.insert(tk.END, "-" * 40 + "\n")

        for elem, mne in sorted(self.mne_results['mne'].items(), key=lambda x: x[1], reverse=True)[:15]:
            mau = self.mau_results['mau'].get(elem, 0)
            pct = self.mau_results['percent_mau'].get(elem, 0)
            self.quant_text.insert(tk.END, f"{elem:<12} {mne:<6} {mau:<6.1f} {pct:<6.1f}%\n")

    def _calculate_diversity(self):
        """Calculate diversity indices"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            return

        # Get taxon counts
        taxon_counts = {}
        for r in records:
            taxon = r.get('taxon', 'Unidentified')
            taxon_counts[taxon] = taxon_counts.get(taxon, 0) + 1

        # Calculate indices
        richness = DiversityCalculator.richness(taxon_counts)
        shannon = DiversityCalculator.shannon(taxon_counts)
        simpson = DiversityCalculator.simpson(taxon_counts)
        evenness = DiversityCalculator.evenness(taxon_counts)

        # Append to quant_text
        self.quant_text.insert(tk.END, "\n\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, "Diversity Indices\n")
        self.quant_text.insert(tk.END, "=" * 60 + "\n")
        self.quant_text.insert(tk.END, f"Taxonomic richness: {richness}\n")
        self.quant_text.insert(tk.END, f"Shannon-Wiener H': {shannon:.3f}\n")
        self.quant_text.insert(tk.END, f"Simpson's D: {simpson:.3f}\n")
        self.quant_text.insert(tk.END, f"Pielou's evenness J': {evenness:.3f}\n")

    def _taphonomy_summary(self):
        """Generate taphonomic summary"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            self.taph_text.delete(1.0, tk.END)
            self.taph_text.insert(tk.END, "No records to analyze")
            return

        # Count weathering stages
        weathering = {}
        burning = {}

        for r in records:
            w = r.get('weathering_stage', 'unknown')
            weathering[w] = weathering.get(w, 0) + 1

            b = r.get('burning_stage', 'unknown')
            burning[b] = burning.get(b, 0) + 1

        output = []
        output.append("=" * 60)
        output.append("TAPHONOMIC SUMMARY")
        output.append("=" * 60)
        output.append(f"Total specimens analyzed: {len(records)}")
        output.append("")

        output.append("WEATHERING STAGES (Behrensmeyer 1978):")
        output.append("-" * 40)
        for stage in sorted(WEATHERING_STAGES.keys()):
            count = weathering.get(stage, 0)
            pct = (count / len(records)) * 100
            output.append(f"  {stage:<20} {count:3d} ({pct:5.1f}%)")

        output.append("")
        output.append("BURNING STAGES:")
        output.append("-" * 40)
        for stage in sorted(BURNING_STAGES.keys()):
            count = burning.get(stage, 0)
            pct = (count / len(records)) * 100
            output.append(f"  {stage:<15} {count:3d} ({pct:5.1f}%)")

        self.taph_text.delete(1.0, tk.END)
        self.taph_text.insert(tk.END, "\n".join(output))

    def _butchery_analysis(self):
        """Analyze butchery patterns"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            self.butchery_text.delete(1.0, tk.END)
            self.butchery_text.insert(tk.END, "No records to analyze")
            return

        # Count butchery by type and element
        butchery_records = [r for r in records if r.get('butchery_present', False)]

        butchery_by_type = {}
        butchery_by_element = {}

        for r in butchery_records:
            btype = r.get('butchery_type', 'unknown')
            butchery_by_type[btype] = butchery_by_type.get(btype, 0) + 1

            elem = r.get('element', 'unknown')
            butchery_by_element[elem] = butchery_by_element.get(elem, 0) + 1

        output = []
        output.append("=" * 60)
        output.append("BUTCHERY ANALYSIS")
        output.append("=" * 60)
        output.append(f"Total specimens with butchery: {len(butchery_records)}")
        output.append(f"Percentage of assemblage: {(len(butchery_records)/len(records))*100:.1f}%")
        output.append("")

        output.append("BY BUTCHERY TYPE:")
        output.append("-" * 40)
        for btype, count in sorted(butchery_by_type.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(butchery_records)) * 100
            desc = BUTCHERY_TYPES.get(btype, {}).get('description', '')
            output.append(f"  {btype:<12} {count:3d} ({pct:5.1f}%) - {desc[:30]}")

        output.append("")
        output.append("BY ELEMENT:")
        output.append("-" * 40)
        for elem, count in sorted(butchery_by_element.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (count / len(butchery_records)) * 100
            output.append(f"  {elem:<15} {count:3d} ({pct:5.1f}%)")

        self.butchery_text.delete(1.0, tk.END)
        self.butchery_text.insert(tk.END, "\n".join(output))

    def _age_analysis(self):
        """Generate age profile from fusion data"""
        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            self.aging_text.delete(1.0, tk.END)
            self.aging_text.insert(tk.END, "No records to analyze")
            return

        # Count fusion stages
        fusion_counts = {'unfused': 0, 'fusing': 0, 'fused': 0}

        for r in records:
            fusion = r.get('fusion_state', 'indeterminate')
            if fusion in fusion_counts:
                fusion_counts[fusion] += 1

        output = []
        output.append("=" * 60)
        output.append("AGE PROFILE ANALYSIS")
        output.append("=" * 60)
        output.append(f"Total specimens with fusion data: {sum(fusion_counts.values())}")
        output.append("")

        output.append("FUSION STAGES:")
        output.append("-" * 40)
        total = sum(fusion_counts.values())
        if total > 0:
            for stage, count in fusion_counts.items():
                pct = (count / total) * 100
                output.append(f"  {stage:<10} {count:3d} ({pct:5.1f}%) - {FUSION_STAGES[stage]['description']}")

        # Interpret age structure
        if fusion_counts['unfused'] > fusion_counts['fused']:
            output.append("\nINTERPRETATION: High proportion of unfused elements -")
            output.append("  Juvenile-dominated assemblage, possibly from")
            output.append("  herd management focusing on young animals")
        elif fusion_counts['fused'] > fusion_counts['unfused'] * 2:
            output.append("\nINTERPRETATION: High proportion of fused elements -")
            output.append("  Adult-dominated assemblage, possibly from")
            output.append("  culling of mature animals")
        else:
            output.append("\nINTERPRETATION: Mixed age profile -")
            output.append("  Mortality reflects natural population structure")

        self.aging_text.delete(1.0, tk.END)
        self.aging_text.insert(tk.END, "\n".join(output))

    def _interpret_ftir(self):
        """Interpret FTIR data"""
        try:
            ci = float(self.ftir_ci.get()) if self.ftir_ci.get() else None
            cp = float(self.ftir_cp.get()) if self.ftir_cp.get() else None
            oh = self.ftir_oh.get()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return

        output = []
        output.append("=" * 60)
        output.append("FTIR SPECTROSCOPY INTERPRETATION")
        output.append("=" * 60)

        if ci:
            output.append(f"\nCrystallinity Index (CI/SF): {ci:.2f}")
            ci_result = FTIRInterpreter.interpret_crystallinity(ci)
            output.append(f"  → {ci_result['status']}")
            output.append(f"     {ci_result['interpretation']}")
            output.append(f"     Recommendation: {ci_result['recommendation']}")

        if cp:
            output.append(f"\nCarbonate/Phosphate Ratio: {cp:.2f}")
            cp_result = FTIRInterpreter.interpret_carbonate(cp)
            output.append(f"  → {cp_result['status']} preservation")
            output.append(f"     {cp_result['interpretation']}")

        if ci:
            heat_result = FTIRInterpreter.interpret_heating(ci, oh)
            output.append(f"\nHeating Assessment:")
            output.append(f"  → {heat_result['status']} ({heat_result['temperature']})")
            output.append(f"     {heat_result['description']}")

        self.ftir_text.delete(1.0, tk.END)
        self.ftir_text.insert(tk.END, "\n".join(output))

    def _compare_contexts(self):
        """Compare two contexts statistically"""
        ctx1 = self.comp_ctx1.get()
        ctx2 = self.comp_ctx2.get()

        if not ctx1 or not ctx2:
            messagebox.showwarning("Warning", "Please select two contexts")
            return

        # Get records for each context
        ctx1_records = [r for r in self.records if r.get('context_type') == ctx1]
        ctx2_records = [r for r in self.records if r.get('context_type') == ctx2]

        if not ctx1_records or not ctx2_records:
            messagebox.showwarning("Warning", "One or both contexts have no records")
            return

        # Get taxon counts
        ctx1_counts = {}
        for r in ctx1_records:
            taxon = r.get('taxon', 'Unidentified')
            ctx1_counts[taxon] = ctx1_counts.get(taxon, 0) + 1

        ctx2_counts = {}
        for r in ctx2_records:
            taxon = r.get('taxon', 'Unidentified')
            ctx2_counts[taxon] = ctx2_counts.get(taxon, 0) + 1

        # Calculate statistics
        chi2_result = ContextComparison.chi_square(ctx1_counts, ctx2_counts)
        similarity = ContextComparison.similarity_indices(ctx1_counts, ctx2_counts)

        output = []
        output.append("=" * 60)
        output.append(f"CONTEXT COMPARISON: {ctx1} vs {ctx2}")
        output.append("=" * 60)
        output.append(f"Context 1: {len(ctx1_records)} specimens")
        output.append(f"Context 2: {len(ctx2_records)} specimens")
        output.append("")

        output.append("TAXON COMPOSITION:")
        output.append("-" * 40)
        all_taxa = set(ctx1_counts.keys()) | set(ctx2_counts.keys())
        for taxon in sorted(all_taxa)[:15]:
            c1 = ctx1_counts.get(taxon, 0)
            c2 = ctx2_counts.get(taxon, 0)
            output.append(f"  {taxon:<25} {c1:3d} vs {c2:3d}")

        output.append("")
        output.append("STATISTICAL TESTS:")
        output.append("-" * 40)
        if 'error' not in chi2_result:
            output.append(f"Chi-square: χ² = {chi2_result['chi2']:.2f}, df = {chi2_result['dof']}")
            output.append(f"p-value = {chi2_result['p_value']:.4f}")
            output.append(f"Interpretation: {chi2_result['interpretation']}")
        else:
            output.append(f"Chi-square: {chi2_result['error']}")

        output.append("")
        output.append("SIMILARITY INDICES:")
        output.append("-" * 40)
        output.append(f"Jaccard index: {similarity['jaccard']:.3f}")
        output.append(f"Brainerd-Robinson coefficient: {similarity['brainerd_robinson']:.1f}")
        output.append(f"Shared taxa: {similarity['shared_taxa']}")

        self.comp_text.delete(1.0, tk.END)
        self.comp_text.insert(tk.END, "\n".join(output))

    def _generate_charts(self):
        """Generate visualizations"""
        if not self.has_mpl:
            messagebox.showerror("Error", "matplotlib required for charts")
            return

        records = self.filtered_records if self.filtered_records else self.records

        if not records:
            return

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. Taxon distribution
        taxon_counts = {}
        for r in records:
            taxon = r.get('taxon', 'Unidentified')
            taxon_counts[taxon] = taxon_counts.get(taxon, 0) + 1

        # Top 10 taxa
        top_taxa = sorted(taxon_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        if top_taxa:
            names, counts = zip(*top_taxa)
            axes[0, 0].barh(names, counts)
            axes[0, 0].set_title('Top 10 Taxa by NISP')
            axes[0, 0].set_xlabel('NISP')

        # 2. Element distribution
        element_counts = {}
        for r in records:
            elem = r.get('element', 'Indeterminate')
            element_counts[elem] = element_counts.get(elem, 0) + 1

        top_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        if top_elements:
            names, counts = zip(*top_elements)
            axes[0, 1].bar(names, counts)
            axes[0, 1].set_title('Top 10 Elements')
            axes[0, 1].set_xticklabels(names, rotation=45, ha='right')
            axes[0, 1].set_ylabel('NISP')

        # 3. Weathering stages
        weathering_counts = {}
        for r in records:
            w = r.get('weathering_stage', 'unknown')
            weathering_counts[w] = weathering_counts.get(w, 0) + 1

        if weathering_counts:
            axes[1, 0].pie(weathering_counts.values(), labels=weathering_counts.keys(), autopct='%1.1f%%')
            axes[1, 0].set_title('Weathering Stage Distribution')

        # 4. Context comparison
        context_counts = {}
        for r in records:
            ctx = r.get('context_type', 'unknown')
            context_counts[ctx] = context_counts.get(ctx, 0) + 1

        if context_counts:
            axes[1, 1].bar(context_counts.keys(), context_counts.values())
            axes[1, 1].set_title('NISP by Context')
            axes[1, 1].set_xticklabels(context_counts.keys(), rotation=45, ha='right')
            axes[1, 1].set_ylabel('NISP')

        plt.tight_layout()
        plt.show()

    def _export_results(self):
        """Export analysis results"""
        if not self.quant_text.get(1.0, tk.END).strip():
            messagebox.showwarning("Warning", "No results to export")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("PDF", "*.pdf")],
            initialfile=f"zooarch_analysis_{datetime.now().strftime('%Y%m%d')}"
        )

        if path:
            try:
                with open(path, 'w') as f:
                    f.write(self.quant_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Results saved to {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def send_to_table(self):
        """Send data to main table"""
        if not self.records:
            messagebox.showwarning("No Data", "No records to send")
            return

        try:
            self.app.import_data_from_plugin(self.records)
            self.status_var.set(f"✅ Sent {len(self.records)} records to main table")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {e}")


# ============================================================================
# PLUGIN REGISTRATION - SOFTWARE (ADVANCED MENU)
# ============================================================================
def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = ZooarchaeologyAnalyticsSuitePlugin(main_app)

    return plugin
