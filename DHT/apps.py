
from time import sleep
from django.apps import AppConfig
from threading import Thread
class DhtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DHT'
    escalation_thread = None

    def ready(self):
        from .api import start_escalation_task  # Import différé

        def thread_runner():
            while True:
                if not self.escalation_thread or not self.escalation_thread.is_alive():
                    print("Restarting escalation thread...")
                    self.escalation_thread = Thread(target=start_escalation_task, daemon=True)
                    self.escalation_thread.start()
                sleep(60)  # Vérification toutes les 60 secondes

        # Lancer un superviseur de thread
        Thread(target=thread_runner, daemon=True).start()
