"""
seed.py — Datos de prueba para StayHub
=======================================
Inserta usuarios, propiedades, reservas y reseñas en la base de datos
usando la API directamente (respeta las validaciones de Pydantic y la
lógica de negocio, igual que un cliente real).

USO:
    docker compose run --rm backend uv run python scripts/seed.py

IMPORTANTE: La DB debe estar vacía o el script detecta datos existentes.
Si querés resetear: docker compose down -v && docker compose up -d
y luego correr las migraciones antes del seed.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE_URL = "http://stayhub_api:8000"

# ─── Colores para la terminal ─────────────────────────────────────────────────
OK   = "✅"
FAIL = "❌"
INFO = "📋"
SKIP = "⏭️ "


def post(endpoint: str, payload: dict) -> dict | None:
    """Hace un POST a la API y devuelve el JSON de respuesta."""
    data = json.dumps(payload, default=str).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        print(f"     {FAIL} HTTP {e.code}: {body.get('detail', body)}")
        return None


def get(endpoint: str) -> list | dict | None:
    """Hace un GET a la API y devuelve el JSON de respuesta."""
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        print(f"     {FAIL} HTTP {e.code}: {body.get('detail', body)}")
        return None


# ─── 1. USUARIOS ──────────────────────────────────────────────────────────────
print(f"\n{INFO} Verificando usuarios existentes...")
usuarios_existentes = get("/usuarios/") or []

if len(usuarios_existentes) >= 4:
    print(f"   {SKIP} Ya hay {len(usuarios_existentes)} usuarios. Saltando creación.")
    usuarios = usuarios_existentes[:4]
else:
    print(f"\n{INFO} Creando usuarios...")

    usuarios_data = [
        {
            "nombre": "Carlos Moya",
            "email": "carlos.moya@stayhub.com",
            "password": "Admin1234!",
            "rol": "admin",
        },
        {
            "nombre": "Ana Iriarte Lopez",
            "email": "ana.iriarte@stayhub.com",
            "password": "Propietaria1!",
            "rol": "propietario",
        },
        {
            "nombre": "Solange Parada",
            "email": "solange.parada@stayhub.com",
            "password": "Huesped123!",
            "rol": "huesped",
        },
        {
            "nombre": "Tomas Reali",
            "email": "tomas.reali@stayhub.com",
            "password": "Huesped456!",
            "rol": "huesped",
        },
    ]

    usuarios = []
    for u in usuarios_data:
        resultado = post("/usuarios/", u)
        if resultado:
            usuarios.append(resultado)
            print(f"   {OK} Usuario creado: {resultado['nombre']} (id={resultado['id']}, rol={resultado['rol']})")
        else:
            print(f"   {FAIL} No se pudo crear: {u['email']}")

if not usuarios:
    print(f"\n{FAIL} No hay usuarios. Abortando seed.")
    sys.exit(1)

# Asignar IDs por rol para usarlos después
propietario = next((u for u in usuarios if u["rol"] == "propietario"), usuarios[0])
huespedes = [u for u in usuarios if u["rol"] == "huesped"]
huesped_1 = huespedes[0] if len(huespedes) > 0 else usuarios[-1]
huesped_2 = huespedes[1] if len(huespedes) > 1 else usuarios[-1]


# ─── 2. PROPIEDADES ───────────────────────────────────────────────────────────
print(f"\n{INFO} Verificando propiedades existentes...")
propiedades_existentes = get("/propiedades/") or []

if len(propiedades_existentes) >= 3:
    print(f"   {SKIP} Ya hay {len(propiedades_existentes)} propiedades. Saltando creación.")
    propiedades = propiedades_existentes[:3]
else:
    print(f"\n{INFO} Creando propiedades...")

    # Coordenadas: POINT(longitud latitud) — formato WKT obligatorio
    propiedades_data = [
        {
            "propietario_id": propietario["id"],
            "nombre": "Casa del Valle — Mendoza",
            "descripcion": "Acogedora casa con vista a la cordillera. Ideal para parejas.",
            "tipo": "casa",
            "ciudad": "Mendoza",
            "direccion": "Ruta 40 Km 1020, Luján de Cuyo",
            "ubicacion": "POINT(-68.8648 -33.0458)",   # longitud latitud
            "precio": 8500.00,
            "amenidades": {
                "wifi": True,
                "estacionamiento": True,
                "cocina": True,
                "calefaccion": True,
            },
            "tags": ["casa", "montaña", "mendoza", "cordillera"],
        },
        {
            "propietario_id": propietario["id"],
            "nombre": "Departamento Centro — San Rafael",
            "descripcion": "Depto moderno a 2 cuadras de la peatonal. Ideal para viajes de trabajo.",
            "tipo": "departamento",
            "ciudad": "San Rafael",
            "direccion": "Av. Hipólito Yrigoyen 1234, piso 3",
            "ubicacion": "POINT(-68.3302 -34.6175)",
            "precio": 4200.00,
            "amenidades": {
                "wifi": True,
                "aire_acondicionado": True,
                "cocina": True,
                "tv": True,
            },
            "tags": ["departamento", "centro", "san-rafael", "ejecutivo"],
        },
        {
            "propietario_id": propietario["id"],
            "nombre": "Casa con Pileta — General Alvear",
            "descripcion": "Casa familiar con pileta y jardín. Capacidad para 8 personas.",
            "tipo": "casa",
            "ciudad": "General Alvear",
            "direccion": "Calle Los Álamos 456",
            "ubicacion": "POINT(-67.6932 -34.9783)",
            "precio": 12000.00,
            "amenidades": {
                "pileta": True,
                "parrilla": True,
                "wifi": True,
                "estacionamiento": True,
                "jardín": True,
            },
            "tags": ["casa", "familia", "pileta", "general-alvear"],
        },
    ]

    propiedades = []
    for p in propiedades_data:
        resultado = post("/propiedades/", p)
        if resultado:
            propiedades.append(resultado)
            print(f"   {OK} Propiedad creada: {resultado['nombre']} (id={resultado['id']}, ${resultado['precio']}/noche)")
        else:
            print(f"   {FAIL} No se pudo crear: {p['nombre']}")

if not propiedades:
    print(f"\n{FAIL} No hay propiedades. Abortando seed.")
    sys.exit(1)

propiedad_1 = propiedades[0]
propiedad_2 = propiedades[1] if len(propiedades) > 1 else propiedades[0]


# ─── 3. RESERVAS ──────────────────────────────────────────────────────────────
print(f"\n{INFO} Verificando reservas existentes...")
reservas_existentes = get("/reservas/") or []

if len(reservas_existentes) >= 3:
    print(f"   {SKIP} Ya hay {len(reservas_existentes)} reservas. Saltando creación.")
    reservas = reservas_existentes[:2]
else:
    print(f"\n{INFO} Creando reservas...")

    hoy = date.today()

    reservas_data = [
        {   # Reserva confirmada — propiedad 1, huesped 1
            "propiedad_id": propiedad_1["id"],
            "huesped_id": huesped_1["id"],
            "fecha_checkin": str(hoy + timedelta(days=10)),
            "fecha_checkout": str(hoy + timedelta(days=15)),
            "precio_total": propiedad_1["precio"] * 5,
            "estado": "confirmada",
        },
        {   # Reserva pendiente — propiedad 2, huesped 2
            "propiedad_id": propiedad_2["id"],
            "huesped_id": huesped_2["id"],
            "fecha_checkin": str(hoy + timedelta(days=20)),
            "fecha_checkout": str(hoy + timedelta(days=25)),
            "precio_total": propiedad_2["precio"] * 5,
            "estado": "pendiente",
        },
        {   # Reserva completada (pasada) — para poder agregar reseña
            "propiedad_id": propiedad_1["id"],
            "huesped_id": huesped_2["id"],
            "fecha_checkin": str(hoy - timedelta(days=30)),
            "fecha_checkout": str(hoy - timedelta(days=25)),
            "precio_total": propiedad_1["precio"] * 5,
            "estado": "completada",
        },
    ]

    reservas = []
    for r in reservas_data:
        resultado = post("/reservas/", r)
        if resultado:
            reservas.append(resultado)
            print(f"   {OK} Reserva creada: id={resultado['id']} | {resultado['fecha_checkin']} → {resultado['fecha_checkout']} | estado={resultado['estado']}")
        else:
            print(f"   {FAIL} No se pudo crear reserva para propiedad_id={r['propiedad_id']}")

# Buscar la reserva completada para la reseña
reserva_completada = next(
    (r for r in (reservas or reservas_existentes) if r.get("estado") == "completada"),
    None
)


# ─── 4. RESEÑAS ───────────────────────────────────────────────────────────────
if reserva_completada:
    print(f"\n{INFO} Verificando reseñas existentes...")
    resenas_existentes = get("/rese%C3%B1as/") or []

    if resenas_existentes:
        print(f"   {SKIP} Ya hay {len(resenas_existentes)} reseña(s). Saltando creación.")
    else:
        print(f"\n{INFO} Creando reseña...")
        resena = post("/rese%C3%B1as/", {
            "reserva_id": reserva_completada["id"],
            "propiedad_id": reserva_completada["propiedad_id"],
            "huesped_id": reserva_completada["huesped_id"],
            "puntuacion": 5,
            "comentario": "Excelente lugar. Muy limpio y cómodo, volvería sin dudarlo.",
        })
        if resena:
            print(f"   {OK} Reseña creada: id={resena['id']} | puntuación={resena['puntuacion']}/5")
else:
    print(f"\n   {SKIP} No hay reserva completada disponible para crear reseña.")


# ─── Resumen final ────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  SEED COMPLETADO — StayHub")
print("=" * 55)
print(f"\n  Podés verificar los datos en:")
print(f"  → pgAdmin:  http://localhost:5050")
print(f"  → API docs: http://localhost:8000/docs")
print(f"\n  Para probar doble booking:")
print(f"  docker compose run --rm backend uv run python scripts/test_concurrencia.py")
print("=" * 55 + "\n")
