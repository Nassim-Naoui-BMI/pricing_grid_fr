import time
from typing import List
from src.pricing_grid_fr.data_loader import DataLoader
from src.pricing_grid_fr.pricing_engine import PricingEngine
from src.pricing_grid_fr.grid_builder import GridBuilder
from src.pricing_grid_fr.formatter import ExcelFormatter
from src.pricing_grid_fr.distributor import FileDistributor
from src.pricing_grid_fr.notifier import ProgressNotifier


class GridOrchestrator:
    def __init__(self):
        print("Initialisation de l'orchestrateur...")
        self.loader = DataLoader()
        self.engine = PricingEngine(self.loader)
        self.builder = GridBuilder(self.loader)
        self.formatter = ExcelFormatter()
        self.distributor = FileDistributor(self.loader)
        self.notifier = ProgressNotifier()

    def process_single_client(self, client_id: int):
        """Traite la grille standard et la grille dérogatoire pour un client[cite: 1]."""

        @staticmethod
        def clean_path(path):

            delete_chain = ".shortcut-targets-by-id\\1Hn5W4bo3IaXRI-17oRWJJAdiQ2Cd0KfE\\BMI France_BI_Sales\\pricing-grid-fr"

            return str(path).replace(delete_chain, "...")

        # 1. Grille Standard (Diffus)
        df_std = self.engine.calculate_grid(client_id, is_derog=False)
        if not df_std.empty:
            path_std = self.builder.create_excel(
                df_std, client_id, self.loader.dic_produits, is_derog=False
            )
            self.formatter.format_client_grid(path_std, is_derog=False)
            target_path = self.distributor.move_to_drive(path_std, client_id)
            self.notifier.send_log(
                step="PROGRESS",
                message=f"Grille éditée dans : ${clean_path(target_path)}",
            )

        # 2. Grille Dérogatoire (Table 73/74)
        df_derog = self.engine.calculate_grid(client_id, is_derog=True)
        if not df_derog.empty:
            path_derog = self.builder.create_excel(df_derog, client_id, is_derog=True)
            self.formatter.format_client_grid(path_derog, is_derog=True)
            target_path = self.distributor.move_to_drive(path_derog, client_id)
            self.notifier.send_log(
                step="PROGRESS",
                message=f"Grille éditée dans : ${clean_path(target_path)}",
            )

    def process_batch(
        self,
        client_ids: List[int],
        max_retries: int = 3,
        delay_between_retries: int = 5,
    ):
        """
        Traite une liste de clients par lots.
        En cas d'échec sur un client, il est placé dans une file d'attente pour être réessayé.
        """
        failed_clients = client_ids.copy()
        attempt = 1
        step = 1
        progress = 0

        while failed_clients and attempt <= max_retries:
            print(
                f"\n--- Lancement du Batch (Essai {attempt}/{max_retries}) - {len(failed_clients)} clients restants ---"
            )

            # File temporaire pour stocker les échecs de la tentative en cours
            current_failures = []

            for client_id in failed_clients:
                try:
                    self.notifier.send_log(
                        step="START",
                        message=f"Édition de la grille : {client_id}",
                    )

                    self.process_single_client(client_id)

                    progress = round(step / len(client_ids) * 100)
                    step += 1

                    print(f"[{client_id}] Traitement réussi.")

                    self.notifier.send_log(
                        step="PROGRESS",
                        message=f"Avancement : {progress} %",
                    )
                except Exception as e:
                    print(f"[{client_id}] Erreur lors du traitement : {e}")
                    current_failures.append(client_id)

            failed_clients = current_failures

            if failed_clients and attempt < max_retries:
                print(
                    f"Attente de {delay_between_retries} secondes avant de relancer les {len(failed_clients)} échecs..."
                )
                time.sleep(delay_between_retries)

            attempt += 1

        # Bilan final
        if failed_clients:
            print(
                f"\nÉchec définitif pour les clients suivants après {max_retries} tentatives : {failed_clients}"
            )
            self.notifier.send_log(
                step="DONE",
                message=f"Traitement terminé avec des échecs sur {len(failed_clients)} client(s). | liste : {failed_clients}",
            )
        else:
            print("\nTous les clients ont été traités avec succès !")
            self.notifier.send_log(
                step="DONE", message="Tous les clients ont été traités avec succès !"
            )
