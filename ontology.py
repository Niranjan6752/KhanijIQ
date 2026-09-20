"""Critical-mineral ontology. Edit freely: these keywords drive all tagging.

Pilot covers 6 minerals. To extend to the full Ministry of Mines list of 30,
add entries to MINERALS (first keyword = plain display term).
"""

MINERALS = {
    "Lithium": ["lithium", "li-ion", "lithium-ion", "spodumene", "lepidolite", "lithium carbonate"],
    "Cobalt": ["cobalt", "cobalt oxide", "licoo2"],
    "Nickel": ["nickel", "laterite", "pentlandite"],
    "Rare earth elements": ["rare earth", "rare-earth", "neodymium", "dysprosium", "monazite", "ndfeb"],
    "Graphite": ["graphite", "graphene", "anode material"],
    "Vanadium": ["vanadium", "vanadium pentoxide", "redox flow battery"],
}

# Value-chain stages, in order.
STAGES = {
    "Exploration": ["exploration", "prospecting", "geophysical", "geochemical survey", "remote sensing"],
    "Mining": ["mining", "open-pit", "underground mining", "ore extraction"],
    "Beneficiation": ["beneficiation", "flotation", "magnetic separation", "gravity separation", "comminution"],
    "Extraction & refining": ["leaching", "hydrometallurgy", "solvent extraction", "pyrometallurgy",
                              "electrowinning", "refining", "roasting", "bioleaching"],
    "Recycling": ["recycling", "spent batteries", "recovery from spent", "e-waste", "urban mining", "black mass"],
    "End-use": ["cathode", "anode", "battery", "magnet", "alloy", "catalyst", "electrolyte", "supercapacitor"],
}

# PLACEHOLDER strategic weights (1-3). Replace with import-dependence / NCMM priority data.
PRIORITY = {"Lithium": 3, "Cobalt": 3, "Nickel": 2, "Rare earth elements": 3, "Graphite": 2, "Vanadium": 1}

# Simple entity resolution for organisation names (substring match, lowercase).
ORG_ALIASES = {
    "national metallurgical laboratory": "CSIR-NML",
    "csir-nml": "CSIR-NML",
    "institute of minerals and materials": "CSIR-IMMT",
    "csir-immt": "CSIR-IMMT",
    "indian institute of technology bombay": "IIT Bombay",
    "iit bombay": "IIT Bombay",
    "indian institute of technology kharagpur": "IIT Kharagpur",
    "iit kharagpur": "IIT Kharagpur",
    "indian institute of science": "IISc Bangalore",
    "iisc": "IISc Bangalore",
    "non-ferrous materials technology": "NFTDC",
    "nftdc": "NFTDC",
    "bhabha atomic": "BARC",
    "indian rare earths": "IREL",
}


def canon_org(name) -> str:
    n = str(name).lower()
    for key, val in ORG_ALIASES.items():
        if key in n:
            return val
    return str(name).strip() or "Unknown"
