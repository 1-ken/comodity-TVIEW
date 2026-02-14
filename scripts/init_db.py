#!/usr/bin/env python3
"""
Initialize PostgreSQL database for commodities application.
Creates all necessary tables and indexes.

Usage: python init_db.py
"""
import logging
import os
import sys

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
# Ensure project root is on sys.path so `import app` works when running
# this script from the `scripts/` directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.database import init_db, test_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    print("\n" + "=" * 60)
    print("PostgreSQL Database Initialization")
    print("=" * 60 + "\n")

    # Test connection
    print("Testing database connection...")
    if not test_connection():
        print("\n✗ ERROR: Cannot connect to PostgreSQL database")
        print("\nMake sure:")
        print("1. PostgreSQL is running on your machine")
        print("2. Database credentials in .env are correct")
        print("3. DATABASE_URL is set properly (e.g., postgresql://postgres:postgres@localhost:5432/commodities)")
        sys.exit(1)

    # Initialize database
    print("\nInitializing database tables...")
    try:
        init_db()
        print("\n✓ Database initialized successfully!")
        print("\nTables created:")
        print("  - alerts")
        print("  - price_history")
        print("  - candles")
        print("\n" + "=" * 60)
        print("Database is ready for use!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
