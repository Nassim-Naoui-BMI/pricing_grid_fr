from flask import Flask, render_template, Response, jsonify, request
import redis
import threading
from src.pricing_grid_fr.data_loader import DataLoader
from src.pricing_grid_fr.notifier import ProgressNotifier
from src.pricing_grid_fr.orchestrator import GridOrchestrator

app = Flask(__name__)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/customer/catalogue", methods=["GET"])
def get_customer_catalogue():
    catalogue = DataLoader()._generate_customer_catalogue()
    return catalogue, 200


@app.route("/api/progress")
def progress_stream():
    notifier = ProgressNotifier()

    return Response(notifier.listen_logs(), mimetype="text/event-stream")


@app.route("/api/edit-grid", methods=["POST"])  # <-- Slash retiré
def edit_grid():
    data = request.json

    # On extrait les arguments
    marque = data.get("marque")
    type_grille = data.get("type_grille")
    clients_ids = data.get("clients_ids", [])  # <-- "s" ajouté pour matcher le JS

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
        runner = GridOrchestrator()
        if type_grille == "individuelle":
            runner.process_batch(client_ids=clean_ids)

    # Lancement du worker dans un thread séparé
    thread = threading.Thread(target=background_task)
    thread.start()

    # Flask répond immédiatement : le navigateur peut lancer sa connexion SSE !
    return jsonify({"status": "success", "message": "Worker lancé en arrière-plan"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
