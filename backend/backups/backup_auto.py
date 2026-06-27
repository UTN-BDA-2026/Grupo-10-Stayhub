"""
backup_auto.py — Backup automático con rotación de 7 días
==========================================================
Genera un backup de la DB y elimina automáticamente los backups
que superen los 7 días de antigüedad.

USO MANUAL:
    uv run --directory backend python backups/backup_auto.py

PROGRAMAR CON CRON (diariamente a las 2 AM):
    crontab -e
    → agregar:
    0 2 * * * cd /ruta/al/proyecto && uv run --directory backend python backups/backup_auto.py >> /var/log/stayhub_backup.log 2>&1

PROGRAMAR CON CRON DENTRO DEL CONTENEDOR:
    docker compose exec backend python backups/backup_auto.py

POLÍTICA DE RETENCIÓN:
    - Se conservan backups de los últimos 7 días.
    - Los archivos .dump con más de 7 días se eliminan automáticamente.
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# ─── Configuración ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

BACKUP_DIR = ROOT / "backend" / "backups"
RETENTION_DAYS = 7          # Días que se conserva cada backup
BACKUP_EXTENSION = ".dump"

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ─── 1. Generar nuevo backup ───────────────────────────────────────────────────
def crear_backup() -> Path:
    """Ejecuta pg_dump y devuelve la ruta del archivo generado."""
    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        log("❌ Faltan variables de entorno: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = BACKUP_DIR / f"backup_{timestamp}{BACKUP_EXTENSION}"

    log(f"Iniciando backup → {output_file.name}")

    command = [
        "docker", "compose", "exec", "-T", "db",
        "pg_dump", "-U", POSTGRES_USER, "-F", "c", POSTGRES_DB,
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = POSTGRES_PASSWORD

    try:
        with open(output_file, "wb") as out:
            subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                stdout=out,
                stderr=subprocess.PIPE,
                timeout=300,
                check=True,
            )
    except subprocess.TimeoutExpired:
        output_file.unlink(missing_ok=True)
        log("❌ Timeout durante pg_dump (> 300s)")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        output_file.unlink(missing_ok=True)
        log(f"❌ Error en pg_dump: {e.stderr.decode() if e.stderr else 'desconocido'}")
        sys.exit(1)

    size_mb = output_file.stat().st_size / 1024 / 1024
    log(f"✅ Backup creado: {output_file.name} ({size_mb:.2f} MB)")
    return output_file


# ─── 2. Rotación — eliminar backups antiguos ───────────────────────────────────
def purgar_backups_antiguos() -> list[Path]:
    """Elimina archivos .dump con más de RETENTION_DAYS días. Devuelve lista de eliminados."""
    limite = datetime.now() - timedelta(days=RETENTION_DAYS)
    eliminados = []

    for archivo in sorted(BACKUP_DIR.glob(f"*{BACKUP_EXTENSION}")):
        # Usar mtime (fecha de modificación del archivo)
        mtime = datetime.fromtimestamp(archivo.stat().st_mtime)
        if mtime < limite:
            size_mb = archivo.stat().st_size / 1024 / 1024
            archivo.unlink()
            eliminados.append(archivo)
            log(f"🗑️  Eliminado (>{RETENTION_DAYS}d): {archivo.name} ({size_mb:.2f} MB)")

    return eliminados


# ─── 3. Resumen ───────────────────────────────────────────────────────────────
def mostrar_resumen(nuevo_backup: Path, eliminados: list[Path]):
    backups_actuales = sorted(BACKUP_DIR.glob(f"*{BACKUP_EXTENSION}"))
    espacio_total_mb = sum(f.stat().st_size for f in backups_actuales) / 1024 / 1024

    print("\n" + "=" * 55)
    print("  RESUMEN DE BACKUP AUTOMÁTICO — StayHub")
    print("=" * 55)
    print(f"  Nuevo backup : {nuevo_backup.name}")
    print(f"  Eliminados   : {len(eliminados)} archivo(s)")
    print(f"  Conservados  : {len(backups_actuales)} backup(s) (últimos {RETENTION_DAYS} días)")
    print(f"  Espacio total: {espacio_total_mb:.2f} MB")
    if backups_actuales:
        print(f"\n  Backups disponibles:")
        for b in backups_actuales:
            mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            size_mb = b.stat().st_size / 1024 / 1024
            marker = " ← nuevo" if b == nuevo_backup else ""
            print(f"    {b.name}  [{mtime}]  {size_mb:.2f} MB{marker}")
    print("=" * 55)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log("=== Backup automático StayHub iniciado ===")

    nuevo = crear_backup()
    eliminados = purgar_backups_antiguos()
    mostrar_resumen(nuevo, eliminados)

    log("=== Proceso finalizado ===")
