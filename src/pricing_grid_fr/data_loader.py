import pandas as pd
import numpy as np
from src.pricing_grid_fr import config


class DataLoader:
    def __init__(self):
        """Initialise le DataLoader en utilisant les paramètres de config.py"""
        # self.load_all()

    def load_all(self):
        print("Chargement des bases de données...")
        self.clients = self._load_clients()
        self.produits = self._load_produits()
        self.dic_produits = self._build_product_dic(self.produits)

        print("Chargement des exports SAP...")
        self.zpr0 = self._load_zpr0()
        self.zd01 = self._load_zd01()
        self.zd03_art = self._load_zd03_art()
        self.zd03_ph6 = self._load_zd03_ph6()
        self.zd03_derog = self._load_zd03_derog()

        self.zeco = self._load_zeco()
        print("Chargement terminé.")

    @staticmethod
    def _clean_rate(series: pd.Series, divide_by_100: bool = True) -> pd.Series:
        s = series.astype(str)
        s = s.str.replace("-", "").str.replace(" ", "").str.replace(",", ".")
        s = s.replace("0.000", np.nan)
        s = pd.to_numeric(s, errors="coerce")
        if divide_by_100:
            s = s / 100
        return s

    def _load_clients(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_BDD / config.FILES["clients"])
        df = df[df["marque"] == config.MARQUE_CIBLE].reset_index(drop=True)

        cols = [
            "id_externe",
            "marque",
            "id_externe_marque",
            "nom_client",
            "code_dep",
            "dc",
            "dr",
            "cust_sales_level_1",
            "cust_sales_level_2",
            "cust_sales_level_3",
        ]
        df = df.loc[:, [c for c in cols if c in df.columns]]

        df["nom_client"] = df["nom_client"].str.replace("/", "-")
        df["id_externe"] = df["id_externe"].astype(int)
        return df

    def _generate_customer_catalogue(self) -> dict:
        catalogue = self._load_clients()
        return catalogue.to_json(orient="records")

    def _load_produits(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["produits_sap"])
        df["Article"] = df["Article"].astype(str)
        df["Code EAN"] = df["Code EAN"].astype(str)

        ph_code = [
            "Code PH1 EN",
            "Code PH2 EN",
            "Code PH3 EN",
            "Code PH4",
            "Code PH5",
            "Code PH6",
        ]
        for col in ph_code:
            df[col] = df[col].fillna(0)

        df["Code PH3 EN"] = df["Code PH3 EN"].astype(int).astype(str)
        for col in ph_code:
            df[col] = df[col].astype(str)

        df["PH6_CODE"] = (
            df["Code PH1 EN"]
            + df["Code PH2 EN"]
            + df["Code PH3 EN"]
            + df["Code PH4"]
            + df["Code PH5"]
            + df["Code PH6"]
        )

        autre_bdd = pd.read_excel(config.DIR_BDD / config.FILES["produits_bdd"])
        autre_bdd = autre_bdd[["s4_code", "ph_level_5"]].rename(
            columns={"s4_code": "Article"}
        )
        autre_bdd["Article"] = autre_bdd["Article"].astype(str)

        return pd.merge(df, autre_bdd, how="left", on="Article")

    def _build_product_dic(self, df_product) -> dict:
        profils_beton = df_product[
            (df_product["Hiérarchie 1"] == "Béton")
            & (df_product["Hiérarchie 2"] == "Tuiles Béton")
        ]["Hiérarchie 3"].unique()

        acc_profils_beton = df_product[
            (df_product["Hiérarchie 1"] == "Béton")
            & (df_product["Hiérarchie 2"] != "Tuiles Béton")
        ]["Hiérarchie 3"].unique()

        profils_tc = df_product[
            (df_product["Hiérarchie 1"] == "Terre Cuite")
            & (df_product["Hiérarchie 2"] == "Tuiles Terre Cuite")
        ]["Hiérarchie 3"].unique()

        acc_profils_tc = df_product[
            (df_product["Hiérarchie 1"] == "Terre Cuite")
            & (df_product["Hiérarchie 2"] != "Tuiles Terre Cuite")
        ]["Hiérarchie 3"].unique()

        composants = df_product[
            (df_product["Hiérarchie 1"] == "Composants toits en pente")
            & (df_product["Hiérarchie 2"] != "Isolation")
        ]["Hiérarchie 3"].unique()

        isolation = df_product[(df_product["Hiérarchie 2"] == "Isolation")][
            "Hiérarchie 3"
        ].unique()

        return {
            "Béton": {
                "Tuiles Béton": list(profils_beton),
                "Accessoires Béton": list(acc_profils_beton),
            },
            "Terre Cuite": {
                "Tuiles Terre Cuite": list(profils_tc),
                "Accessoires Terre Cuite": list(acc_profils_tc),
            },
            "Composants et Isolations": {
                "Composants": list(composants),
                "Isolation": list(isolation),
            },
        }

    def _load_zpr0(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zpr0"])
        df = df[["Article", "Rate", "Unit of Measure"]]
        df["Article"] = df["Article"].astype(str)
        return df

    def _load_zd01(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zd01"])
        df = df[df["Grpe marchandises 4"] == config.MARQUE_CIBLE].reset_index(drop=True)
        df = df[["Client", "Rate"]].rename(columns={"Client": "id_externe"})

        df["ZD01"] = self._clean_rate(df["Rate"], divide_by_100=True)
        return df[["id_externe", "ZD01"]]

    def _load_zd03_art(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zd03_art"])
        df = df[["Client", "Article", "Rate"]].rename(columns={"Client": "id_externe"})
        df["Article"] = df["Article"].astype(str)

        df["ZD03_ARTICLE"] = self._clean_rate(df["Rate"], divide_by_100=True)
        return df[["id_externe", "Article", "ZD03_ARTICLE"]]

    def _load_zd03_ph6(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zd03_ph6"])
        df = df.rename(columns={"Client": "id_externe"})

        ph_cols = [
            "Cat - Roofing, Construction, Services",
            "Appli - Pitched, Flat, Civil Eng, Design",
            "Brand",
            "Material (Clay, Cement, Rubber, etc.)",
            "Prod Cat - Tile/Fitting/Cap Sheet etc",
            "Product (without finish or color)",
        ]

        for col in ph_cols:
            df[col] = df[col].astype(str)

        df["PH6_CODE"] = df[ph_cols].agg("".join, axis=1)
        df["ZD03_PH6"] = self._clean_rate(df["Rate"], divide_by_100=True)

        return df[["id_externe", "PH6_CODE", "ZD03_PH6"]]

    def _load_zd03_derog(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zd03_derog"])
        df = df[["Client", "PartenaireTarif", "Article", "Rate"]].rename(
            columns={"Client": "id_externe"}
        )
        df["Article"] = df["Article"].astype(str)

        df["Rate"] = self._clean_rate(df["Rate"], divide_by_100=True)

        df_pivot = df.pivot(
            index=["id_externe", "Article"], columns="PartenaireTarif", values="Rate"
        ).reset_index()
        df_pivot.columns.name = None

        if config.CODE_DEROG in df_pivot.columns:
            df_pivot = df_pivot.rename(columns={config.CODE_DEROG: "Dérog"})
        else:
            df_pivot["Dérog"] = np.nan

        return df_pivot[["id_externe", "Article", "Dérog"]]

    def _load_zeco(self) -> pd.DataFrame:
        df = pd.read_excel(config.DIR_SAP_CURRENT / config.FILES["zeco"])
        df = df[["Article", "Rate", "Per", "Unit of Measure"]]
        df["Article"] = df["Article"].astype(str)

        df["Rate_float"] = df["Rate"].astype(str).str.replace(",", ".").astype(float)
        df["ZECO"] = df["Rate_float"] / df["Per"]

        # ------ TEST DATA VALIDATION ------
        test = pd.merge(df, self.produits[["Article"]], how="inner", on="Article")
        test = pd.merge(
            test,
            self.zpr0[["Article", "Unit of Measure"]],
            how="inner",
            on="Article",
            suffixes=("_zeco", "_zpr0"),
        )

        mask = test["Unit of Measure_zeco"] != test["Unit of Measure_zpr0"]
        test_false = test[mask]

        for _, row in test_false.iterrows():
            df.loc[df["Article"] == row["Article"], "Unit of Measure"] = row[
                "Unit of Measure_zpr0"
            ]

        # ------ TEST DATA VALIDATION ------

        return df[["Article", "ZECO", "Unit of Measure"]]
