-- Consultas para Analizar Horario LLR Generado
-- Base de Datos: db.sqlite3
-- Horario ID: 21 (LLR Test Optimizado)

-- ============================================
-- 1. VER ASIGNACIONES COMPLETAS
-- ============================================
SELECT 
    sa.id AS asignacion_id,
    c.xml_id AS clase_id,
    co.code AS curso,
    r.xml_id AS aula_id,
    r.capacity AS capacidad_aula,
    c.class_limit AS estudiantes_clase,
    ts.days AS dias_binario,
    CASE 
        WHEN substr(ts.days, 1, 1) = '1' THEN 'L'
        ELSE ''
    END ||
    CASE 
        WHEN substr(ts.days, 2, 1) = '1' THEN 'M'
        ELSE ''
    END ||
    CASE 
        WHEN substr(ts.days, 3, 1) = '1' THEN 'X'
        ELSE ''
    END ||
    CASE 
        WHEN substr(ts.days, 4, 1) = '1' THEN 'J'
        ELSE ''
    END ||
    CASE 
        WHEN substr(ts.days, 5, 1) = '1' THEN 'V'
        ELSE ''
    END AS dias_texto,
    printf('%02d:%02d', ts.start_time * 5 / 60, (ts.start_time * 5) % 60) AS hora_inicio,
    ts.length * 5 AS duracion_min,
    printf('%02d:%02d', (ts.start_time + ts.length) * 5 / 60, ((ts.start_time + ts.length) * 5) % 60) AS hora_fin
FROM schedule_assignments sa
JOIN classes c ON sa.class_obj_id = c.id
JOIN rooms r ON sa.room_id = r.id
JOIN time_slots ts ON sa.time_slot_id = ts.id
LEFT JOIN courses co ON c.offering_id = co.id
WHERE sa.schedule_id = 21
ORDER BY ts.days, ts.start_time
LIMIT 20;

-- ============================================
-- 2. VER CLASES DE UN DÍA ESPECÍFICO (Lunes)
-- ============================================
SELECT 
    c.xml_id AS clase,
    co.code AS curso,
    r.xml_id AS aula,
    printf('%02d:%02d', ts.start_time * 5 / 60, (ts.start_time * 5) % 60) AS inicio,
    printf('%02d:%02d', (ts.start_time + ts.length) * 5 / 60, ((ts.start_time + ts.length) * 5) % 60) AS fin,
    ts.length * 5 AS minutos,
    c.class_limit AS estudiantes
FROM schedule_assignments sa
JOIN classes c ON sa.class_obj_id = c.id
JOIN rooms r ON sa.room_id = r.id
JOIN time_slots ts ON sa.time_slot_id = ts.id
LEFT JOIN courses co ON c.offering_id = co.id
WHERE sa.schedule_id = 21
  AND substr(ts.days, 1, 1) = '1'  -- Lunes
ORDER BY ts.start_time, r.xml_id;

-- ============================================
-- 3. CONFLICTOS DE AULA (mismo horario, misma aula)
-- ============================================
SELECT 
    r.xml_id AS aula,
    COUNT(*) AS num_clases,
    GROUP_CONCAT(c.xml_id) AS clases_conflicto,
    ts.days AS dias,
    printf('%02d:%02d', ts.start_time * 5 / 60, (ts.start_time * 5) % 60) AS hora
FROM schedule_assignments sa1
JOIN schedule_assignments sa2 ON 
    sa1.schedule_id = sa2.schedule_id 
    AND sa1.room_id = sa2.room_id
    AND sa1.id != sa2.id
JOIN classes c ON sa1.class_obj_id = c.id
JOIN rooms r ON sa1.room_id = r.id
JOIN time_slots ts1 ON sa1.time_slot_id = ts1.id
JOIN time_slots ts2 ON sa2.time_slot_id = ts2.id
WHERE sa1.schedule_id = 21
  AND ts1.days = ts2.days
  AND ts1.start_time < ts2.start_time + ts2.length
  AND ts2.start_time < ts1.start_time + ts1.length
GROUP BY r.xml_id, ts1.days, ts1.start_time
HAVING COUNT(*) > 1;

-- ============================================
-- 4. CONFLICTOS DE INSTRUCTOR (mismo horario)
-- ============================================
SELECT 
    i.xml_id AS instructor,
    i.name AS nombre,
    COUNT(*) AS num_clases_simultaneas,
    GROUP_CONCAT(c.xml_id) AS clases,
    ts.days AS dias,
    printf('%02d:%02d', ts.start_time * 5 / 60, (ts.start_time * 5) % 60) AS hora
FROM schedule_assignments sa1
JOIN schedule_assignments sa2 ON 
    sa1.schedule_id = sa2.schedule_id 
    AND sa1.id != sa2.id
JOIN classes c1 ON sa1.class_obj_id = c1.id
JOIN classes c2 ON sa2.class_obj_id = c2.id
JOIN class_instructors ci1 ON c1.id = ci1.class_obj_id
JOIN class_instructors ci2 ON c2.id = ci2.class_obj_id
    AND ci1.instructor_id = ci2.instructor_id
JOIN instructors i ON ci1.instructor_id = i.id
JOIN time_slots ts1 ON sa1.time_slot_id = ts1.id
JOIN time_slots ts2 ON sa2.time_slot_id = ts2.id
JOIN classes c ON sa1.class_obj_id = c.id
JOIN time_slots ts ON sa1.time_slot_id = ts.id
WHERE sa1.schedule_id = 21
  AND ts1.days = ts2.days
  AND ts1.start_time < ts2.start_time + ts2.length
  AND ts2.start_time < ts1.start_time + ts1.length
