"""
test_endpoints.py — Suite de pruebas de endpoints StayHub
===========================================================
Prueba los happy paths y casos de error de todos los recursos principales.
Usa solo stdlib (urllib + json) para no requerir dependencias extra.

USO (desde la raíz del proyecto):
    # Opción A: desde la terminal del host (backend corriendo en Docker)
    uv run --directory backend python scripts/test_endpoints.py

    # Opción B: desde dentro del contenedor
    docker compose run --rm backend uv run python scripts/test_endpoints.py

REQUISITOS:
    - docker compose up -d (backend corriendo en localhost:8000)
    - Al menos 1 propiedad existente en la DB (o dejar que el script cree todo)

RESULTADO ESPERADO:
    Cada test muestra ✅ si pasó o ❌ si falló, con el detalle del error.
"""

import json
import time
import urllib.error
import urllib.request
from datetime import date, timedelta

# ─── Configuración ─────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"

# Timestamp único para evitar conflictos de email en re-ejecuciones
TS = int(time.time())

# ─── Utilidades ────────────────────────────────────────────────────────────────
passed = 0
failed = 0


def post(path: str, payload: dict) -> tuple[int, dict]:
    """Envía un POST y devuelve (status_code, body)."""
    import urllib.parse
    encoded_path = urllib.parse.quote(path, safe="/?=&")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{encoded_path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {"detail": str(e)}
        return e.code, body


def check(nombre: str, status: int, body: dict, expected_status: int, expected_fragment: str = ""):
    """Verifica un resultado y muestra el estado del test."""
    global passed, failed
    ok = status == expected_status
    if expected_fragment:
        ok = ok and expected_fragment.lower() in json.dumps(body).lower()

    if ok:
        passed += 1
        print(f"  ✅ {nombre}")
    else:
        failed += 1
        print(f"  ❌ {nombre}")
        print(f"     Esperado: {expected_status}  |  Obtenido: {status}")
        if expected_fragment:
            print(f"     Fragmento buscado: '{expected_fragment}'")
        print(f"     Body: {json.dumps(body, ensure_ascii=False)[:200]}")


def separador(titulo: str):
    print(f"\n{'─' * 55}")
    print(f"  {titulo}")
    print(f"{'─' * 55}")


# ─────────────────────────────────────────────────────────────────────────────
print("=" * 55)
print("  TEST SUITE — StayHub API")
print(f"  Base URL: {BASE_URL}")
print("=" * 55)

# ─── 1. USUARIOS ──────────────────────────────────────────────────────────────
separador("1. USUARIOS")

# 1.1 Crear huésped
s, body = post("/usuarios/", {
    "nombre": f"Huesped Test {TS}",
    "email": f"huesped.{TS}@test.com",
    "password": "TestPass123!",
    "rol": "huesped",
})
check("Crear huésped válido → 201", s, body, 201)
HUESPED_ID = body.get("id")

# 1.2 Crear propietario
s, body = post("/usuarios/", {
    "nombre": f"Propietario Test {TS}",
    "email": f"propietario.{TS}@test.com",
    "password": "TestPass123!",
    "rol": "propietario",
})
check("Crear propietario válido → 201", s, body, 201)
PROPIETARIO_ID = body.get("id")

# 1.3 Email duplicado → 400
s, body = post("/usuarios/", {
    "nombre": "Duplicado",
    "email": f"huesped.{TS}@test.com",
    "password": "TestPass123!",
    "rol": "huesped",
})
check("Email duplicado → 400", s, body, 400, "email")

# ─── 2. PROPIEDADES ───────────────────────────────────────────────────────────
separador("2. PROPIEDADES")

# 2.1 Crear propiedad válida
# NOTA: El CHECK constraint en DB permite: 'departamento','casa','cabaña','habitacion'
# El schema normaliza 'cabaña'→'cabana' (sin ñ) lo cual NO pasa el CHECK — bug conocido.
# Usamos "casa" que siempre es seguro.
s, body = post("/propiedades/", {
    "propietario_id": PROPIETARIO_ID,
    "nombre": f"Casa Test {TS}",
    "descripcion": "Propiedad de prueba automatizada",
    "tipo": "casa",
    "ciudad": "Mendoza",
    "direccion": "Calle Falsa 123",
    "precio": 75000.00,
    "amenidades": {"wifi": True, "pileta": False},
    "tags": ["test", "automatizado"],
})
check("Crear propiedad válida → 201", s, body, 201)
PROPIEDAD_ID = body.get("id")

# 2.2 Propietario inexistente → 400 (IntegrityError)
s, body = post("/propiedades/", {
    "propietario_id": 99999,
    "nombre": "Propiedad Fantasma",
    "tipo": "departamento",
    "ciudad": "Buenos Aires",
    "direccion": "Sin dirección",
    "precio": 10000.00,
})
check("Propietario inexistente → 400", s, body, 400)

# ─── 3. RESERVAS ──────────────────────────────────────────────────────────────
separador("3. RESERVAS")

HOY = date.today()
CHECKIN = (HOY + timedelta(days=30)).isoformat()
CHECKOUT = (HOY + timedelta(days=35)).isoformat()

# 3.1 Reserva con propiedad inexistente → 400
s, body = post("/reservas/", {
    "propiedad_id": 99999,
    "huesped_id": HUESPED_ID,
    "fecha_checkin": CHECKIN,
    "fecha_checkout": CHECKOUT,
    "precio_total": 100000.00,
})
check("Propiedad inexistente → 400", s, body, 400, "no encontrada")

# 3.2 Reserva válida → 201
s, body = post("/reservas/", {
    "propiedad_id": PROPIEDAD_ID,
    "huesped_id": HUESPED_ID,
    "fecha_checkin": CHECKIN,
    "fecha_checkout": CHECKOUT,
    "precio_total": 375000.00,
})
check("Crear reserva válida → 201", s, body, 201)
RESERVA_ID = body.get("id")

# 3.3 Doble booking (mismas fechas, misma propiedad) → 400
s, body = post("/reservas/", {
    "propiedad_id": PROPIEDAD_ID,
    "huesped_id": HUESPED_ID,
    "fecha_checkin": CHECKIN,
    "fecha_checkout": CHECKOUT,
    "precio_total": 375000.00,
})
check("Doble booking → 400", s, body, 400, "reservada")

# ─── 4. RESEÑAS ───────────────────────────────────────────────────────────────
separador("4. RESEÑAS")

# 4.1 Reseña válida → 200
if RESERVA_ID:
    s, body = post("/reseñas/", {
        "reserva_id": RESERVA_ID,
        "propiedad_id": PROPIEDAD_ID,
        "huesped_id": HUESPED_ID,
        "puntuacion": 5,
        "comentario": "Test automatizado — excelente",
    })
    check("Crear reseña válida → 200", s, body, 200)

    # 4.2 Reseña duplicada (misma reserva) → 400 (unique constraint)
    s, body = post("/reseñas/", {
        "reserva_id": RESERVA_ID,
        "propiedad_id": PROPIEDAD_ID,
        "huesped_id": HUESPED_ID,
        "puntuacion": 3,
        "comentario": "Intento de reseña duplicada",
    })
    check("Reseña duplicada (unique constraint) → 400", s, body, 400)
else:
    print("  ⚠️  Skipped — no se pudo crear reserva")

# ─── RESUMEN ──────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'=' * 55}")
print(f"  RESULTADO: {passed}/{total} tests pasaron")
if failed == 0:
    print("  🎉 Todos los tests pasaron correctamente.")
else:
    print(f"  ⚠️  {failed} test(s) fallaron — revisar output arriba.")
print("=" * 55)
