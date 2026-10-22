import redis
import json


class ProgressNotifier:
    def __init__(self, host="localhost", port=6379, channel="worker_progress"):
        # On se connecte au Redis local (puisqu'on a abandonné Docker pour Python)
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.channel = channel

    def send_log(self, step, message, progress_percent=None):
        """Envoie un message de progression à l'interface web."""
        data = {
            "step": step,
            "message": message,
            "progress": progress_percent,
        }
        # Publication du message au format JSON sur le channel Redis
        self.r.publish(self.channel, json.dumps(data))

    def listen_logs(self):
        """Écoute le channel Redis et génère les messages au format SSE pour Flask."""
        pubsub = self.r.pubsub()
        pubsub.subscribe(self.channel)

        # pubsub.listen() crée une boucle infinie qui attend les nouveaux messages
        for message in pubsub.listen():
            # On ignore les messages de confirmation d'abonnement (type 'subscribe')
            if message["type"] == "message":
                # Le format "data: {json}\n\n" est obligatoire pour le standard SSE
                yield f"data: {message['data']}\n\n"
