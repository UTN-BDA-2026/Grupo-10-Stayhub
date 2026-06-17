-- 1. Creamos un usuario exclusivo para la API (no es superusuario)
CREATE ROLE api_stayhub WITH LOGIN PASSWORD 'ApiSecurePass2026!';

-- 2. Revocamos el acceso por defecto para evitar que usuarios no autorizados vean la estructura
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- 3. Le damos permiso de uso del esquema al nuevo usuario
GRANT USAGE ON SCHEMA public TO api_stayhub;

-- 4. Le otorgamos permisos estrictamente operativos sobre las tablas (Menor Privilegio)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_stayhub;

-- 5. Permitimos que use las secuencias (necesario para que funcionen los IDs autoincrementales)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_stayhub;

-- 6. Garantizamos que cualquier tabla FUTURA que creen tus compañeros también aplique esta regla
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_stayhub;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO api_stayhub;