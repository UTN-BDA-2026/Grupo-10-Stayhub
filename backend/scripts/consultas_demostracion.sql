-- ==============================================================================
-- CONSULTAS DE DEMOSTRACIÓN PARA LA DEFENSA (STAYHUB)
-- Estas consultas están diseñadas para demostrar el uso de índices complejos,
-- joins relacionales y funciones avanzadas de PostgreSQL.
-- ==============================================================================

-- 1. BÚSQUEDA CON JSONB (Usa el índice GIN en la columna amenidades)
-- Busca todas las propiedades que tengan 'wifi' y 'pileta' activados.
SELECT id, nombre, ciudad, precio 
FROM propiedades 
WHERE amenidades @> '{"wifi": true, "pileta": true}';

-- 2. BÚSQUEDA GEOESPACIAL (Usa el índice GiST en la columna ubicacion)
-- Busca propiedades en un radio de 50km desde el centro de Mendoza (-68.8458, -32.9000).
-- Usamos ST_DWithin casteando a geography para medir en metros (50000m).
SELECT id, nombre, direccion, ciudad 
FROM propiedades 
WHERE ST_DWithin(
    ubicacion::geography, 
    ST_MakePoint(-68.8458, -32.9000)::geography, 
    50000
);

-- 3. JOIN MULTIPLE CON AGREGACIÓN
-- Obtiene el total de ingresos por propietario, sumando el precio_total de sus reservas completadas.
SELECT 
    u.nombre AS propietario,
    u.email,
    COUNT(r.id) as cantidad_reservas,
    SUM(r.precio_total) as ingresos_totales
FROM usuarios u
JOIN propiedades p ON u.id = p.propietario_id
JOIN reservas r ON p.id = r.propiedad_id
WHERE r.estado = 'completada'
GROUP BY u.id, u.nombre, u.email
ORDER BY ingresos_totales DESC;

-- 4. CONSULTA DE DISPONIBILIDAD CON FECHAS (Overlap)
-- Busca propiedades disponibles en Bariloche para unas fechas específicas
-- (Asegurándose de que no haya cruce con reservas existentes).
SELECT p.id, p.nombre, p.precio 
FROM propiedades p
WHERE p.ciudad = 'Bariloche'
  AND p.estado = 'disponible'
  AND NOT EXISTS (
      SELECT 1 FROM reservas r 
      WHERE r.propiedad_id = p.id 
        AND r.estado IN ('confirmada', 'pendiente')
        AND r.fecha_checkin < '2026-08-15' 
        AND r.fecha_checkout > '2026-08-01'
  );

-- 5. CÁLCULO DE RATING PROMEDIO (Relación Reseñas -> Propiedades)
-- Muestra las propiedades ordenadas por su calificación promedio.
SELECT 
    p.nombre,
    p.ciudad,
    ROUND(AVG(re.puntuacion), 2) AS rating_promedio,
    COUNT(re.id) AS cantidad_resenas
FROM propiedades p
LEFT JOIN reseñas re ON p.id = re.propiedad_id
GROUP BY p.id, p.nombre, p.ciudad
HAVING COUNT(re.id) > 0
ORDER BY rating_promedio DESC;

-- 6. FULL TEXT SEARCH BÁSICO EN DESCRIPCIÓN O TAGS
-- (Si se usan arrays o cadenas simples)
SELECT nombre, tags 
FROM propiedades 
WHERE 'montaña' = ANY(tags);

-- 7. DEMOSTRACIÓN DE BLOQUEO PARA CONCURRENCIA (FOR UPDATE)
-- Esta es la consulta equivalente a la que hace el backend en `crear_reserva_segura`
-- para evitar sobreventas (race conditions).
BEGIN;
SELECT id, nombre, estado 
FROM propiedades 
WHERE id = 1 
FOR UPDATE;
-- (Acá ocurriría la lógica de verificación y la inserción de la reserva)
COMMIT;

-- 8. FUNCIONES DE VENTANA (Window Functions)
-- Ranquea las propiedades dentro de cada ciudad según su precio (del más caro al más barato).
SELECT 
    nombre, 
    ciudad, 
    precio,
    RANK() OVER (PARTITION BY ciudad ORDER BY precio DESC) as ranking_precio_ciudad
FROM propiedades;

-- 9. COMMON TABLE EXPRESSIONS (WITH) Y MANEJO DE FECHAS
-- Calcula el total de noches reservadas por propiedad cruzando con CTE.
WITH NochesPorReserva AS (
    SELECT 
        propiedad_id,
        (fecha_checkout - fecha_checkin) AS cantidad_noches,
        precio_total
    FROM reservas
    WHERE estado IN ('completada', 'confirmada')
)
SELECT 
    p.nombre,
    SUM(n.cantidad_noches) as total_noches_vendidas,
    SUM(n.precio_total) as recaudacion_total
FROM propiedades p
JOIN NochesPorReserva n ON p.id = n.propiedad_id
GROUP BY p.id, p.nombre
ORDER BY recaudacion_total DESC;

-- 10. SUBCONSULTAS CORRELACIONADAS
-- Encuentra las propiedades cuyo precio está por encima del precio promedio DE SU MISMA CIUDAD.
SELECT p1.nombre, p1.ciudad, p1.precio 
FROM propiedades p1
WHERE p1.precio > (
    SELECT AVG(p2.precio) 
    FROM propiedades p2 
    WHERE p1.ciudad = p2.ciudad
);
