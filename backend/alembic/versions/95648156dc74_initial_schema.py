"""initial schema

Revision ID: 95648156dc74
Revises: 
Create Date: 2026-06-17 14:06:52.604098

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType

# revision identifiers, used by Alembic.
revision: str = "95648156dc74"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class GeometryPoint4326(UserDefinedType):
    def get_col_spec(self, **kw: object) -> str:
        return "GEOMETRY(Point, 4326)"


def upgrade() -> None:
    """Create the full baseline schema from scratch."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("usuarios_pkey")),
        sa.UniqueConstraint("email", name=op.f("usuarios_email_key")),
        sa.CheckConstraint(
            "rol IN ('huesped', 'propietario', 'admin')",
            name=op.f("usuarios_rol_check"),
        ),
    )

    op.create_table(
        "propiedades",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "propietario_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("ciudad", sa.String(length=100), nullable=False),
        sa.Column("direccion", sa.Text(), nullable=False),
        sa.Column("ubicacion", GeometryPoint4326(), nullable=True),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "amenidades",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'disponible'")),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True, server_default=sa.text("0")),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("propiedades_pkey")),
        sa.ForeignKeyConstraint(
            ["propietario_id"],
            ["usuarios.id"],
            name=op.f("propiedades_propietario_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "tipo IN ('departamento', 'casa', 'cabaña', 'habitacion')",
            name=op.f("propiedades_tipo_check"),
        ),
        sa.CheckConstraint(
            "estado IN ('disponible', 'pausada', 'eliminada')",
            name=op.f("propiedades_estado_check"),
        ),
    )

    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("propiedad_id", sa.Integer(), nullable=False),
        sa.Column("huesped_id", sa.Integer(), nullable=False),
        sa.Column("fecha_checkin", sa.Date(), nullable=False),
        sa.Column("fecha_checkout", sa.Date(), nullable=False),
        sa.Column("precio_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'pendiente'")),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("reservas_pkey")),
        sa.ForeignKeyConstraint(
            ["propiedad_id"],
            ["propiedades.id"],
            name=op.f("reservas_propiedad_id_fkey"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["huesped_id"],
            ["usuarios.id"],
            name=op.f("reservas_huesped_id_fkey"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "fecha_checkout > fecha_checkin",
            name=op.f("fechas_validas"),
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'confirmada', 'cancelada', 'completada')",
            name=op.f("reservas_estado_check"),
        ),
    )

    op.create_table(
        "reseñas",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("reserva_id", sa.Integer(), nullable=False),
        sa.Column("propiedad_id", sa.Integer(), nullable=False),
        sa.Column("huesped_id", sa.Integer(), nullable=False),
        sa.Column("puntuacion", sa.SmallInteger(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("reseñas_pkey")),
        sa.UniqueConstraint("reserva_id", name=op.f("reseñas_reserva_id_key")),
        sa.ForeignKeyConstraint(
            ["reserva_id"],
            ["reservas.id"],
            name=op.f("reseñas_reserva_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["propiedad_id"],
            ["propiedades.id"],
            name=op.f("reseñas_propiedad_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["huesped_id"],
            ["usuarios.id"],
            name=op.f("reseñas_huesped_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("puntuacion BETWEEN 1 AND 5", name=op.f("reseñas_puntuacion_check")),
    )

    op.create_table(
        "logs_actividad",
        sa.Column("id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=100), nullable=False),
        sa.Column("tabla", sa.String(length=100), nullable=True),
        sa.Column("registro_id", sa.Integer(), nullable=True),
        sa.Column(
            "detalle",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("logs_actividad_pkey")),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("logs_actividad_usuario_id_fkey"),
            ondelete="SET NULL",
        ),
    )

    # Core search and access-path indexes.
    op.create_index("idx_propiedades_precio", "propiedades", ["precio"], unique=False)
    op.create_index("idx_reservas_fechas", "reservas", ["fecha_checkin", "fecha_checkout"], unique=False)
    op.create_index("idx_reservas_creado_en", "reservas", ["creado_en"], unique=False)
    op.create_index("idx_usuarios_email_hash", "usuarios", ["email"], unique=False, postgresql_using="hash")
    op.create_index("idx_reservas_estado", "reservas", ["estado"], unique=False)
    op.create_index("idx_propiedades_tipo", "propiedades", ["tipo"], unique=False)
    op.create_index("idx_propiedades_ciudad_precio", "propiedades", ["ciudad", "precio"], unique=False)
    op.create_index("idx_reservas_estado_checkin", "reservas", ["estado", "fecha_checkin"], unique=False)
    op.create_index(
        "idx_reservas_activas",
        "reservas",
        ["propiedad_id", "fecha_checkin"],
        unique=False,
        postgresql_where=sa.text("estado IN ('pendiente', 'confirmada')"),
    )
    op.create_index(
        "idx_propiedades_disponibles",
        "propiedades",
        ["ciudad", "precio"],
        unique=False,
        postgresql_where=sa.text("estado = 'disponible'"),
    )
    op.create_index(
        "idx_propiedades_cubriente",
        "propiedades",
        ["id", "precio"],
        unique=False,
        postgresql_include=["nombre", "rating", "tipo"],
    )
    op.create_index(
        "idx_usuarios_email_lower",
        "usuarios",
        [sa.text("lower(email)")],
        unique=False,
    )
    op.create_index(
        "idx_logs_brin",
        "logs_actividad",
        ["creado_en"],
        unique=False,
        postgresql_using="brin",
        postgresql_with={"pages_per_range": 128},
    )
    op.create_index(
        "idx_propiedades_amenidades_gin",
        "propiedades",
        ["amenidades"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_propiedades_tags_gin",
        "propiedades",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_propiedades_fulltext_gin",
        "propiedades",
        [sa.text("to_tsvector('spanish', coalesce(nombre, '') || ' ' || coalesce(descripcion, ''))")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index("idx_propiedades_ubicacion_gist", "propiedades", ["ubicacion"], unique=False, postgresql_using="gist")

    # Extra indexes already represented in the current ORM models.
    op.create_index("ix_ciudad_estado", "propiedades", ["ciudad", "estado"], unique=False)
    op.create_index("ix_amenidades_gin", "propiedades", ["amenidades"], unique=False, postgresql_using="gin")
    op.create_index(op.f("ix_propiedades_ciudad"), "propiedades", ["ciudad"], unique=False)
    op.create_index(op.f("ix_usuarios_rol"), "usuarios", ["rol"], unique=False)


def downgrade() -> None:
    """Drop the baseline schema in reverse order."""
    op.drop_index(op.f("ix_usuarios_rol"), table_name="usuarios")
    op.drop_index(op.f("ix_propiedades_ciudad"), table_name="propiedades")
    op.drop_index("ix_amenidades_gin", table_name="propiedades", postgresql_using="gin")
    op.drop_index("ix_ciudad_estado", table_name="propiedades")
    op.drop_index("idx_propiedades_ubicacion_gist", table_name="propiedades", postgresql_using="gist")
    op.drop_index("idx_propiedades_fulltext_gin", table_name="propiedades", postgresql_using="gin")
    op.drop_index("idx_propiedades_tags_gin", table_name="propiedades", postgresql_using="gin")
    op.drop_index("idx_propiedades_amenidades_gin", table_name="propiedades", postgresql_using="gin")
    op.drop_index("idx_logs_brin", table_name="logs_actividad", postgresql_using="brin")
    op.drop_index("idx_usuarios_email_lower", table_name="usuarios")
    op.drop_index("idx_propiedades_cubriente", table_name="propiedades")
    op.drop_index("idx_propiedades_disponibles", table_name="propiedades")
    op.drop_index("idx_reservas_activas", table_name="reservas")
    op.drop_index("idx_reservas_estado_checkin", table_name="reservas")
    op.drop_index("idx_propiedades_ciudad_precio", table_name="propiedades")
    op.drop_index("idx_propiedades_tipo", table_name="propiedades")
    op.drop_index("idx_reservas_estado", table_name="reservas")
    op.drop_index("idx_usuarios_email_hash", table_name="usuarios")
    op.drop_index("idx_reservas_creado_en", table_name="reservas")
    op.drop_index("idx_reservas_fechas", table_name="reservas")
    op.drop_index("idx_propiedades_precio", table_name="propiedades")

    op.drop_table("logs_actividad")
    op.drop_table("reseñas")
    op.drop_table("reservas")
    op.drop_table("propiedades")
    op.drop_table("usuarios")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS postgis")