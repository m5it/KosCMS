"""
KosDB SQLAlchemy Dialect

SQLAlchemy dialect adapter for KosDB LevelDB socket server.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import types as sqltypes
from sqlalchemy.engine import default
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql import compiler
from sqlalchemy.sql import expression as sql_expression

from .kosdb_client import KosDBClient, KosDBConfig


class KosDBTypeCompiler(compiler.GenericTypeCompiler):
    """KosDB type compiler."""
    
    def visit_INTEGER(self, type_, **kw):
        return "INT"
    
    def visit_BIGINT(self, type_, **kw):
        return "INT"
    
    def visit_SMALLINT(self, type_, **kw):
        return "INT"
    
    def visit_VARCHAR(self, type_, **kw):
        return "TEXT"
    
    def visit_TEXT(self, type_, **kw):
        return "TEXT"
    
    def visit_BOOLEAN(self, type_, **kw):
        return "INT"
    
    def visit_DATETIME(self, type_, **kw):
        return "TEXT"
    
    def visit_DATE(self, type_, **kw):
        return "TEXT"
    
    def visit_FLOAT(self, type_, **kw):
        return "FLOAT"
    
    def visit_DECIMAL(self, type_, **kw):
        return "FLOAT"
    
    def visit_BLOB(self, type_, **kw):
        return "TEXT"


class KosDBCompiler(compiler.SQLCompiler):
    """KosDB SQL compiler."""
    
    def visit_select(self, select, **kw):
        """Compile SELECT statement."""
        if select._distinct:
            text = "SELECT DISTINCT "
        else:
            text = "SELECT "
        
        text += self._generate_select_columns(select, **kw)
        text += self._generate_select_from(select, **kw)
        text += self._generate_select_where(select, **kw)
        text += self._generate_select_orderby(select, **kw)
        
        if select._limit_clause is not None:
            text += " LIMIT " + self.process(select._limit_clause, **kw)
        
        return text
    
    def _generate_select_columns(self, select, **kw):
        if select._raw_columns:
            return ", ".join(self.process(c, **kw) for c in select._raw_columns)
        return "*"
    
    def _generate_select_from(self, select, **kw):
        froms = select._from_obj
        if froms:
            return " FROM " + ", ".join(self.process(f, **kw) for f in froms)
        return ""
    
    def _generate_select_where(self, select, **kw):
        if select._whereclause is not None:
            return " WHERE " + self.process(select._whereclause, **kw)
        return ""
    
    def _generate_select_orderby(self, select, **kw):
        if select._order_by_clause.clauses:
            text = " ORDER BY "
            text += ", ".join(self.process(c, **kw) for c in select._order_by_clause.clauses)
            return text
        return ""
    
    def visit_insert(self, insert_stmt, **kw):
        table = self.process(insert_stmt.table, **kw)
        values = insert_stmt.parameters
        
        if values:
            if isinstance(values, dict):
                vals = [str(v) for v in values.values()]
            else:
                vals = [str(v) for v in values]
            return f"INSERT INTO {table} VALUES ({', '.join(vals)})"
        
        return f"INSERT INTO {table} VALUES ()"
    
    def visit_update(self, update_stmt, **kw):
        table = self.process(update_stmt.table, **kw)
        set_values = []
        for k, v in update_stmt.parameters.items():
            set_values.append(f"{k}={self._escape_value(v)}")
        
        text = f"UPDATE {table} SET {', '.join(set_values)}"
        
        if update_stmt._whereclause is not None:
            text += " WHERE " + self.process(update_stmt._whereclause, **kw)
        
        return text
    
    def visit_delete(self, delete_stmt, **kw):
        table = self.process(delete_stmt.table, **kw)
        text = f"DELETE FROM {table}"
        
        if delete_stmt._whereclause is not None:
            text += " WHERE " + self.process(delete_stmt._whereclause, **kw)
        
        return text
    
    def visit_create_table(self, create, **kw):
        table = self.process(create.element, **kw)
        columns = []
        for column in create.element.columns:
            col_def = self._format_column(column)
            columns.append(col_def)
        return f"CREATE TABLE {table} ({', '.join(columns)})"
    
    def visit_drop_table(self, drop, **kw):
        table = self.process(drop.element, **kw)
        return f"DROP TABLE {table}"
    
    def _format_column(self, column):
        name = column.name
        col_type = self.process(column.type)
        parts = [name, col_type]
        
        if column.primary_key:
            parts.append("PRIMARY KEY")
        if column.index:
            parts.append("INDEX")
        
        return " ".join(parts)
    
    def _escape_value(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)
    
    def visit_column(self, column, **kw):
        if column.table is not None:
            return f"{column.table.name}.{column.name}"
        return column.name
    
    def visit_table(self, table, **kw):
        return table.name
    
    def visit_binary(self, binary, **kw):
        left = self.process(binary.left, **kw)
        right = self.process(binary.right, **kw)
        op = binary.operator.__name__
        
        op_map = {
            'eq': '=',
            'ne': '!=',
            'lt': '<',
            'le': '<=',
            'gt': '>',
            'ge': '>=',
            'like': 'LIKE',
            'ilike': 'LIKE',
            'in_op': 'IN',
            'notin_op': 'NOT IN',
            'is_': 'IS',
            'isnot': 'IS NOT'
        }
        
        sql_op = op_map.get(op, op)
        return f"{left} {sql_op} {right}"
    
    def visit_and_(self, clause, **kw):
        return " AND ".join(self.process(c, **kw) for c in clause.clauses)
    
    def visit_or_(self, clause, **kw):
        return " OR ".join(self.process(c, **kw) for c in clause.clauses)
    
    def visit_unary_expression(self, unary, **kw):
        if unary.operator.__name__ == 'inv':
            return f"NOT {self.process(unary.element, **kw)}"
        return self.process(unary.element, **kw)


class KosDBExecutionContext(default.DefaultExecutionContext):
    def __init__(self, dialect, compiled, parameters):
        super().__init__(dialect, compiled, parameters)
        self._result = None
    
    def _execute_scalar(self, stmt, parameters, **kw):
        return self._execute_raw(stmt, parameters)
    
    def _execute_raw(self, stmt, parameters):
        sql = str(stmt)
        
        if parameters:
            for key, value in parameters.items():
                placeholder = f":{key}"
                sql = sql.replace(placeholder, self._escape_value(value))
        
        client = self.dialect._get_client()
        result = client.execute(sql)
        return result
    
    def _escape_value(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)
    
    def get_result_proxy(self):
        return KosDBResultProxy(self)


class KosDBResultProxy:
    def __init__(self, context):
        self.context = context
        self._rows = []
        self._keys = []
        self._index = 0
        self._fetch_result()
    
    def _fetch_result(self):
        result = self.context._result
        
        if isinstance(result, str):
            parsed = self._parse_response(result)
            self._keys = parsed.get("columns", [])
            self._rows = parsed.get("rows", [])
    
    def _parse_response(self, response: str) -> Dict:
        lines = response.split('\n')
        columns = []
        rows = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('+') and line.endswith('+'):
                in_table = not in_table
                continue
            
            if in_table and line.startswith('|'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                
                if not columns:
                    columns = cells
                else:
                    row = tuple(cells[i] if i < len(cells) else None 
                               for i in range(len(columns)))
                    rows.append(row)
        
        return {"columns": columns, "rows": rows}
    
    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None
    
    def fetchall(self):
        rows = self._rows[self._index:]
        self._index = len(self._rows)
        return rows
    
    def fetchmany(self, size=None):
        size = size or 1
        rows = self._rows[self._index:self._index + size]
        self._index += len(rows)
        return rows
    
    def close(self):
        pass
    
    @property
    def keys(self):
        return self._keys
    
    def __iter__(self):
        return iter(self._rows)


class KosDBDialect(default.DefaultDialect):
    name = 'kosdb'
    driver = 'kosdb'
    
    supports_alter = False
    supports_unicode = True
    supports_unicode_statements = True
    supports_sane_rowcount = False
    supports_sane_multi_rowcount = False
    supports_default_values = False
    supports_sequences = False
    supports_native_enum = False
    supports_native_boolean = False
    supports_native_decimal = False
    
    statement_compiler = KosDBCompiler
    type_compiler = KosDBTypeCompiler
    execution_ctx_cls = KosDBExecutionContext
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = None
        self._config = None
    
    def _get_client(self):
        if self._client is None:
            self._client = KosDBClient(self._config)
        return self._client
    
    def connect(self, *cargs, **cparams):
        url = cparams.get('url') or cargs[0] if cargs else None
        
        if url:
            self._config = self._parse_url(str(url))
        else:
            self._config = KosDBConfig(
                host=cparams.get('host', 'localhost'),
                port=cparams.get('port', 9999),
                username=cparams.get('username', ''),
                password=cparams.get('password', ''),
                database=cparams.get('database', 'default')
            )
        
        return KosDBConnection(self._config)
    
    def _parse_url(self, url: str) -> KosDBConfig:
        pattern = r'kosdb://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)'
        match = re.match(pattern, url)
        
        if match:
            return KosDBConfig(
                username=match.group(1),
                password=match.group(2),
                host=match.group(3),
                port=int(match.group(4)),
                database=match.group(5)
            )
        
        if ':' in url:
            host, port = url.rsplit(':', 1)
            return KosDBConfig(host=host, port=int(port))
        
        return KosDBConfig(host=url)
    
    def create_connect_args(self, url):
        return ([], {'url': str(url)})
    
    def do_execute(self, cursor, statement, parameters, context=None):
        client = self._get_client()
        sql = statement
        
        if parameters:
            for key, value in parameters.items():
                placeholder = f":{key}"
                sql = sql.replace(placeholder, self._escape_value(value))
        
        result = client.execute(sql)
        
        if context:
            context._result = result
    
    def _escape_value(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)
    
    def do_begin(self, connection):
        pass
    
    def do_rollback(self, connection):
        pass
    
    def do_commit(self, connection):
        pass
    
    def has_table(self, connection, table_name, schema=None):
        client = self._get_client()
        result = client.execute("SHOW TABLES")
        return table_name in result
    
    def get_table_names(self, connection, schema=None, **kw):
        client = self._get_client()
        result = client.execute("SHOW TABLES")
        return [line.strip() for line in result.split('\n') if line.strip()]
    
    def get_columns(self, connection, table_name, schema=None, **kw):
        return []
    
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        return {'constrained_columns': [], 'name': None}
    
    def get_foreign_keys(self, connection, table_name, schema=None, **kw):
        return []
    
    def get_indexes(self, connection, table_name, schema=None, **kw):
        return []
    
    def get_view_names(self, connection, schema=None, **kw):
        return []
    
    def get_view_definition(self, connection, view_name, schema=None, **kw):
        return None


from sqlalchemy.dialects import registry
registry.register("kosdb", "webcms.database.kosdb_dialect", "KosDBDialect")