#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
echo '[inicialização] Preparando o serviço Cutover...'
python -u init_db.py
echo '[inicialização] Abrindo a porta do servidor web...'
exec gunicorn app:app --bind "0.0.0.0:${PORT:-10000}" --workers "${WEB_CONCURRENCY:-1}" --timeout 120 --graceful-timeout 30 --access-logfile - --error-logfile - --capture-output
