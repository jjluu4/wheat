#!/bin/bash
# Run two nodes for manual cross-node testing.
# Usage: ./run_two_nodes.sh
#
# Run in two terminals:
#   Terminal 1: cd wheat && source ../venv/bin/activate && DJANGO_DB_NAME=db_node_8000.sqlite3 python manage.py runserver 127.0.0.1:8002
#   Terminal 2: cd wheat && source ../venv/bin/activate && python manage.py runserver 127.0.0.1:8001
#
# Setup (one-time): Add RemoteNodes with matching credentials. See CROSS_NODE_TEST_RESULTS.md

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || { python3 -m venv venv; source venv/bin/activate; }
pip install -q -r requirements.txt
cd wheat
python manage.py migrate --no-input 2>/dev/null || true
DJANGO_DB_NAME=db_node_8000.sqlite3 python manage.py migrate --no-input 2>/dev/null || true
echo "Ready. Start nodes as shown in script header."
