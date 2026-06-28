import asyncio
import os
import sys
from datetime import date, timedelta
from typing import List

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, engine, connect_to_mongo, close_mongo, get_mongo_db

from app.schemas.usuario import UsuarioCreate
from app.repositories.usuario import UsuarioRepository

from app.schemas.propiedad import PropiedadCreate
from app.repositories.propiedad import PropiedadRepository

from app.schemas.reserva import ReservaCreate
from app.repositories.reserva import ReservaRepository

from app.schemas.resena import ResenaCreate
from app.repositories.resena import ResenaRepository

from app.utils.log_utils import registrar_actividad

# ==============================================================================
# DATOS DUMMY
# ==============================================================================

USUARIOS_DATA = [
    # ADMIN
    {"nombre": "Admin General", "email": "admin@stayhub.com", "password": "adminpassword123", "rol": "admin"},
    # PROPIETARIOS
    {"nombre": "Carlos Moya", "email": "carlos@stayhub.com", "password": "password123", "rol": "propietario"},
    {"nombre": "Sol Parada", "email": "sol@stayhub.com", "password": "password123", "rol": "propietario"},
    {"nombre": "Tomas Lujan", "email": "tomi@stayhub.com", "password": "password123", "rol": "propietario"},
    # HUESPEDES
    {"nombre": "Huesped Frecuente", "email": "frecuente@gmail.com", "password": "password123", "rol": "huesped"},
    {"nombre": "Ana Viajera", "email": "ana.v@gmail.com", "password": "password123", "rol": "huesped"},
    {"nombre": "Juan Perez", "email": "juanp@gmail.com", "password": "password123", "rol": "huesped"},
    {"nombre": "Laura Turista", "email": "laura@gmail.com", "password": "password123", "rol": "huesped"},
]

PROPIEDADES_DATA = [
    # Props Carlos
    {"propietario_email": "carlos@stayhub.com", "nombre": "Casa en Mendoza", "tipo": "casa", "ciudad": "Mendoza", "direccion": "San Martin 123", "precio": 75000, "amenidades": {"wifi": True, "pileta": True, "cochera": True}, "tags": ["montaña", "vino", "relax"], "ubicacion": "POINT(-68.8272 -32.8908)"},
    {"propietario_email": "carlos@stayhub.com", "nombre": "Depto Centro MZA", "tipo": "departamento", "ciudad": "Mendoza", "direccion": "Colon 456", "precio": 45000, "amenidades": {"wifi": True, "pileta": False}, "tags": ["centro", "trabajo"], "ubicacion": "POINT(-68.8415 -32.8890)"},
    # Props Sol
    {"propietario_email": "sol@stayhub.com", "nombre": "Casa Bosque Bariloche", "tipo": "casa", "ciudad": "Bariloche", "direccion": "Bustillo Km 5", "precio": 120000, "amenidades": {"wifi": True, "pileta": False, "calefaccion": True}, "tags": ["nieve", "bosque"], "ubicacion": "POINT(-71.3000 -41.1500)"},
    {"propietario_email": "sol@stayhub.com", "nombre": "Cabaña Lago", "tipo": "cabaña", "ciudad": "Bariloche", "direccion": "Circuito Chico", "precio": 90000, "amenidades": {"wifi": False, "naturaleza": True}, "tags": ["lago", "naturaleza"], "ubicacion": "POINT(-71.4000 -41.1000)"},
    # Props Tomi
    {"propietario_email": "tomi@stayhub.com", "nombre": "Penthouse CABA", "tipo": "departamento", "ciudad": "Buenos Aires", "direccion": "Libertador 1000", "precio": 200000, "amenidades": {"wifi": True, "pileta": True, "gym": True, "seguridad": True}, "tags": ["premium", "ciudad"], "ubicacion": "POINT(-58.3816 -34.6037)"},
]

# ==============================================================================
# FUNCIONES
# ==============================================================================

async def limpiar_db(db):
    """Limpia Postgres y Mongo para empezar de cero."""
    print("🧹 Limpiando PostgreSQL...")
    # DELETE en orden inverso para respetar FKs (evita errores de permisos de TRUNCATE)
    db.execute(text("DELETE FROM reseñas;"))
    db.execute(text("DELETE FROM reservas;"))
    db.execute(text("DELETE FROM propiedades;"))
    db.execute(text("DELETE FROM usuarios;"))
    db.commit()

    print("🧹 Limpiando MongoDB...")
    mongo = get_mongo_db()
    await mongo.logs_actividad.delete_many({})

