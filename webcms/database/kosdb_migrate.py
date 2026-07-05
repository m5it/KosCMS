"""
KosDB Migration Tools

Migrate data from PostgreSQL/MySQL to KosDB.
Backup and restore functionality.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator
from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker


class KosDBMigrator:
    """
    Migrate data from SQL databases to KosDB.
    
    Supports:
    - PostgreSQL to KosDB
    - MySQL to KosDB
    - SQLite to KosDB
    """
    
    def __init__(self, source_url: str, kosdb_client):
        self.source_url = source_url
        self.kosdb = kosdb_client
        self.source_engine = None
        self.metadata = None
    
    def connect_source(self) -> bool:
        """Connect to source database."""
        try:
            self.source_engine = create_engine(self.source_url)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.source_engine)
            return True
        except Exception as e:
            print(f"Failed to connect to source: {e}")
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of tables from source."""
        if not self.metadata:
            return []
        return [table.name for table in self.metadata.sorted_tables]
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema."""
        if not self.metadata:
            return {}
        
        table = self.metadata.tables.get(table_name)
        if not table:
            return {}
        
        columns = []
        for col in table.columns:
            col_def = f"{col.name} {self._map_type(col.type)}"
            if col.primary_key:
                col_def += " PRIMARY KEY"
            if col.index:
                col_def += " INDEX"
            columns.append(col_def)
        
        return {
            "name": table_name,
            "columns": columns
        }
    
    def _map_type(self, sql_type) -> str:
        """Map SQLAlchemy type to KosDB type."""
        type_str = str(sql_type).upper()
        
        if "INT" in type_str:
            return "INT"
        elif "FLOAT" in type_str or "DECIMAL" in type_str or "NUMERIC" in type_str:
            return "FLOAT"
        elif "BOOL" in type_str:
            return "INT"
        else:
            return "TEXT"
    
    def migrate_table(self, table_name: str, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Migrate single table to KosDB.
        
        Args:
            table_name: Name of table to migrate
            batch_size: Number of rows per batch
        
        Returns:
            Migration statistics
        """
        if not self.source_engine:
            return {"error": "Not connected to source"}
        
        table = self.metadata.tables.get(table_name)
        if not table:
            return {"error": f"Table {table_name} not found"}
        
        # Create table in KosDB
        schema = self.get_table_schema(table_name)
        columns = [col.split()[0] for col in schema["columns"]]
        
        create_result = self.kosdb.create_table(table_name, schema["columns"])
        print(f"Created table {table_name}: {create_result}")
        
        # Migrate data
        Session = sessionmaker(bind=self.source_engine)
        session = Session()
        
        total_rows = 0
        errors = 0
        
        try:
            # Query in batches
            offset = 0
            while True:
                rows = session.query(table).limit(batch_size).offset(offset).all()
                
                if not rows:
                    break
                
                for row in rows:
                    try:
                        values = []
                        for col in columns:
                            val = getattr(row, col, None)
                            if val is None:
                                values.append("NULL")
                            else:
                                values.append(str(val))
                        
                        self.kosdb.insert(table_name, values)
                        total_rows += 1
                        
                    except Exception as e:
                        errors += 1
                        print(f"Error inserting row: {e}")
                
                offset += batch_size
                print(f"  Migrated {total_rows} rows...")
        
        finally:
            session.close()
        
        return {
            "table": table_name,
            "rows_migrated": total_rows,
            "errors": errors
        }
    
    def migrate_all(self, database_name: str = "webcms") -> Dict[str, Any]:
        """
        Migrate all tables to KosDB.
        
        Args:
            database_name: Target database name in KosDB
        
        Returns:
            Migration report
        """
        # Create database
        self.kosdb.execute(f"CREATE DATABASE {database_name}")
        self.kosdb.execute(f"USE {database_name}")
        
        tables = self.get_tables()
        results = []
        
        for table_name in tables:
            print(f"\nMigrating table: {table_name}")
            result = self.migrate_table(table_name)
            results.append(result)
        
        return {
            "database": database_name,
            "tables": len(tables),
            "results": results
        }
    
    def close(self):
        """Close connections."""
        if self.source_engine:
            self.source_engine.dispose()


