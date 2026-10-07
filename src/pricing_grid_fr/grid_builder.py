import pandas as pd
import numpy as np
from src.pricing_grid_fr import config
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows


class GridBuilder:

    def __init__(self, data_loader, output_dir: str = config.DIR_STAGGING):
        self.db = data_loader
        self.output_dir = Path(output_dir)
        self.validity_period = config.VALIDITY_PERIOD

    def _get_client_info(self, client_id: int) -> dict:
        """Récupère les métadonnées du client pour l'en-tête du fichier."""
        client_data = self.db.clients[self.db.clients["id_externe"] == client_id]
        if client_data.empty:
            return {"nom": "Inconnu", "dep": "00", "delegue": "Inconnu"}

        row = client_data.iloc[0]
        # On privilégie 'dc' s'il existe, sinon 'dr', sinon 'Inconnu'
        delegue = row.get("dc", row.get("dr", "Inconnu"))

        return {
            "nom": row.get("nom_client", "Inconnu"),
            "dep": str(row.get("code_dep", "00")),
            "delegue": delegue,
        }

    def _write_headers(self, ws, client_id: int, info: dict):
        """Écrit le bloc d'informations client en haut de la feuille."""
        ws["A2"], ws["B2"] = "N° client :", client_id
        ws["A3"], ws["B3"] = "Nom client :", info["nom"]
        ws["A4"], ws["B4"] = "Délégué :", info["delegue"]
        ws["A5"], ws["B5"] = "Date de validité :", self.validity_period

    def _build_summary(self, df: pd.DataFrame, dictionary) -> pd.DataFrame:
        """Génère la synthèse des remises moyennes par catégories."""

        if "Remise totale" not in df.columns or "Hiérarchie 1" not in df.columns:
            return pd.DataFrame()

        rows = []

        # --- 1. Terre Cuite et Béton ---
        for key, h2_dict in dictionary.items():
            # Masque et calcul Niveau 1
            mask_h1 = df["Hiérarchie 1"] == key
            # mean_h1 = matrice.loc[mask_h1, "Remise totale"].mean()
            rows.append({"Catégorie": key, "Remise Moyenne": np.nan})

            # Niveau 2 & 3
            for jkey, h3_list in h2_dict.items():
                is_tuile = jkey.startswith("Tuiles")

                # Masque et calcul Niveau 2
                if is_tuile:
                    mask_h2 = df["Hiérarchie 2"] == jkey
                else:
                    # On réutilise mask_h1 pour la performance
                    mask_h2 = mask_h1 & (
                        df["Hiérarchie 2"].str.slice(0, 11) == "Accessoires"
                    )

                # mean_h2 = matrice.loc[mask_h2, "Remise totale"].mean()
                rows.append({"Catégorie": jkey, "Remise Moyenne": np.nan})

                # Masque et calcul Niveau 3
                for kkey in sorted(h3_list):
                    # On réutilise mask_h2 pour la performance
                    mask_h3 = mask_h2 & (df["Hiérarchie 3"] == kkey)
                    mean_h3 = df.loc[mask_h3, "Remise totale"].mean()
                    rows.append({"Catégorie": kkey, "Remise Moyenne": mean_h3})

        # --- 2. Composants et Isolation (Global) ---
        mask_not_in_dict = ~df["Hiérarchie 1"].isin(dictionary.keys())
        rows.append(
            {
                "Catégorie": "Composants et Isolations",
                "Remise Moyenne": df.loc[mask_not_in_dict, "Remise totale"].mean(),
            }
        )

        # --- 3. Composants ---
        mask_composants = (df["Hiérarchie 1"] == "Composants toits en pente") & (
            df["Hiérarchie 2"] != "Isolation"
        )
        rows.append(
            {
                "Catégorie": "Composants",
                "Remise Moyenne": df.loc[mask_composants, "Remise totale"].mean(),
            }
        )

        # Composants enfants (Utilisation de groupby pour la performance)
        composants_df = df.loc[mask_composants]
        if not composants_df.empty:
            comp_means = composants_df.groupby("Hiérarchie 3")["Remise totale"].mean()
            for cat, mean_val in sorted(comp_means.items()):
                rows.append({"Catégorie": cat, "Remise Moyenne": mean_val})

        # --- 4. Isolation ---
        mask_isolation = df["Hiérarchie 2"] == "Isolation"
        rows.append(
            {
                "Catégorie": "Isolation",
                "Remise Moyenne": df.loc[mask_isolation, "Remise totale"].mean(),
            }
        )

        # Isolation enfants (Utilisation de groupby pour la performance)
        isolation_df = df.loc[mask_isolation]
        if not isolation_df.empty:
            iso_means = isolation_df.groupby("Hiérarchie 3")["Remise totale"].mean()
            for cat, mean_val in sorted(iso_means.items()):
                rows.append({"Catégorie": cat, "Remise Moyenne": mean_val})

        return pd.DataFrame(rows)

    def create_excel(
        self,
        df: pd.DataFrame,
        client_id: int,
        product_dictionary: dict = {},
        is_derog: bool = False,
    ) -> str:
        """Crée le fichier Excel brut avec les données et les onglets."""
        info = self._get_client_info(client_id)

        # Définition du nom de fichier
        suffix = "_dérog" if is_derog else ""
        filename = f"{client_id}_{info['nom']}_{info['dep']}{suffix}_dev.xlsx"
        filepath = self.output_dir / filename

        wb = Workbook()

        # Onglet 1 : Grille tarifaire
        ws_grid = wb.active
        ws_grid.title = "Grille tarifaire"
        self._write_headers(ws_grid, client_id, info)

        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 7):
            for c_idx, value in enumerate(row, 1):
                ws_grid.cell(row=r_idx, column=c_idx, value=value)

        # Onglet 2 : Synthèse (uniquement si non dérogatoire)
        if not is_derog:
            df_summary = self._build_summary(df, product_dictionary)
            if not df_summary.empty:
                ws_summary = wb.create_sheet("Synthèse")
                self._write_headers(ws_summary, client_id, info)

                for r_idx, row in enumerate(
                    dataframe_to_rows(df_summary, index=False, header=True), 7
                ):
                    for c_idx, value in enumerate(row, 1):
                        ws_summary.cell(row=r_idx, column=c_idx, value=value)

        wb.save(filepath)
        return str(filepath)