async def crear_indices_mongo():
    """Crea índices explícitos en MongoDB para optimizar consultas de logs."""
    print("⚙️ Creando índices en MongoDB...")
    mongo = get_mongo_db()
    # Indice para buscar logs de un usuario rápidamente
    await mongo.logs_actividad.create_index("usuario_id")
    # Indice para filtrar por tabla
    await mongo.logs_actividad.create_index("tabla")
    # Indice compuesto para ordenar por fecha de forma eficiente
    await mongo.logs_actividad.create_index([("creado_en", -1)])

async def run_seed():
    db = SessionLocal()
    await connect_to_mongo()
    mongo = get_mongo_db()

    try:
        await limpiar_db(db)
        await crear_indices_mongo()

        print("\n👤 Poblando Usuarios...")
        repo_usuarios = UsuarioRepository(db)
        usuarios_creados = {}
        for u in USUARIOS_DATA:
            user = repo_usuarios.crear(UsuarioCreate(**u))
            db.commit()
            usuarios_creados[user.email] = user
            await registrar_actividad(mongo, user.id, "CREATE", "usuarios", user.id, {"email": user.email})
            print(f"  + Usuario: {user.nombre} ({user.rol})")

        print("\n🏠 Poblando Propiedades...")
        repo_propiedades = PropiedadRepository(db)
        propiedades_creadas = []
        for p in PROPIEDADES_DATA:
            propietario = usuarios_creados[p.pop("propietario_email")]
            p["propietario_id"] = propietario.id
            # Fix temporal para la ñ del constraint
            if p["tipo"] == "cabaña": p["tipo"] = "casa"
            
            prop = repo_propiedades.crear(PropiedadCreate(**p))
            db.commit()
            propiedades_creadas.append(prop)
            await registrar_actividad(mongo, propietario.id, "CREATE", "propiedades", prop.id, {"nombre": prop.nombre})
            print(f"  + Propiedad: {prop.nombre} en {prop.ciudad}")

        print("\n📅 Poblando Reservas...")
        repo_reservas = ReservaRepository(db)
        huesped = usuarios_creados["frecuente@gmail.com"]
        prop = propiedades_creadas[0] # Casa en Mendoza

        # Reserva Pasada (Completada)
        r1_data = ReservaCreate(
            propiedad_id=prop.id,
            huesped_id=huesped.id,
            fecha_checkin=date.today() - timedelta(days=20),
            fecha_checkout=date.today() - timedelta(days=15),
            precio_total=prop.precio * 5
        )
        r1 = repo_reservas.crear(r1_data)
        db.commit()
        await registrar_actividad(mongo, huesped.id, "CREATE", "reservas", r1.id, {"estado": "completada"})
        
        # Simulamos cambio de estado a completada (ya que crear la deja en pendiente)
        r1.estado = "completada"
        db.commit()
        print(f"  + Reserva Completada: {prop.nombre} por {huesped.nombre}")

        # Reserva Futura (Confirmada)
        r2_data = ReservaCreate(
            propiedad_id=prop.id,
            huesped_id=huesped.id,
            fecha_checkin=date.today() + timedelta(days=30),
            fecha_checkout=date.today() + timedelta(days=35),
            precio_total=prop.precio * 5
        )
        r2 = repo_reservas.crear(r2_data)
        db.commit()
        r2.estado = "confirmada"
        db.commit()
        await registrar_actividad(mongo, huesped.id, "UPDATE", "reservas", r2.id, {"estado": "confirmada"})
        print(f"  + Reserva Confirmada: {prop.nombre} por {huesped.nombre}")

        print("\n⭐ Poblando Reseñas...")
        repo_resenas = ResenaRepository(db)
        resena_data = ResenaCreate(
            reserva_id=r1.id,
            propiedad_id=prop.id,
            huesped_id=huesped.id,
            puntuacion=5,
            comentario="Excelente estadía, la casa es hermosa y la vista a la montaña espectacular."
        )
        res = repo_resenas.crear(resena_data)
        db.commit()
        await registrar_actividad(mongo, huesped.id, "CREATE", "resenas", res.id, {"puntuacion": 5})
        print(f"  + Reseña: 5 estrellas en {prop.nombre}")

        print("\n✅ SEEDING COMPLETADO CON ÉXITO")

    except Exception as e:
        print(f"\n❌ Error durante el seeding: {e}")
        db.rollback()
    finally:
        db.close()
        await close_mongo()

if __name__ == "__main__":
    asyncio.run(run_seed())
