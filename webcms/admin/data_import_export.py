"""
Data Import/Export Module

Provides functionality to import and export data in various formats
"""

import json
import csv
import io
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, BinaryIO
from dataclasses import dataclass, asdict


class DataFormat:
    """Supported data formats."""
    JSON = 'json'
    CSV = 'csv'
    XML = 'xml'
    YAML = 'yaml'


@dataclass
class ImportResult:
    """Result of import operation."""
    success: bool
    imported: int
    failed: int
    errors: List[Dict]
    warnings: List[str]


@dataclass
class ExportResult:
    """Result of export operation."""
    success: bool
    data: bytes
    format: str
    record_count: int
    filename: str


class DataExporter:
    """Export data to various formats."""
    
    def __init__(self):
        self.exporters = {
            DataFormat.JSON: self._export_json,
            DataFormat.CSV: self._export_csv,
            DataFormat.XML: self._export_xml,
        }
    
    def export(self, data: List[Dict], format: str, filename: Optional[str] = None) -> ExportResult:
        """
        Export data to specified format.
        
        Args:
            data: List of dictionaries to export
            format: Export format (json, csv, xml)
            filename: Optional filename (auto-generated if not provided)
        
        Returns:
            ExportResult with exported data
        """
        if format not in self.exporters:
            return ExportResult(
                success=False,
                data=b'',
                format=format,
                record_count=0,
                filename=''
            )
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'export_{timestamp}.{format}'
        
        try:
            exporter = self.exporters[format]
            exported_data = exporter(data)
            
            return ExportResult(
                success=True,
                data=exported_data,
                format=format,
                record_count=len(data),
                filename=filename
            )
        except Exception as e:
            return ExportResult(
                success=False,
                data=str(e).encode(),
                format=format,
                record_count=0,
                filename=filename
            )
    
    def _export_json(self, data: List[Dict]) -> bytes:
        """Export to JSON."""
        return json.dumps(data, indent=2, default=str).encode('utf-8')
    
    def _export_csv(self, data: List[Dict]) -> bytes:
        """Export to CSV."""
        if not data:
            return b''
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8')
    
    def _export_xml(self, data: List[Dict]) -> bytes:
        """Export to XML."""
        root = ET.Element('records')
        
        for item in data:
            record = ET.SubElement(root, 'record')
            for key, value in item.items():
                field = ET.SubElement(record, str(key))
                field.text = str(value) if value is not None else ''
        
        # Pretty print
        self._indent_xml(root)
        
        return ET.tostring(root, encoding='utf-8', method='xml')
    
    def _indent_xml(self, elem, level=0):
        """Add indentation to XML."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class DataImporter:
    """Import data from various formats."""
    
    def __init__(self):
        self.importers = {
            DataFormat.JSON: self._import_json,
            DataFormat.CSV: self._import_csv,
            DataFormat.XML: self._import_xml,
        }
        self.validators = {}
    
    def register_validator(self, entity_type: str, validator: Callable):
        """Register a validator for entity type."""
        self.validators[entity_type] = validator
    
    def import_data(self, data: bytes, format: str, entity_type: str,
                    transformer: Optional[Callable] = None) -> ImportResult:
        """
        Import data from specified format.
        
        Args:
            data: Raw data to import
            format: Import format (json, csv, xml)
            entity_type: Type of entity being imported
            transformer: Optional function to transform records
        
        Returns:
            ImportResult with import statistics
        """
        if format not in self.importers:
            return ImportResult(
                success=False,
                imported=0,
                failed=0,
                errors=[{'message': f'Unsupported format: {format}'}],
                warnings=[]
            )
        
        try:
            importer = self.importers[format]
            records = importer(data)
        except Exception as e:
            return ImportResult(
                success=False,
                imported=0,
                failed=0,
                errors=[{'message': f'Parse error: {str(e)}'}],
                warnings=[]
            )
        
        imported = 0
        failed = 0
        errors = []
        warnings = []
        
        validator = self.validators.get(entity_type)
        
        for i, record in enumerate(records):
            try:
                # Transform if needed
                if transformer:
                    record = transformer(record)
                
                # Validate if validator exists
                if validator:
                    is_valid, error = validator(record)
                    if not is_valid:
                        failed += 1
                        errors.append({
                            'row': i + 1,
                            'message': error,
                            'record': record
                        })
                        continue
                
                imported += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'row': i + 1,
                    'message': str(e),
                    'record': record
                })
        
        return ImportResult(
            success=failed == 0,
            imported=imported,
            failed=failed,
            errors=errors,
            warnings=warnings
        )
    
    def _import_json(self, data: bytes) -> List[Dict]:
        """Import from JSON."""
        content = data.decode('utf-8')
        parsed = json.loads(content)
        
        # Handle both single object and array
        if isinstance(parsed, dict):
            return [parsed]
        return parsed
    
    def _import_csv(self, data: bytes) -> List[Dict]:
        """Import from CSV."""
        content = data.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    
    def _import_xml(self, data: bytes) -> List[Dict]:
        """Import from XML."""
        root = ET.fromstring(data)
        records = []
        
        for record in root.findall('record'):
            item = {}
            for field in record:
                item[field.tag] = field.text
            records.append(item)
        
        return records


class BulkOperations:
    """Bulk operations for data management."""
    
    def __init__(self, db=None):
        self.db = db
    
    def _escape_sql(self, value: Any) -> str:
        """Escape SQL string value."""
        if value is None:
            return 'NULL'
        s = str(value)
        s = s.replace("'", "''")
        return f"'{s}'"
    
    def bulk_insert(self, table: str, records: List[Dict]) -> ImportResult:
        """
        Bulk insert records into database.
        
        Args:
            table: Table name
            records: Records to insert
        
        Returns:
            ImportResult with operation statistics
        """
        if not self.db:
            return ImportResult(
                success=False,
                imported=0,
                failed=len(records),
                errors=[{'message': 'No database connection'}],
                warnings=[]
            )
        
        imported = 0
        failed = 0
        errors = []
        
        for i, record in enumerate(records):
            try:
                columns = ', '.join(record.keys())
                values = ', '.join([self._escape_sql(v) for v in record.values()])
                
                sql = f"INSERT INTO {table} ({columns}) VALUES ({values})"
                self.db.execute(sql)
                imported += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'row': i + 1,
                    'message': str(e),
                    'record': record
                })
        
        return ImportResult(
            success=failed == 0,
            imported=imported,
            failed=failed,
            errors=errors,
            warnings=[]
        )
    
    def bulk_update(self, table: str, records: List[Dict], key_field: str) -> ImportResult:
        """
        Bulk update records in database.
        
        Args:
            table: Table name
            records: Records to update
            key_field: Field to use as key for matching
        
        Returns:
            ImportResult with operation statistics
        """
        if not self.db:
            return ImportResult(
                success=False,
                imported=0,
                failed=len(records),
                errors=[{'message': 'No database connection'}],
                warnings=[]
            )
        
        imported = 0
        failed = 0
        errors = []
        
        for i, record in enumerate(records):
            try:
                if key_field not in record:
                    failed += 1
                    errors.append({
                        'row': i + 1,
                        'message': f'Missing key field: {key_field}',
                        'record': record
                    })
                    continue
                
                key_value = record.pop(key_field)
                sets = ', '.join([f"{k}={self._escape_sql(v)}" for k, v in record.items()])
                
                sql = f"UPDATE {table} SET {sets} WHERE {key_field}={self._escape_sql(key_value)}"
                self.db.execute(sql)
                imported += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    'row': i + 1,
                    'message': str(e),
                    'record': record
                })
        
        return ImportResult(
            success=failed == 0,
            imported=imported,
            failed=failed,
            errors=errors,
            warnings=[]
        )
    
    def bulk_delete(self, table: str, ids: List[str], id_field: str = 'id') -> Dict:
        """
        Bulk delete records from database.
        
        Args:
            table: Table name
            ids: IDs to delete
            id_field: ID field name
        
        Returns:
            Dict with operation results
        """
        if not self.db:
            return {'success': False, 'deleted': 0, 'error': 'No database connection'}
        
        try:
            id_list = ', '.join([self._escape_sql(id) for id in ids])
            sql = f"DELETE FROM {table} WHERE {id_field} IN ({id_list})"
            self.db.execute(sql)
            
            return {
                'success': True,
                'deleted': len(ids),
                'table': table
            }
            
        except Exception as e:
            return {
                'success': False,
                'deleted': 0,
                'error': str(e)
            }


# Global instances
exporter = DataExporter()
importer = DataImporter()


def export_users(users: List[Dict], format: str = DataFormat.JSON) -> ExportResult:
    """Export users to specified format."""
    return exporter.export(users, format, f'users_export.{format}')


def export_content(content: List[Dict], format: str = DataFormat.JSON) -> ExportResult:
    """Export content to specified format."""
    return exporter.export(content, format, f'content_export.{format}')


def import_users(data: bytes, format: str = DataFormat.JSON) -> ImportResult:
    """Import users from specified format."""
    return importer.import_data(data, format, 'user')


def import_content(data: bytes, format: str = DataFormat.JSON) -> ImportResult:
    """Import content from specified format."""
    return importer.import_data(data, format, 'content')


# Export
__all__ = [
    'DataFormat',
    'DataExporter',
    'DataImporter',
    'BulkOperations',
    'ImportResult',
    'ExportResult',
    'exporter',
    'importer',
    'export_users',
    'export_content',
    'import_users',
    'import_content'
]
