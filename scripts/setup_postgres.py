#!/usr/bin/env python3
"""
Setup PostgreSQL database and user for the commodities application.
Run this if you don't have a database created yet.

Usage: python setup_postgres.py
"""
import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commodities")

def parse_db_url(url: str):
    """Parse PostgreSQL connection string."""
    # Format: postgresql://user:password@host:port/dbname
    try:
        url = url.replace("postgresql://", "")
        user_pass, host_db = url.split("@")
        user, password = user_pass.split(":")
        host_port, dbname = host_db.split("/")
        host, port = host_port.split(":") if ":" in host_port else (host_port, "5432")
        return {
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "dbname": dbname,
        }
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        return None


def main():
    """Setup PostgreSQL database."""
    print("\n" + "=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60 + "\n")

    creds = parse_db_url(DB_URL)
    if not creds:
        print("Could not parse DATABASE_URL from .env")
        print(f"Current URL: {DB_URL}")
        sys.exit(1)

    print(f"Database Configuration:")
    print(f"  Host: {creds['host']}")
    print(f"  Port: {creds['port']}")
    print(f"  User: {creds['user']}")
    print(f"  Database: {creds['dbname']}")

    # Try to create database
    print(f"\nAttempting to create database '{creds['dbname']}'...")
    
    try:
        # Create database
        cmd = [
            "psql",
            "-h", creds["host"],
            "-U", creds["user"],
            "-c", f"CREATE DATABASE {creds['dbname']};"
        ]
        
        # Set password for psql
        env = os.environ.copy()
        env["PGPASSWORD"] = creds["password"]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0 or "already exists" in result.stderr:
            print(f"✓ Database '{creds['dbname']}' is ready")
        else:
            print(f"✗ Error: {result.stderr}")
            
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Make sure PostgreSQL is running:")
        print("   sudo service postgresql start")
        print("2. Initialize the database tables:")
        print("   python init_db.py")
        print("3. Start the application:")
        print("   python run.py")
        print("=" * 60 + "\n")
        
    except FileNotFoundError:
        print("✗ Error: 'psql' command not found")
        print("\nMake sure PostgreSQL client is installed:")
        print("  Ubuntu/Debian: sudo apt-get install postgresql-client")
        print("  macOS: brew install postgresql")
        print("  Windows: Install PostgreSQL from https://www.postgresql.org/download/windows/")
        sys.exit(1)


if __name__ == "__main__":
    main()