GROUP BY i.xml_id, ts.days, ts.start_time
HAVING COUNT(*) > 1;

-- ============================================
-- 5. UTILIZACIÓN DE AULAS POR DÍA
-- ============================================
SELECT 
    r.xml_id AS aula,
    r.capacity AS capacidad,
    CASE 
        WHEN substr(ts.days, 1, 1) = '1' THEN 'Lunes'
        WHEN substr(ts.days, 2, 1) = '1' THEN 'Martes'
        WHEN substr(ts.days, 3, 1) = '1' THEN 'Miércoles'
        WHEN substr(ts.days, 4, 1) = '1' THEN 'Jueves'
        WHEN substr(ts.days, 5, 1) = '1' THEN 'Viernes'
    END AS dia,
    COUNT(*) AS num_clases,
    SUM(ts.length * 5) AS minutos_ocupados,
    ROUND(SUM(ts.length * 5) / 600.0 * 100, 1) AS porcentaje_uso  -- Asumiendo 10h disponibles
FROM schedule_assignments sa
JOIN rooms r ON sa.room_id = r.id
JOIN time_slots ts ON sa.time_slot_id = ts.id
WHERE sa.schedule_id = 21
GROUP BY r.xml_id, 
    CASE 
        WHEN substr(ts.days, 1, 1) = '1' THEN 'Lunes'
        WHEN substr(ts.days, 2, 1) = '1' THEN 'Martes'
        WHEN substr(ts.days, 3, 1) = '1' THEN 'Miércoles'
        WHEN substr(ts.days, 4, 1) = '1' THEN 'Jueves'
        WHEN substr(ts.days, 5, 1) = '1' THEN 'Viernes'
    END
ORDER BY num_clases DESC;

-- ============================================
-- 6. CLASES POR FRANJA HORARIA
-- ============================================
SELECT 
    printf('%02d:00', ts.start_time * 5 / 60) AS franja,
    COUNT(*) AS num_clases,
    GROUP_CONCAT(DISTINCT r.xml_id) AS aulas_usadas
FROM schedule_assignments sa
JOIN time_slots ts ON sa.time_slot_id = ts.id
JOIN rooms r ON sa.room_id = r.id
WHERE sa.schedule_id = 21
GROUP BY ts.start_time * 5 / 60
ORDER BY ts.start_time;

-- ============================================
-- 7. VIOLACIONES DE CAPACIDAD
-- ============================================
SELECT 
    c.xml_id AS clase,
    co.code AS curso,
    c.class_limit AS estudiantes,
    r.xml_id AS aula,
    r.capacity AS capacidad_aula,
    (r.capacity - c.class_limit) AS diferencia,
    CASE 
        WHEN r.capacity < c.class_limit THEN 'VIOLACIÓN'
        WHEN r.capacity < c.class_limit * 1.1 THEN 'Justo'
        ELSE 'Holgado'
    END AS estado
FROM schedule_assignments sa
JOIN classes c ON sa.class_obj_id = c.id
JOIN rooms r ON sa.room_id = r.id
LEFT JOIN courses co ON c.offering_id = co.id
WHERE sa.schedule_id = 21
  AND r.capacity < c.class_limit
ORDER BY diferencia;

-- ============================================
-- 8. RESUMEN GENERAL DEL HORARIO
-- ============================================
SELECT 
    'Clases asignadas' AS metrica,
    COUNT(*) AS valor
FROM schedule_assignments
WHERE schedule_id = 21
UNION ALL
SELECT 
    'Aulas utilizadas',
    COUNT(DISTINCT room_id)
FROM schedule_assignments
WHERE schedule_id = 21
UNION ALL
SELECT 
    'Instructores asignados',
    COUNT(DISTINCT ci.instructor_id)
FROM schedule_assignments sa
JOIN class_instructors ci ON sa.class_obj_id = ci.class_obj_id
WHERE sa.schedule_id = 21
UNION ALL
SELECT 
    'Timeslots únicos',
    COUNT(DISTINCT time_slot_id)
FROM schedule_assignments
WHERE schedule_id = 21;

-- ============================================
-- 9. CARGA DE INSTRUCTORES
-- ============================================
SELECT 
    i.xml_id AS instructor,
    i.name AS nombre,
    COUNT(DISTINCT c.id) AS num_clases,
    COUNT(DISTINCT ts.days || '-' || ts.start_time) AS sesiones_unicas,
    SUM(ts.length * 5) AS minutos_totales
FROM schedule_assignments sa
JOIN classes c ON sa.class_obj_id = c.id
JOIN class_instructors ci ON c.id = ci.class_obj_id
JOIN instructors i ON ci.instructor_id = i.id
JOIN time_slots ts ON sa.time_slot_id = ts.id
WHERE sa.schedule_id = 21
GROUP BY i.xml_id
ORDER BY num_clases DESC
LIMIT 20;

-- ============================================
-- 10. RESTRICCIONES BTB VIOLADAS
-- ============================================
SELECT 
    gc.constraint_type AS tipo_restriccion,
    gc.preference AS preferencia,
    COUNT(*) AS num_restricciones
FROM group_constraints gc
JOIN group_constraint_classes gcc ON gc.id = gcc.constraint_id
GROUP BY gc.constraint_type, gc.preference;
