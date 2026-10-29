from flask import Flask, render_template, Response, jsonify, request
import pickle
import redis
import threading
from src.pricing_grid_fr.data_loader import DataLoader
from src.pricing_grid_fr.notifier import ProgressNotifier
from src.pricing_grid_fr.orchestrator import GridOrchestrator

app = Flask(__name__)

# ⚠️ CORRECTION 1 : Retrait de decode_responses=True
# On laisse Redis renvoyer des bytes bruts pour que pickle.loads fonctionne.
r = redis.Redis(host="localhost", port=6379, db=0)

# --------------------- DATA LOADER REDIS ---------------------


class RedisCache:
    def __init__(self):
        self.load_all()

    def _cache_set(self, key, data, ttl=86400):
        """Sérialise et stocke dans Redis avec une expiration (ici 24h)"""
        r.setex(key, ttl, pickle.dumps(data))

    def _cache_get(self, key):
        """Récupère et désérialise depuis Redis"""
        data = r.get(key)
        if data:
            return pickle.loads(data)
        return None

    def load_all(self):
        if r.exists("clients"):
            print("⚡ Chargement des données depuis le cache Redis...")
            self.clients = self._cache_get("clients")
            self.produits = self._cache_get("produits")
            self.dic_produits = self._cache_get("dic_produits")

            self.zpr0 = self._cache_get("zpr0")
            self.zd01 = self._cache_get("zd01")
            self.zd03_art = self._cache_get("zd03_art")
            self.zd03_ph6 = self._cache_get("zd03_ph6")
            self.zd03_derog = self._cache_get("zd03_derog")
            self.zeco = self._cache_get("zeco")
            print("✅ Chargement depuis Redis terminé.")

        else:
            print("⏳ Cache vide. Chargement depuis les fichiers sources...")

            loader = DataLoader()

            self.clients = loader._load_clients()
            self.produits = loader._load_produits()
            self.dic_produits = loader._build_product_dic(self.produits)

            self.zpr0 = loader._load_zpr0()
            self.zd01 = loader._load_zd01()
            self.zd03_art = loader._load_zd03_art()
            self.zd03_ph6 = loader._load_zd03_ph6()
            self.zd03_derog = loader._load_zd03_derog()
            self.zeco = loader._load_zeco()

            print("💾 Sauvegarde des données dans Redis pour les prochains appels...")
            self._cache_set("clients", self.clients)
            self._cache_set("produits", self.produits)
            self._cache_set("dic_produits", self.dic_produits)
            self._cache_set("zpr0", self.zpr0)
            self._cache_set("zd01", self.zd01)
            self._cache_set("zd03_art", self.zd03_art)
            self._cache_set("zd03_ph6", self.zd03_ph6)
            self._cache_set("zd03_derog", self.zd03_derog)
            self._cache_set("zeco", self.zeco)

            print("✅ Chargement et mise en cache terminés.")


# Instanciation au lancement du serveur
redis_cache = RedisCache()


# --------------------- ROUTES --------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/customer/catalogue", methods=["GET"])
def get_customer_catalogue():
    loader = DataLoader()
    catalogue = loader._generate_customer_catalogue(
        redis_cache.clients, redis_cache.zd01
    )
    return catalogue, 200


@app.route("/api/progress")
def progress_stream():
    notifier = ProgressNotifier()

    return Response(notifier.listen_logs(), mimetype="text/event-stream")


@app.route("/api/edit-grid", methods=["POST"])
def edit_grid():
    data = request.json

    # On extrait les arguments
    marque = data.get("marque")
    type_grille = data.get("type_grille")
    clients_ids = data.get("clients_ids", [])

    if not clients_ids:
        return jsonify({"status": "error", "message": "Aucun client sélectionné"}), 400

    # Sécurisation de la conversion en int (au cas où un ID serait mal formaté)
    try:
        clean_ids = [int(client_id) for client_id in clients_ids]
    except ValueError:
        return (
            jsonify({"status": "error", "message": "Format d'ID client invalide"}),
            400,
        )

    # Fonction encapsulée qui sera exécutée en arrière-plan
    def background_task():
        runner = GridOrchestrator(redis_cache=redis_cache)
        if type_grille == "individuelle":
            runner.process_batch(client_ids=clean_ids)

    # Lancement du worker dans un thread séparé
    thread = threading.Thread(target=background_task)
    thread.start()

    # Flask répond immédiatement : le navigateur peut lancer sa connexion SSE !
    return jsonify({"status": "success", "message": "Worker lancé en arrière-plan"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
