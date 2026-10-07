import shutil
from pathlib import Path
from src.pricing_grid_fr import config


class FileDistributor:
    def __init__(
        self,
        data_loader,
        drive_base_path: str = config.DIR_STOCKAGE,
    ):
        self.db = data_loader
        self.drive_base = Path(drive_base_path)
        self.title_dir = f"GM{config.ANNEE}"

    def move_to_drive(self, filepath: str, client_id: int):
        """Déplace le fichier généré vers le bon dossier du Drive."""
        source_path = Path(filepath)
        if not source_path.exists():
            print(f"Erreur : Le fichier {source_path.name} n'existe pas.")
            return

        client_data = self.db.clients[self.db.clients["id_externe"] == client_id]
        if client_data.empty:
            print(f"Erreur : Client {client_id} introuvable pour le routage.")
            return

        row = client_data.iloc[0]
        dr = str(row.get("dr", "Inconnu"))
        dc = str(row.get("dc", "Inconnu"))
        dep = str(row.get("code_dep", "00"))

        # Construction du chemin Drive : G:/Mon Drive/.../Grilles Monier 2026 DR/Grilles Monier 2026 DC/DEP[cite: 1]
        target_dir = (
            self.drive_base
            / f"{self.title_dir} - {dr}"
            / f"{self.title_dir} - {dc}"
            / dep
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        # Déplacement et écrasement si existant

        target_path = target_dir / source_path.name

        shutil.move(source_path, target_path)
        print(f"✅ {source_path.name} déplacé vers {target_dir}")  # [cite: 1]
