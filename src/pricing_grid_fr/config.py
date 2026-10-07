from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
print(".env loaded")

# --- CHEMINS DE BASE ---
BASE_DIR = Path(os.getenv("G_DRIVE"))

# --- CONSTANTE TEMPORELLE ---
ANNEE = 2026
VALIDITY_PERIOD = "01/06/2026 - 31/08/2026"

# --- CHEMIN MÉTIERS ---
BASE_DIR_PRICING = BASE_DIR / "pricing-grid-fr"
BASE_DIR_SALES = BASE_DIR / "sales-data-services"


# --- CHEMINS DE TRAVAIL
DIR_BDD = BASE_DIR_SALES / "01 - BDD"
DIR_SAP = BASE_DIR_PRICING / "01 - Extractions SAP"
DIR_SAP_CURRENT = DIR_SAP / f"{ANNEE}"
DIR_STAGGING = BASE_DIR_PRICING / "02 - Stagging"
DIR_STOCKAGE = BASE_DIR_PRICING / "03 - Dépôt des grilles" / "01 - Grilles Monier"

# --- NOMS DES FICHIERS ---
FILES = {
    "clients": f"bdd_client_{ANNEE}.xlsx",
    "produits_sap": f"Hierarchie produit {ANNEE} V2.xlsx",
    "produits_bdd": "bdd_produit.xlsx",
    "zpr0": f"ZPR0_{ANNEE}.xlsx",
    "zd01": f"ZD01_MON_{ANNEE}.xlsx",
    "zd03_art": f"ZD03_DIFF_ART_{ANNEE}.xlsx",
    "zd03_ph6": f"ZD03_DIFF_PH6_{ANNEE}.xlsx",
    "zd03_derog": "ZD03_73_74.xlsx",
    "zeco": "ZECO.xlsx",
}

# --- CONSTANTES METIER ---
MARQUE_CIBLE = "MON"
CODE_DEROG = 4001473

CATEGORIES_TUILES = ["Clay Main Tiles", "Concrete Main Tiles"]
ARTICLES_GENOISES = [
    "10036569",
    "10036570",
    "10036571",
    "10036572",
    "10036574",
    "10036576",
]
ARTICLE_CARTON = "20012666"
