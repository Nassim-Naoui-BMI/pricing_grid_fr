import pandas as pd
import numpy as np
from src.pricing_grid_fr import config


class PricingEngine:
    def __init__(self, data_loader):
        self.db = data_loader
        self.master_products = self._build_master_products()

    def _build_master_products(self) -> pd.DataFrame:
        """Construit le socle commun (Produits + ZPR0 + ZECO) au démarrage."""
        df = self.db.produits.copy()

        # Jointures de base
        df = pd.merge(df, self.db.zpr0, how="left", on="Article")
        df = pd.merge(df, self.db.zeco, how="left", on="Article")

        # Ajustement des unités de facturation (Tuiles et Génoises)
        mask_tuiles = df["ph_level_5"].isin(config.CATEGORIES_TUILES)
        mask_genoise = df["Article"].isin(config.ARTICLES_GENOISES)

        df.loc[mask_tuiles | mask_genoise, "ZECO"] *= 1000
        df["Unité de facturation"] = np.where(mask_tuiles | mask_genoise, 1000, 1)

        # Cas spécifique du produit au carton
        df.loc[df["Article"] == config.ARTICLE_CARTON, "Unité de facturation"] = 100

        return df

    def calculate_grid(self, client_id: int, is_derog: bool = False) -> pd.DataFrame:
        """Génère la grille tarifaire complète pour un client donné."""
        df = self.master_products.copy()
        df["id_externe"] = client_id

        # 1. Remise de base (ZD01)
        df = pd.merge(df, self.db.zd01, how="left", on="id_externe")

        if is_derog:
            # --- LOGIQUE DÉROG ---
            df = pd.merge(
                df, self.db.zd03_derog, how="left", on=["id_externe", "Article"]
            )

            df = df[df["Dérog"].notna()].copy()
            df["ZD01"] = df["ZD01"].fillna(0)

            # Calcul du prix dérog
            df["Prix Dérog - 4001473"] = round(
                df["Rate"] * (1 - df["ZD01"]) * (1 - df["Dérog"]), 2
            )

            # Mise en forme finale Dérog
            df = df.rename(
                columns={"Rate": "Prix tarif public HT", "ZECO": "Eco-contrib"}
            )
            cols_derog = [
                "Article",
                "Legacy code",
                "Code EAN",
                "Libellé Article",
                "Coloris",
                "Hiérarchie 1",
                "Hiérarchie 2",
                "Hiérarchie 3",
                "Conditionnement",
                "Poids unitaire",
                "Unité de facturation",
                "Prix tarif public HT",
                "Prix Dérog - 4001473",
                "Eco-contrib",
            ]

            df = df.loc[:, [c for c in cols_derog if c in df.columns]]

        else:
            # --- LOGIQUE STANDARD (DIFFUS) ---
            df = pd.merge(
                df, self.db.zd03_art, how="left", on=["id_externe", "Article"]
            )
            df = pd.merge(
                df, self.db.zd03_ph6, how="left", on=["id_externe", "PH6_CODE"]
            )

            # La remise Article prime sur la remise Famille (PH6)
            df["ZD03"] = np.where(
                df["ZD03_ARTICLE"].notna(), df["ZD03_ARTICLE"], df["ZD03_PH6"]
            )

            # Remplacement des valeurs manquantes par 0
            df[["ZD01", "ZD03", "ZECO"]] = df[["ZD01", "ZD03", "ZECO"]].fillna(0)

            # Calculs du prix diffus et de la remise totale
            df["Prix diffus"] = round(
                df["Rate"] * (1 - df["ZD01"]) * (1 - df["ZD03"]), 2
            )
            df["Remise totale"] = round(
                (df["Rate"] - df["Prix diffus"]) / df["Rate"], 2
            )

            # Mise en forme finale Standard
            df = df.rename(
                columns={"Rate": "Prix tarif public HT", "ZECO": "Eco-contrib"}
            )
            cols_std = [
                "Article",
                "Legacy code",
                "Code EAN",
                "Libellé Article",
                "Coloris",
                "Hiérarchie 1",
                "Hiérarchie 2",
                "Hiérarchie 3",
                "Conditionnement",
                "Poids unitaire",
                "Unité de facturation",
                "Prix tarif public HT",
                "Remise totale",
                "Prix diffus",
                "Eco-contrib",
            ]

            df = df.loc[:, [c for c in cols_std if c in df.columns]]

        # Exclure les articles sans prix
        df = df[df["Prix tarif public HT"] != 0].copy()

        return df