class KosDBBackup:
    """Backup and restore for KosDB."""
    
    def __init__(self, kosdb_client):
        self.kosdb = kosdb_client
    
    def backup_database(self, database_name: str, backup_dir: str = "./backups") -> str:
        """
        Backup KosDB database to JSON files.
        
        Args:
            database_name: Database to backup
            backup_dir: Directory for backup files
        
        Returns:
            Path to backup file
        """
        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"kosdb_{database_name}_{timestamp}.json"
        
        # Switch to database
        self.kosdb.execute(f"USE {database_name}")
        
        # Get tables
        tables_result = self.kosdb.execute("SHOW TABLES")
        tables = [line.strip() for line in tables_result.split('\n') if line.strip()]
        
        backup_data = {
            "database": database_name,
            "timestamp": timestamp,
            "tables": {}
        }
        
        for table_name in tables:
            print(f"Backing up table: {table_name}")
            
            # Get schema
            # Note: KosDB doesn't expose schema directly, we'd need to infer from data
            
            # Get data
            result = self.kosdb.query(f"SELECT * FROM {table_name}")
            
            backup_data["tables"][table_name] = {
                "columns": result.get("columns", []),
                "rows": result.get("rows", [])
            }
        
        # Write backup file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"Backup saved to: {backup_file}")
        return str(backup_file)
    
    def restore_database(self, backup_file: str, database_name: Optional[str] = None) -> bool:
        """
        Restore KosDB database from backup.
        
        Args:
            backup_file: Path to backup JSON file
            database_name: Optional new database name
        
        Returns:
            True if successful
        """
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        db_name = database_name or backup_data["database"]
        
        # Create database
        self.kosdb.execute(f"CREATE DATABASE {db_name}")
        self.kosdb.execute(f"USE {db_name}")
        
        # Restore tables
        for table_name, table_data in backup_data["tables"].items():
            print(f"Restoring table: {table_name}")
            
            columns = table_data["columns"]
            
            # Create table
            col_defs = [f"{col} TEXT" for col in columns]
            self.kosdb.create_table(table_name, col_defs)
            
            # Insert data
            for row in table_data["rows"]:
                self.kosdb.insert(table_name, row)
        
        print(f"Database {db_name} restored successfully")
        return True
    
    def list_backups(self, backup_dir: str = "./backups") -> List[Dict[str, Any]]:
        """List available backups."""
        backup_path = Path(backup_dir)
        
        if not backup_path.exists():
            return []
        
        backups = []
        for file in backup_path.glob("kosdb_*.json"):
            stat = file.stat()
            backups.append({
                "file": str(file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)


class KosDBValidator:
    """Validate KosDB data integrity."""
    
    def __init__(self, kosdb_client):
        self.kosdb = kosdb_client
    
    def validate_database(self, database_name: str) -> Dict[str, Any]:
        """
        Validate database integrity.
        
        Args:
            database_name: Database to validate
        
        Returns:
            Validation report
        """
        self.kosdb.execute(f"USE {database_name}")
        
        tables_result = self.kosdb.execute("SHOW TABLES")
        tables = [line.strip() for line in tables_result.split('\n') if line.strip()]
        
        report = {
            "database": database_name,
            "tables_checked": 0,
            "errors": [],
            "warnings": []
        }
        
        for table_name in tables:
            print(f"Validating table: {table_name}")
            report["tables_checked"] += 1
            
            # Check if table is accessible
            result = self.kosdb.query(f"SELECT COUNT(*) FROM {table_name}")
            
            if "error" in result:
                report["errors"].append({
                    "table": table_name,
                    "error": result["error"]
                })
            else:
                row_count = result.get("count", 0)
                if row_count == 0:
                    report["warnings"].append({
                        "table": table_name,
                        "warning": "Empty table"
                    })
        
        return report
    
    def check_consistency(self, table_name: str, primary_key: str = "id") -> Dict[str, Any]:
        """Check table consistency."""
        result = self.kosdb.query(f"SELECT {primary_key} FROM {table_name}")
        
        ids = [row[0] for row in result.get("rows", [])]
        duplicates = len(ids) - len(set(ids))
        
        return {
            "table": table_name,
            "total_rows": len(ids),
            "duplicates": duplicates,
            "is_consistent": duplicates == 0
        }


def create_migration_script(source_type: str, source_url: str, target_config: Dict) -> str:
    """
    Generate migration script.
    
    Args:
        source_type: postgresql, mysql, sqlite
        source_url: Database connection URL
        target_config: KosDB connection config
    
    Returns:
        Python script as string
    """
    script = f'''#!/usr/bin/env python3
"""
Auto-generated KosDB migration script

Source: {source_type}
Target: KosDB
"""

from webcms.database.kosdb_client import KosDBClient, KosDBConfig
from webcms.database.kosdb_migrate import KosDBMigrator

def migrate():
    # Source database
    source_url = "{source_url}"
    
    # Target KosDB
    config = KosDBConfig(
        host="{target_config.get('host', 'localhost')}",
        port={target_config.get('port', 9999)},
        username="{target_config.get('username', '')}",
        password="{target_config.get('password', '')}",
        database="{target_config.get('database', 'webcms')}"
    )
    
    # Connect
    kosdb = KosDBClient(config)
    migrator = KosDBMigrator(source_url, kosdb)
    
    if not migrator.connect_source():
        print("Failed to connect to source")
        return
    
    # Migrate
    report = migrator.migrate_all()
    
    print("\\nMigration complete!")
    print(f"Tables: {{report['tables']}}")
    for result in report['results']:
        print(f"  {{result['table']}}: {{result['rows_migrated']}} rows")
    
    migrator.close()
    kosdb.close()

if __name__ == "__main__":
    migrate()
'''
    return script