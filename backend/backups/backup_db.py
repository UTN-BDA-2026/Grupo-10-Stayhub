import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ROOT debe ser la raíz del repositorio (donde está docker-compose.yml)
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise SystemExit("Faltan variables de entorno en .env: POSTGRES_USER, POSTGRES_PASSWORD o POSTGRES_DB")

# Directorio de backup
BACKUP_DIR = ROOT / "backend" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = BACKUP_DIR / f"backup_{timestamp}.dump"

# Verificar que docker esté disponible
if shutil.which("docker") is None:
    raise SystemExit("❌ No se encontró el ejecutable docker en el PATH")

# Verificar que el servicio db está corriendo
print("Verificando que el servicio 'db' esté en ejecución...")
try:
    container_check = subprocess.run(
        ["docker", "compose", "ps", "-q", "db"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=5
    )
    if not container_check.stdout.strip():
        raise SystemExit("❌ El servicio 'db' no está corriendo. Inicia los contenedores con: docker compose up -d")
except subprocess.TimeoutExpired:
    raise SystemExit("❌ Timeout al verificar el servicio 'db'")
except subprocess.CalledProcessError as e:
    raise SystemExit(f"❌ Error al verificar docker-compose: {e.stderr}")

# Ejecutar pg_dump dentro del servicio db
print("Iniciando backup de la base de datos...")
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

try:
    with open(output_file, "wb") as out:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=out,
            stderr=subprocess.PIPE,
            timeout=300,  # 5 minutos timeout
            check=True
        )
except subprocess.TimeoutExpired:
    output_file.unlink(missing_ok=True)
    raise SystemExit(f"❌ Timeout durante el backup. El proceso tardó más de 300 segundos.")
except subprocess.CalledProcessError as e:
    output_file.unlink(missing_ok=True)
    error_msg = e.stderr.decode() if e.stderr else "Error desconocido"
    raise SystemExit(f"❌ Error durante pg_dump:\n{error_msg}")
except Exception as e:
    output_file.unlink(missing_ok=True)
    raise SystemExit(f"❌ Error inesperado: {e}")

# Validar que el archivo se generó correctamente
if not output_file.exists():
    raise SystemExit(f"❌ El archivo de backup no se creó: {output_file}")

file_size = output_file.stat().st_size
if file_size == 0:
    output_file.unlink()
    raise SystemExit("❌ El archivo de backup está vacío. El backup falló.")

print(f"✅ Backup completado correctamente")
print(f"   Archivo: {output_file}")
print(f"   Tamaño: {file_size / 1024 / 1024:.2f} MB")
