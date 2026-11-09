#!/usr/bin/env bash
# Guardas del CI: reglas de CLAUDE.md y defectos ya pagados que no deben volver.
# Cada guarda imprime las líneas que la incumplen; el script falla si alguna lo hace.
# Uso local (desde la raíz del repo):  bash .github/scripts/guardas.sh
set -uo pipefail

fallos=0

guarda() {
  local nombre="$1" salida="$2"
  if [[ -n "$salida" ]]; then
    echo "::error::Guarda «$nombre» incumplida:"
    echo "$salida"
    echo
    fallos=$((fallos + 1))
  else
    echo "ok · $nombre"
  fi
}

# 1. Credenciales escritas en el código: hashes de contraseña y contraseñas en claro
#    (migración 0017: hash y contraseña del super administrador en un repositorio público).
guarda "sin hashes de contraseña en el código" "$(
  git grep -nIE '\$argon2(id|i|d)\$|\$2[aby]\$[0-9]{2}\$' -- 'Ec-backend/app' 'Ec-backend/alembic' 'Ec-backend/scripts' || true)"
guarda "sin contraseñas en claro en migraciones y scripts" "$(
  git grep -nIiE "(password|contrase(ñ|n)a|clave|hash)[^=:]{0,30}(=|:| de )\s*['\"][^'\" ]{8,}['\"]" \
    -- 'Ec-backend/alembic' 'Ec-backend/scripts' || true)"

# 2. Archivos que nunca se versionan
guarda "sin archivos .env versionados" "$(git ls-files | grep -E '(^|/)\.env(\..+)?$' | grep -vE '\.(example|ejemplo)$' || true)"
guarda "sin __pycache__ versionado" "$(git ls-files | grep -E '__pycache__/|\.pyc$' || true)"

# 3. Moneda de la empresa (fix de P2-CU11): nunca «€» ni EUR escrito a mano
guarda "sin € ni 'EUR' en la web" "$(
  git grep -nIE "€|'EUR'" -- 'Ec-frontend/src/app' ':!*.spec.ts' || true)"
guarda "sin € ni 'EUR' en el móvil" "$(git grep -nIE "€|'EUR'" -- 'Ec-mobile/lib' || true)"

# 4. Hora de Bolivia (fix de P2-CU11, defecto 66): «hoy» solo con core/tiempo.py
guarda "sin date.today() ni datetime.now() sin zona" "$(
  git grep -nIE 'date\.today\(\)|datetime\.(now|today)\(\)|datetime\.utcnow\(\)' -- 'Ec-backend/app' \
    ':!Ec-backend/app/core/tiempo.py' || true)"

# 5. Vercel: cleanUrls rompe todas las rutas de Angular (defecto 59)
guarda "sin cleanUrls en vercel.json" "$(git grep -nI 'cleanUrls' -- 'Ec-frontend/vercel.json' || true)"

if (( fallos > 0 )); then
  echo "$fallos guarda(s) incumplida(s)."
  exit 1
fi
echo "Todas las guardas en verde."
