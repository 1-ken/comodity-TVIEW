#!/bin/bash
# Helper script to initialize PostgreSQL database as the postgres system user
# This uses peer authentication which doesn't require a password

cd /home/here/Desktop/prompts/commodities

# Run the initialization as postgres user
sudo -u postgres bash << 'EOF'
source .venv/bin/activate
python init_db.py
EOF
