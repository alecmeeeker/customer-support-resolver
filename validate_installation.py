#!/usr/bin/env python3
"""
Installation Validation Script
Validates that the email pipeline is properly set up and ready to run
"""
import sys
import os
import json
from pathlib import Path


def test_python_version():
    """Test Python version compatibility"""
    print("Checking Python version...")
    version = sys.version_info
    if version < (3, 7):
        print(f"  Python {version.major}.{version.minor} detected. Python 3.7+ required.")
        return False
    print(f"  Python {version.major}.{version.minor}.{version.micro} (compatible)")
    return True


def test_required_packages():
    """Test that all required packages are installed"""
    print("\nChecking required packages...")

    required_packages = [
        'cryptography',
        'aiohttp',
        'google.oauth2',
        'googleapiclient',
        'sqlite3',
        'lancedb',
        'sentence_transformers',
        'python_dotenv'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if '.' in package:
                parent = package.split('.')[0]
                __import__(parent)
            else:
                __import__(package)
            print(f"  {package} - OK")
        except ImportError:
            print(f"  {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n  Missing packages: {missing_packages}")
        print("  Run: pip install -r requirements.txt")
        return False

    return True


def test_oauth_configuration():
    """Test OAuth configuration"""
    print("\nChecking OAuth configuration...")

    config_path = Path.home() / '.email-pipeline' / 'config' / 'oauth_config.json'

    if not config_path.exists():
        print("  OAuth configuration not found")
        print("  Run: python setup_oauth.py")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        required_keys = ['client_id', 'client_secret', 'redirect_uri', 'encryption_key', 'scopes']
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            print(f"  OAuth config missing keys: {missing_keys}")
            return False

        print("  OAuth configuration found and valid")
        return True

    except json.JSONDecodeError:
        print("  OAuth configuration file is corrupted")
        return False
    except Exception as e:
        print(f"  Error reading OAuth configuration: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\nChecking database...")

    try:
        from config.database import get_connection, get_vector_db, DATA_DIR

        db_path = os.path.join(DATA_DIR, 'limrose.db')

        if not os.path.exists(db_path):
            print(f"  Database file not found at {db_path}")
            print("  Run: python scripts/setup_all_tables.py")
            return False

        # Test SQLite connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT sqlite_version()")
        version = cur.fetchone()[0]
        print(f"  SQLite version: {version}")

        # Check tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall() if row[0] != 'sqlite_sequence']
        print(f"  SQLite tables: {len(tables)}")

        if 'classified_emails' not in tables:
            print("  classified_emails table not found")
            print("  Run: python scripts/setup_all_tables.py")
            conn.close()
            return False

        conn.close()

        # Test LanceDB
        vector_path = os.path.join(DATA_DIR, 'vectors')
        if not os.path.exists(vector_path):
            print(f"  LanceDB directory not found at {vector_path}")
            print("  Run: python scripts/setup_all_tables.py")
            return False

        vector_db = get_vector_db()
        lance_tables = vector_db.table_names()
        print(f"  LanceDB tables: {len(lance_tables)} ({', '.join(lance_tables)})")

        print("  Database setup verified")
        return True

    except Exception as e:
        print(f"  Database error: {e}")
        return False


def test_llm_configuration():
    """Test LLM API configuration"""
    print("\nChecking LLM configuration...")

    # Load env if available
    env_path = Path('.env')
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv()

    api_key = os.getenv('LLM_API_KEY')
    provider = os.getenv('LLM_PROVIDER', 'GEMINI')

    if not api_key:
        print("  LLM_API_KEY not set in .env")
        print("  Get API key from: https://makersuite.google.com/app/apikey")
        return False

    if api_key.startswith('your-') or 'placeholder' in api_key.lower():
        print("  LLM_API_KEY appears to be a placeholder")
        return False

    print(f"  LLM configured ({provider})")
    return True


def test_environment_file():
    """Test .env file exists and is properly configured"""
    print("\nChecking .env file...")

    env_path = Path('.env')
    if not env_path.exists():
        print("  .env file not found")
        print("  Copy .env.example to .env and configure it")
        return False

    print("  .env file exists")

    from dotenv import load_dotenv
    load_dotenv()

    critical_vars = ['LLM_API_KEY']
    missing_vars = [v for v in critical_vars if not os.getenv(v)]

    if missing_vars:
        print(f"  Missing environment variables: {missing_vars}")
        return False

    return True


def main():
    """Run all validation tests"""
    print("Email Pipeline Installation Validation")
    print("=" * 50)

    tests = [
        ("Python Version", test_python_version),
        ("Required Packages", test_required_packages),
        ("Environment File", test_environment_file),
        ("OAuth Configuration", test_oauth_configuration),
        ("Database", test_database_connection),
        ("LLM Configuration", test_llm_configuration),
    ]

    passed = 0
    total = len(tests)
    issues = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * (30 - len(test_name))}")
        try:
            if test_func():
                passed += 1
            else:
                issues.append(test_name)
        except Exception as e:
            print(f"  {test_name} failed with error: {e}")
            issues.append(test_name)

    print(f"\n{'=' * 50}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 50}")
    print(f"\nPassed: {passed}/{total} tests")

    if passed == total:
        print("\nAll validations passed! The email pipeline is ready to use.")
        print("\nNext steps:")
        print("   1. Run: python gmail_oauth_extractor.py --test")
        print("   2. If test works, run: ./update_emails_v2.sh")
        return True
    else:
        print(f"\nFailed tests: {issues}")
        print("\nPlease fix the issues above before proceeding.")
        print("See README.md for setup instructions.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
