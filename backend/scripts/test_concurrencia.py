"""
test_concurrencia.py — Prueba de doble booking concurrente
===========================================================
Demuestra que el mecanismo SELECT ... FOR UPDATE previene el doble booking
cuando dos requests llegan simultáneamente para la misma propiedad y fechas.

USO:
    1. Asegurarse de que el backend esté corriendo: docker compose up -d
    2. Tener al menos 1 usuario y 1 propiedad en la DB (correr seed.py primero)
    3. Ejecutar: docker compose run --rm backend uv run python scripts/test_concurrencia.py

QUÉ ESPERAR:
    - Una reserva se crea exitosamente (HTTP 201)
    - La otra es rechazada (HTTP 400 — doble booking detectado)
    - Nunca dos reservas para la misma propiedad y fechas
"""

import threading
import urllib.request
import urllib.error
import json

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL = "http://stayhub_api:8000"

# Ajustar estos valores según los datos que tengas en tu DB
PAYLOAD = {
    "propiedad_id": 4,              # Casa del Valle — Mendoza (sin reservas aún)
    "huesped_id": 3,                # Solange Parada (huesped)
    "fecha_checkin": "2026-08-01",
    "fecha_checkout": "2026-08-05",
    "precio_total": "34000.00",     # 8500 x 4 noches
    "estado": "pendiente"
}

# ─── Función que simula un request de reserva ─────────────────────────────────
resultados = []
lock_resultados = threading.Lock()

def intentar_reserva(numero_request: int):
    """Envía un POST /reservas y registra el resultado."""
    data = json.dumps(PAYLOAD).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/reservas/",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read())
            with lock_resultados:
                resultados.append({
                    "request": numero_request,
                    "status": response.status,
                    "resultado": "✅ RESERVA CREADA",
                    "id": body.get("id"),
                })
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        with lock_resultados:
            resultados.append({
                "request": numero_request,
                "status": e.code,
                "resultado": "❌ RECHAZADA (esperado)",
                "detalle": body.get("detail"),
            })


# ─── Lanzar dos threads simultáneos ──────────────────────────────────────────
print("=" * 60)
print("  TEST DE DOBLE BOOKING CONCURRENTE — StayHub")
print("=" * 60)
print(f"\nEnviando 2 requests simultáneos para:")
print(f"  propiedad_id : {PAYLOAD['propiedad_id']}")
print(f"  fechas       : {PAYLOAD['fecha_checkin']} → {PAYLOAD['fecha_checkout']}")
print(f"  huesped_id   : {PAYLOAD['huesped_id']}")
print("\n⏳ Ejecutando...\n")

t1 = threading.Thread(target=intentar_reserva, args=(1,))
t2 = threading.Thread(target=intentar_reserva, args=(2,))

# Lanzar ambos al mismo tiempo
t1.start()
t2.start()
t1.join()
t2.join()

# ─── Mostrar resultados ───────────────────────────────────────────────────────
print("─" * 60)
for r in sorted(resultados, key=lambda x: x["request"]):
    print(f"\n  Request #{r['request']}")
    print(f"  HTTP Status : {r['status']}")
    print(f"  Resultado   : {r['resultado']}")
    if "id" in r:
        print(f"  Reserva ID  : {r['id']}")
    if "detalle" in r:
        print(f"  Detalle     : {r['detalle']}")

print("\n" + "─" * 60)

# ─── Verificación automática ──────────────────────────────────────────────────
exitosas = [r for r in resultados if r["status"] == 201]
rechazadas = [r for r in resultados if r["status"] == 400]

print("\n📊 ANÁLISIS:")
print(f"  Reservas creadas  : {len(exitosas)} (esperado: 1)")
print(f"  Requests rechazados: {len(rechazadas)} (esperado: 1)")

if len(exitosas) == 1 and len(rechazadas) == 1:
    print("\n✅ TEST PASSED — SELECT FOR UPDATE previno el doble booking correctamente.")
    print("   La transacción ACID garantizó que solo una reserva fue aceptada.")
elif len(exitosas) == 2:
    print("\n🚨 TEST FAILED — Se crearon DOS reservas para las mismas fechas.")
    print("   El mecanismo de locking no está funcionando correctamente.")
else:
    print("\n⚠️  Resultado inesperado — revisar logs del backend.")

print("=" * 60)
