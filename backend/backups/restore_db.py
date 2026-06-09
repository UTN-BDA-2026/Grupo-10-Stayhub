import argparse
import os
import shutil
import subprocess
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


def latest_backup_file() -> Path:
    dumps = sorted(BACKUP_DIR.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        raise FileNotFoundError(f"No se encontraron archivos de backup en {BACKUP_DIR}")
    return dumps[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restaurar una base de datos PostgreSQL desde un backup generado con pg_dump.")
    parser.add_argument(
        "backup_file",
        nargs="?",
        help="Ruta al archivo de backup .dump. Si no se indica, se usa el backup más reciente en backend/backups.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.backup_file:
        backup_path = Path(args.backup_file)
        if not backup_path.is_absolute():
            backup_path = ROOT / args.backup_file
    else:
        backup_path = latest_backup_file()

    if not backup_path.exists():
        raise SystemExit(f"Archivo de backup no encontrado: {backup_path}")

    docker_cmd = shutil.which("docker")
    if docker_cmd is None:
        raise SystemExit("No se encontró el ejecutable docker en el PATH")

    # Obtener el id del contenedor asociado al servicio 'db'
    try:
        container_id = subprocess.check_output(["docker", "compose", "ps", "-q", "db"], cwd=ROOT).decode().strip()
    except subprocess.CalledProcessError as e:
        raise SystemExit("Error al obtener el contenedor del servicio 'db'") from e

    if not container_id:
        raise SystemExit("El servicio 'db' no está corriendo (no se encontró contenedor)")

    # Copiar el archivo de backup al contenedor (ruta temporal)
    dest_path = f"/tmp/{backup_path.name}"
    print(f"Copiando {backup_path} al contenedor {container_id}:{dest_path}...")
    subprocess.run(["docker", "cp", str(backup_path), f"{container_id}:{dest_path}"], cwd=ROOT, check=True)

    # Ejecutar pg_restore dentro del contenedor usando docker exec
    command = [
        "docker",
        "exec",
        "-i",
        container_id,
        "pg_restore",
        "-U",
        POSTGRES_USER,
        "-d",
        POSTGRES_DB,
        "--clean",
        "--if-exists",
        dest_path,
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = POSTGRES_PASSWORD

    print(f"Restaurando la base de datos '{POSTGRES_DB}' desde {dest_path} en el contenedor...")
    subprocess.run(command, cwd=ROOT, env=env, check=True)

    # Eliminar el archivo temporal dentro del contenedor
    subprocess.run(["docker", "exec", container_id, "rm", "-f", dest_path], cwd=ROOT, check=True)

    print("Restauración completada.")


if __name__ == "__main__":
    main()
