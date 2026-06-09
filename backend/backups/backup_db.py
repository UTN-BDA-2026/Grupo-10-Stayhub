import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise SystemExit("Faltan variables de entorno en .env: POSTGRES_USER, POSTGRES_PASSWORD o POSTGRES_DB")

BACKUP_DIR = ROOT / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = BACKUP_DIR / f"backup_{timestamp}.dump"

# Elegir docker compose disponible
DOCKER_COMPOSE_CMD = shutil.which("docker")
if DOCKER_COMPOSE_CMD is None:
    raise SystemExit("No se encontró el ejecutable docker en el PATH")

# Ejecutar pg_dump dentro del servicio db
command = [
    "docker",
    "compose",
    "exec",
    "-T",
    "db",
    "pg_dump",
    "-U",
    POSTGRES_USER,
    "-F",
    "c",
    POSTGRES_DB,
]

env = os.environ.copy()
env["PGPASSWORD"] = POSTGRES_PASSWORD

print("Iniciando backup de la base de datos...")
with open(output_file, "wb") as out:
    subprocess.run(command, cwd=ROOT, env=env, stdout=out, check=True)

print(f"Backup completado: {output_file}")
