import argparse
import os
import shutil
import subprocess
import sys
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


def latest_backup_file() -> Path:
    if not BACKUP_DIR.exists():
        raise SystemExit(f"❌ Directorio de backups no existe: {BACKUP_DIR}")
    
    dumps = sorted(BACKUP_DIR.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not dumps:
        raise SystemExit(f"❌ No se encontraron archivos de backup en {BACKUP_DIR}")
    return dumps[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restaurar una base de datos PostgreSQL desde un backup generado con pg_dump.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python restore_db.py                           # Usa el backup más reciente
  python restore_db.py backend/backups/backup_20240621_120000.dump  # Usa un backup específico
        """
    )
    parser.add_argument(
        "backup_file",
        nargs="?",
        help="Ruta al archivo de backup .dump. Si no se indica, se usa el backup más reciente.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Determinar el archivo de backup
    if args.backup_file:
        backup_path = Path(args.backup_file)
        if not backup_path.is_absolute():
            backup_path = ROOT / args.backup_file
    else:
        backup_path = latest_backup_file()
    
    # Validar que el archivo existe
    if not backup_path.exists():
        raise SystemExit(f"❌ Archivo de backup no encontrado: {backup_path}")
    
    # Validar que el archivo tiene contenido
    file_size = backup_path.stat().st_size
    if file_size == 0:
        raise SystemExit(f"❌ El archivo de backup está vacío: {backup_path}")
    
    print(f"📁 Archivo de backup: {backup_path}")
    print(f"   Tamaño: {file_size / 1024 / 1024:.2f} MB")
    
    # Verificar que docker está disponible
    if shutil.which("docker") is None:
        raise SystemExit("❌ No se encontró el ejecutable docker en el PATH")
    
    # Obtener el id del contenedor asociado al servicio 'db'
    print("Verificando servicio 'db'...")
    try:
        container_id = subprocess.check_output(
            ["docker", "compose", "ps", "-q", "db"],
            cwd=ROOT,
            stderr=subprocess.PIPE,
            timeout=5
        ).decode().strip()
    except subprocess.TimeoutExpired:
        raise SystemExit("❌ Timeout al verificar el servicio 'db'")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Error desconocido"
        raise SystemExit(f"❌ Error al obtener el contenedor del servicio 'db': {error_msg}") from e
    
    if not container_id:
        raise SystemExit("❌ El servicio 'db' no está corriendo. Inicia los contenedores con: docker compose up -d")
    
    print(f"✅ Contenedor encontrado: {container_id[:12]}")
    
    # Copiar el archivo de backup al contenedor (ruta temporal)
    dest_path = f"/tmp/{backup_path.name}"
    print(f"📤 Copiando backup al contenedor...")
    try:
        subprocess.run(
            ["docker", "cp", str(backup_path), f"{container_id}:{dest_path}"],
            cwd=ROOT,
            timeout=60,
            check=True,
            capture_output=True
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(f"❌ Timeout copiando el archivo de backup")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Error desconocido"
        raise SystemExit(f"❌ Error copiando archivo: {error_msg}")
    
    # Ejecutar pg_restore dentro del contenedor
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
    
    print(f"🔄 Restaurando base de datos '{POSTGRES_DB}'...")
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            timeout=300,  # 5 minutos timeout
            check=False,  # No lanzar excepción, revisar manualmente
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # pg_restore puede tener warnings que no son errores fatales
            if "error" in result.stderr.lower() or "fatal" in result.stderr.lower():
                # Limpiar el archivo temporal
                subprocess.run(["docker", "exec", container_id, "rm", "-f", dest_path], cwd=ROOT, timeout=5)
                raise SystemExit(f"❌ Error durante pg_restore:\n{result.stderr}")
            else:
                # Solo warnings, continuar
                print(f"⚠️  Warnings durante restauración:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "exec", container_id, "rm", "-f", dest_path], cwd=ROOT, timeout=5)
        raise SystemExit(f"❌ Timeout durante la restauración (>300s)")
    except Exception as e:
        subprocess.run(["docker", "exec", container_id, "rm", "-f", dest_path], cwd=ROOT, timeout=5)
        raise SystemExit(f"❌ Error inesperado: {e}")
    
    # Eliminar el archivo temporal dentro del contenedor
    print("🧹 Limpiando archivos temporales...")
    try:
        subprocess.run(
            ["docker", "exec", container_id, "rm", "-f", dest_path],
            cwd=ROOT,
            timeout=5,
            check=True,
            capture_output=True
        )
    except Exception as e:
        print(f"⚠️  No se pudo eliminar el archivo temporal: {e}")
    
    print("✅ Restauración completada correctamente.")


if __name__ == "__main__":
    main()
