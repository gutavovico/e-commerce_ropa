-- =============================================================================
-- Migración puntual para CU10: Vestidor Virtual (Dos Motores: Local e IA Decart)
-- =============================================================================
-- Este script es idempotente y está diseñado para aplicarse sobre bases de datos
-- existentes que ya contienen la tabla 'fashionstore.sesiones_vestidor_virtual'.
--
-- NOTA: El archivo 'specs/diseno_fisico_neon.sql' se mantiene como el diseño
-- físico completo y consolidado para la creación de bases de datos nuevas desde cero.
-- =============================================================================

-- 1. Agregar columnas motor y duracion_segundos de manera idempotente
ALTER TABLE fashionstore.sesiones_vestidor_virtual
  ADD COLUMN IF NOT EXISTS motor VARCHAR(10) NOT NULL DEFAULT 'local',
  ADD COLUMN IF NOT EXISTS duracion_segundos INTEGER;

-- 2. Restricción CHECK para los valores permitidos del motor ('local' | 'ia')
ALTER TABLE fashionstore.sesiones_vestidor_virtual
  DROP CONSTRAINT IF EXISTS chk_sesiones_ar_motor;

ALTER TABLE fashionstore.sesiones_vestidor_virtual
  ADD CONSTRAINT chk_sesiones_ar_motor
  CHECK (motor IN ('local', 'ia'));

-- 3. Restricción CHECK para validar que duracion_segundos sea nula o mayor/igual a 0
ALTER TABLE fashionstore.sesiones_vestidor_virtual
  DROP CONSTRAINT IF EXISTS chk_sesiones_ar_duracion;

ALTER TABLE fashionstore.sesiones_vestidor_virtual
  ADD CONSTRAINT chk_sesiones_ar_duracion
  CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0);

