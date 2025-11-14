#!/usr/bin/env python3
"""
Database Migration Script

This script migrates the existing database to include new columns and tables:
- Adds data_folder column to subjects table
- Adds images relationship to subjects table
- Creates patient_images table

Run this if you get "no such column" errors.
"""

import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def backup_database(db_path: Path) -> Path:
    """
    Create a backup of the database.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.

    Args:
        cursor: SQLite cursor
        table_name: Name of the table
        column_name: Name of the column

    Returns:
        True if column exists, False otherwise
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def check_table_exists(cursor, table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        cursor: SQLite cursor
        table_name: Name of the table

    Returns:
        True if table exists, False otherwise
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate_database(db_path: Path) -> bool:
    """
    Migrate the database to the new schema.

    Args:
        db_path: Path to database file

    Returns:
        True if migration was needed and successful, False if no migration needed
    """
    print(f"Checking database: {db_path}")

    if not db_path.exists():
        print("Database does not exist yet. No migration needed.")
        return False

    # Create backup
    print("\nCreating backup...")
    backup_path = backup_database(db_path)
    print(f"✓ Backup created: {backup_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migration_needed = False

    try:
        # Check if subjects.data_folder column exists
        if not check_column_exists(cursor, "subjects", "data_folder"):
            print("\nAdding 'data_folder' column to subjects table...")
            cursor.execute(
                "ALTER TABLE subjects ADD COLUMN data_folder VARCHAR(500)"
            )
            conn.commit()
            print("✓ Added data_folder column")
            migration_needed = True
        else:
            print("\n✓ subjects.data_folder column already exists")

        # Check if patient_images table exists
        if not check_table_exists(cursor, "patient_images"):
            print("\nCreating patient_images table...")
            cursor.execute("""
                CREATE TABLE patient_images (
                    image_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER NOT NULL,
                    image_type VARCHAR(50) NOT NULL,
                    vertebra_level VARCHAR(20),
                    file_path VARCHAR(500) NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    notes TEXT,
                    FOREIGN KEY(subject_id) REFERENCES subjects (subject_id)
                )
            """)

            # Create index on subject_id for faster queries
            cursor.execute(
                "CREATE INDEX ix_patient_images_subject_id ON patient_images (subject_id)"
            )

            conn.commit()
            print("✓ Created patient_images table")
            migration_needed = True
        else:
            print("\n✓ patient_images table already exists")

        # Get current table stats
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM patient_images")
        image_count = cursor.fetchone()[0]

        print(f"\nDatabase statistics:")
        print(f"  - Subjects: {subject_count}")
        print(f"  - Images: {image_count}")

        if migration_needed:
            print("\n✓ Database migration completed successfully!")
        else:
            print("\n✓ Database is already up to date. No migration needed.")

        return migration_needed

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"\nRestoring from backup: {backup_path}")
        conn.close()
        shutil.copy2(backup_path, db_path)
        print("✓ Database restored from backup")
        raise

    finally:
        conn.close()


def main():
    """Main entry point."""
    print("=" * 70)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 70)
    print()

    # Get database path
    db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"

    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        print("\nNo migration needed. The database will be created with the")
        print("correct schema when you run the application or initialization script.")
        return 0

    print("This script will update your database to include:")
    print("  • data_folder column in subjects table")
    print("  • patient_images table for image tracking")
    print()
    print(f"Database location: {db_path}")
    print()

    response = input("Do you want to continue with the migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nMigration cancelled.")
        return 0

    try:
        migrated = migrate_database(db_path)

        print("\n" + "=" * 70)
        if migrated:
            print("MIGRATION SUCCESSFUL!")
        else:
            print("DATABASE ALREADY UP TO DATE!")
        print("=" * 70)
        print()
        print("You can now run:")
        print("  python initialize_all_patients.py")
        print("  python main.py")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
