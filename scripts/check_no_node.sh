#!/usr/bin/env bash
set -euo pipefail

PROHIBITED_PATTERNS=(
  "package.json"
  "package-lock.json"
  "yarn.lock"
  "pnpm-lock.yaml"
  "bun.lockb"
  "node_modules"
  "webpack.config.*"
  "vite.config.*"
  "tsconfig.json"
)

FOUND=0
echo "[Stack Guard] Verificando política Zero Node/NPM..."

for pattern in "${PROHIBITED_PATTERNS[@]}"; do
  matches=$(find . -name "$pattern" -print 2>/dev/null || true)
  if [ -n "$matches" ]; then
    echo "[ERRO] Artefato proibido encontrado: $matches" >&2
    FOUND=1
  fi
done

ts_matches=$(find . \( -name "*.ts" -o -name "*.tsx" \) -print 2>/dev/null || true)
if [ -n "$ts_matches" ]; then
  echo "[ERRO] TypeScript proibido encontrado: $ts_matches" >&2
  FOUND=1
fi

if [ "$FOUND" -ne 0 ]; then
  echo "Node.js, NPM, bundlers e TypeScript são proibidos nesta mini-versão." >&2
  exit 1
fi

echo "[Stack Guard OK] Nenhum artefato Node/NPM/TypeScript detectado."
