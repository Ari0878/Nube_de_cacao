# Crea un archivo llamado cleanup_tokens.py en la raíz

import schedule
import time
from services.auth_service import eliminar_tokens_expirados

def job():
    print("Limpiando tokens expirados...")
    eliminar_tokens_expirados()
    print("Tokens limpiados")

# Ejecutar cada hora
schedule.every(1).hour.do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)# Crea un archivo llamado cleanup_tokens.py en la raíz

import schedule
import time
from services.auth_service import eliminar_tokens_expirados

def job():
    print("Limpiando tokens expirados...")
    eliminar_tokens_expirados()
    print("Tokens limpiados")

# Ejecutar cada hora
schedule.every(1).hour.do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)