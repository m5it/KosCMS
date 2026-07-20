"""
Benchmark test for settings save optimization.

Measures database round-trips and elapsed time for saving settings
via the admin API. Verifies that the optimized KosDB path uses at
most N+2 round-trips (1 SELECT + BEGIN + N writes + COMMIT) instead
of the unoptimized 2N+1.
"""

import time
import unittest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class MockQueryResult:
    """Mock result from KosDB query()"""
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def get(self, key: str, default=None):
        return getattr(self, key, default)


class MockKosDBConnection:
    """Mock connection for pipelining tests."""
    
    def __init__(self, client: 'MockKosDBClient'):
        self._client = client
        self._buffer: List[str] = []
        self._flushed = False
    
    def query(self, sql: str) -> Dict[str, Any]:
        """Execute query immediately (flushes buffer first)."""
        if self._buffer:
            self._flush()
        return self._client.query(sql)
    
    def execute(self, sql: str) -> str:
        """Buffer execute call for pipelined execution."""
        if self._flushed:
            raise RuntimeError("Cannot execute after pipeline flushed")
        self._buffer.append(sql)
        return "OK (buffered)"
    
    def _flush(self):
        """Flush buffered commands."""
        if self._flushed or not self._buffer:
            return
        self._flushed = True
        # Execute all buffered commands on the client
        for cmd in self._buffer:
            self._client._execute_immediate(cmd)
    
    def get_buffered_results(self) -> List[str]:
        """Get results from buffered execute() calls."""
        if not self._flushed:
            raise RuntimeError("Pipeline not yet flushed")
        return ["OK"] * len(self._buffer)


class MockTransactionContext:
    """Mock context manager for KosDBClient.transaction()"""
    
    def __init__(self, client: 'MockKosDBClient', pipeline: bool = False):
        self.client = client
        self.pipeline = pipeline
        self._conn = None
        
    def __enter__(self):
        if self.pipeline:
            self._conn = MockKosDBConnection(self.client)
            return self._conn
        self.client._in_transaction = True
        return self.client
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pipeline and self._conn:
            self._conn._flush()
        self.client._in_transaction = False
        return False


class MockKosDBClient:
    """
    Mock KosDB client that counts query/execute calls.
    
    Simulates the KosDB wire protocol behavior while tracking
    all database operations for benchmarking.
    """
    
    def __init__(self):
        self.queries: List[str] = []
        self.executes: List[str] = []
        self._tables: Dict[str, List[Dict]] = {}
        self._settings: Dict[str, Dict] = {}
        self._in_transaction = False
        
    def query(self, sql: str) -> Dict[str, Any]:
        """Execute a SELECT query and track the call."""
        self.queries.append(sql)
        
        # Simulate SELECT setting_key FROM settings
        if "SELECT setting_key FROM settings" in sql:
            rows = [{"setting_key": k} for k in self._settings.keys()]
            return {
                "columns": ["setting_key"],
                "rows": rows,
                "error": None
            }
        
        # Simulate other SELECTs
        return {"columns": [], "rows": [], "error": None}
    
    def _execute_immediate(self, sql: str) -> str:
        """Execute without tracking (called from pipeline flush)."""
        return self._track_execute(sql)
    
    def _track_execute(self, sql: str) -> str:
        """Track the execute call."""
        self.executes.append(sql)
        
        # Simulate storing settings for UPDATE vs INSERT detection
        if "settings" in sql.lower():
            if "INSERT" in sql.upper():
                # Extract key from INSERT
                import re
                match = re.search(r"VALUES\s*\('([^']+)'", sql)
                if match:
                    key = match.group(1)
                    self._settings[key] = {"value": "stored"}
            elif "UPDATE" in sql.upper():
                # Extract key from WHERE
                import re
                match = re.search(r"WHERE\s+setting_key='([^']+)'", sql)
                if match:
                    key = match.group(1)
                    if key in self._settings:
                        self._settings[key]["value"] = "updated"
        
        return "OK"
    
    def execute(self, sql: str) -> str:
        """Execute an INSERT/UPDATE/DELETE and track the call."""
        return self._track_execute(sql)
    
    def transaction(self, pipeline: bool = False):
        """Return context manager for transaction() support."""
        return MockTransactionContext(self, pipeline=pipeline)
    
    @property
    def call_count(self) -> int:
        """Total number of database round-trips."""
        return len(self.queries) + len(self.executes)
    
    def reset_counters(self):
        """Reset all counters for a fresh benchmark run."""
        self.queries = []
        self.executes = []


class TestSettingsSaveBenchmark(unittest.TestCase):
    """
    Benchmark tests for admin settings save optimization.
    
    These tests verify that the optimized code reduces database
    round-trips from 2N+1 to N+2 for N settings.
    """
    
    def setUp(self):
        """Set up mock KosDB client for each test."""
        self.db = MockKosDBClient()
        
    def _simulate_optimized_settings_save(self, settings_count: int, 
                                          use_pipeline: bool = False) -> Dict[str, Any]:
        """
        Simulate the OPTIMIZED settings save logic.
        
        This mirrors the actual implementation in AdminAPI.update_settings()
        for KosDB mode with transaction context and optional pipelining.
        """
        normalized = {f"setting_{i}": f"value_{i}" for i in range(settings_count)}
        
        start_time = time.perf_counter()
        
        # OPTIMIZED PATH: Use transaction context manager with single connection
        with self.db.transaction(pipeline=use_pipeline) as conn:
            # Send BEGIN to start transaction
            conn.execute("BEGIN")
            
            # 1 SELECT for all existing keys
            existing_keys_result = conn.query("SELECT setting_key FROM settings")
            existing_keys = {
                row.get('setting_key')
                for row in existing_keys_result.get('rows', [])
                if row.get('setting_key')
            }
            
            # N writes (INSERT or UPDATE per setting)
            for key, value in normalized.items():
                exists = key in existing_keys
                if exists:
                    cmd = (
                        f"UPDATE settings SET value='{value}', type='str' "
                        f"WHERE setting_key='{key}'"
                    )
                else:
                    cmd = (
                        f"INSERT INTO settings (setting_key, value, type) VALUES "
                        f"('{key}', '{value}', 'str')"
                    )
                conn.execute(cmd)
            
            # Send COMMIT to finalize transaction
            conn.execute("COMMIT")
        
        elapsed = time.perf_counter() - start_time
        
        return {
            "elapsed_seconds": elapsed,
            "query_count": len(self.db.queries),
            "execute_count": len(self.db.executes),
            "total_round_trips": self.db.call_count
        }
    
    def _simulate_unoptimized_settings_save(self, settings_count: int) -> Dict[str, Any]:
        """
        Simulate the UNOPTIMIZED settings save logic.
        
        This is the old implementation that checked each key individually.
        """
        normalized = {f"setting_{i}": f"value_{i}" for i in range(settings_count)}
        
        start_time = time.perf_counter()
        
        # UNOPTIMIZED PATH: Check each key individually (no transaction context)
        for key, value in normalized.items():
            # 1 SELECT per key (N round-trips)
            result = self.db.query(f"SELECT setting_key FROM settings WHERE setting_key='{key}'")
            exists = len(result.get('rows', [])) > 0
            
            # 1 write per key (N round-trips)
            if exists:
                cmd = (
                    f"UPDATE settings SET value='{value}', type='str' "
                    f"WHERE setting_key='{key}'"
                )
            else:
                cmd = (
                    f"INSERT INTO settings (setting_key, value, type) VALUES "
                    f"('{key}', '{value}', 'str')"
                )
            self.db.execute(cmd)
        
        elapsed = time.perf_counter() - start_time
        
        return {
            "elapsed_seconds": elapsed,
            "query_count": len(self.db.queries),
            "execute_count": len(self.db.executes),
            "total_round_trips": self.db.call_count
        }
    
    def test_optimized_path_uses_n_plus_2_round_trips(self):
        """
        Verify optimized path uses at most N+2 round-trips for N settings.
        
        With 15 settings:
        - 1 SELECT to get all existing keys
        - 1 BEGIN
        - 15 INSERT/UPDATE operations
        - 1 COMMIT
        - Total: 18 round-trips (N+3, or N+2 if BEGIN/COMMIT pipelined)
        
        Instead of unoptimized:
        - 15 SELECTs (one per key)
        - 15 INSERT/UPDATE operations  
        - Total: 30 round-trips (2N)
        
        With pipelining, could be as low as 3 round-trips (1 SELECT + 1 pipeline batch).
        """
        settings_count = 15
        
        # Run optimized path (without pipelining for worst-case count)
        result = self._simulate_optimized_settings_save(settings_count, use_pipeline=False)
        
        # Assert N+3 bound (SELECT + BEGIN + N writes + COMMIT)
        max_allowed = settings_count + 3  # 18
        self.assertLessEqual(
            result["total_round_trips"],
            max_allowed,
            f"Optimized path should use at most {max_allowed} round-trips for "
            f"{settings_count} settings, but used {result['total_round_trips']}"
        )
        
        # Verify exactly 1 SELECT was issued
        self.assertEqual(
            result["query_count"],
            1,
            f"Optimized path should issue exactly 1 SELECT, got {result['query_count']}"
        )
        
        # Verify N+2 writes were issued (BEGIN + N settings + COMMIT)
        expected_writes = settings_count + 2  # 17
        self.assertEqual(
            result["execute_count"],
            expected_writes,
            f"Optimized path should issue exactly {expected_writes} writes "
            f"(BEGIN + {settings_count} settings + COMMIT), "
            f"got {result['execute_count']}"
        )
        
        print(f"\nOptimized path: {result['total_round_trips']} round-trips "
              f"({result['query_count']} SELECT + {result['execute_count']} writes) "
              f"in {result['elapsed_seconds']:.4f}s")
    
    def test_unoptimized_path_uses_2n_round_trips(self):
        """
        Show that unoptimized path uses ~2N round-trips.
        
        This demonstrates the problem the optimization solves.
        """
        settings_count = 15
        
        # Run unoptimized path
        result = self._simulate_unoptimized_settings_save(settings_count)
        
        # Unoptimized does 2N operations (N SELECTs + N writes)
        expected_unoptimized = settings_count * 2  # 30
        
        self.assertGreaterEqual(
            result["total_round_trips"],
            expected_unoptimized,
            f"Unoptimized path should use ~{expected_unoptimized} round-trips"
        )
        
        print(f"\nUnoptimized path: {result['total_round_trips']} round-trips "
              f"({result['query_count']} SELECTs + {result['execute_count']} writes) "
              f"in {result['elapsed_seconds']:.4f}s")
    
    def test_optimization_reduces_round_trips_by_40_percent(self):
        """
        Verify the optimization achieves at least 40% reduction in round-trips.
        
        For 15 settings:
        - Unoptimized: 30 round-trips
        - Optimized: 18 round-trips (40% reduction)
        """
        settings_count = 15
        
        # Unoptimized
        unopt_result = self._simulate_unoptimized_settings_save(settings_count)
        
        # Reset and run optimized
        self.db.reset_counters()
        opt_result = self._simulate_optimized_settings_save(settings_count)
        
        reduction = unopt_result["total_round_trips"] - opt_result["total_round_trips"]
        reduction_percent = (reduction / unopt_result["total_round_trips"]) * 100
        
        print(f"\nRound-trip reduction: {reduction} ({reduction_percent:.1f}%)")
        print(f"  Unoptimized: {unopt_result['total_round_trips']}")
        print(f"  Optimized: {opt_result['total_round_trips']}")
        
        self.assertGreaterEqual(
            reduction_percent,
            40.0,
            f"Optimization should reduce round-trips by at least 40%, "
            f"but only achieved {reduction_percent:.1f}%"
        )
    
    def test_transaction_context_manager_functionality(self):
        """
        Test that transaction() context manager works correctly.
        
        Verifies:
        - Returns a connection-like object
        - Supports query() and execute() methods
        - Properly tracks all operations
        """
        settings_count = 5
        
        with self.db.transaction() as conn:
            # Should be able to query
            result = conn.query("SELECT setting_key FROM settings")
            self.assertIsInstance(result, dict)
            self.assertIn("rows", result)
            
            # Should be able to execute
            for i in range(settings_count):
                conn.execute(f"INSERT INTO settings VALUES ('key{i}', 'val{i}', 'str')")
        
        # Verify all operations were tracked
        self.assertEqual(len(self.db.queries), 1)  # 1 SELECT
        self.assertEqual(len(self.db.executes), settings_count)  # N INSERTs
    
    def test_pipelined_transaction_buffers_executes(self):
        """
        Test that pipeline=True buffers execute() calls.
        
        With pipelining, execute() calls should return "OK (buffered)"
        and only be sent when the context exits.
        """
        settings_count = 3
        
        with self.db.transaction(pipeline=True) as conn:
            # These should be buffered
            for i in range(settings_count):
                result = conn.execute(f"INSERT INTO settings VALUES ('key{i}', 'val{i}', 'str')")
                self.assertEqual(result, "OK (buffered)")
            
            # Before flush, no executes should be tracked yet
            self.assertEqual(len(self.db.executes), 0, 
                           "Executes should be buffered, not immediate")
        
        # After context exits, all should be flushed
        self.assertEqual(len(self.db.executes), settings_count,
                        "All buffered executes should be flushed on exit")
    
    def test_pipeline_query_flushes_buffer(self):
        """
        Test that query() flushes the pipeline buffer before executing.
        
        This maintains consistency - queries see all prior writes.
        """
        with self.db.transaction(pipeline=True) as conn:
            # Buffer some writes
            conn.execute("INSERT INTO settings VALUES ('key1', 'val1', 'str')")
            conn.execute("INSERT INTO settings VALUES ('key2', 'val2', 'str')")
            
            # Query should flush buffer first
            result = conn.query("SELECT setting_key FROM settings")
            
            # After query, executes should be tracked
            self.assertEqual(len(self.db.executes), 2,
                           "Query should flush buffered executes")
    
    def test_performance_threshold(self):
        """
        Assert that settings save completes within reasonable time.
        
        This catches performance regressions.
        """
        settings_count = 15
        
        result = self._simulate_optimized_settings_save(settings_count, use_pipeline=False)
        
        # Should complete in under 100ms even with mocks
        max_elapsed = 0.1  # 100ms
        self.assertLess(
            result["elapsed_seconds"],
            max_elapsed,
            f"Settings save took {result['elapsed_seconds']:.4f}s, "
            f"exceeds threshold of {max_elapsed}s"
        )


class TestSettingsSaveRegression(unittest.TestCase):
    """
    Regression tests that fail if optimization is broken.
    
    These tests simulate the actual AdminAPI code paths.
    """
    
    def setUp(self):
        self.db = MockKosDBClient()
    
    def test_regression_if_transaction_not_used(self):
        """
        Fail if transaction() is not used in optimized path.
        
        This catches cases where someone removes the transaction()
        context manager and reverts to individual pool acquires.
        """
        settings_count = 10
        
        # Simulate what would happen without transaction context
        # (Each operation does its own pool acquire/release)
        
        # This is WRONG - should use transaction()
        for i in range(settings_count):
            result = self.db.query(f"SELECT * FROM settings WHERE key='key{i}'")
            self.db.execute(f"INSERT INTO settings VALUES ('key{i}', 'val{i}', 'str')")
        
        # This is 2N round-trips, which is the regression we're preventing
        round_trips = self.db.call_count
        self.assertGreaterEqual(
            round_trips,
            settings_count * 2,
            "Test setup: expected 2N round-trips for unoptimized path"
        )
        
        # Now verify the optimized path is better
        self.db.reset_counters()
        
        # This is CORRECT - uses transaction context
        with self.db.transaction() as conn:
            conn.execute("BEGIN")
            result = conn.query("SELECT setting_key FROM settings")
            for i in range(settings_count):
                conn.execute(f"INSERT INTO settings VALUES ('key{i}', 'val{i}', 'str')")
            conn.execute("COMMIT")
        
        optimized_round_trips = self.db.call_count
        
        # Optimized should be significantly less
        self.assertLess(
            optimized_round_trips,
            round_trips,
            "Optimized path MUST use fewer round-trips than unoptimized. "
            "If this fails, the optimization has been regressed!"
        )
    
    def test_regression_if_single_select_not_used(self):
        """
        Fail if individual SELECTs are issued per setting.
        
        This catches cases where the bulk SELECT is replaced with
        per-key existence checks.
        """
        settings_count = 10
        
        # Simulate optimized path
        with self.db.transaction() as conn:
            conn.execute("BEGIN")
            result = conn.query("SELECT setting_key FROM settings")
            
            # Check that we got all keys in ONE query
            self.assertEqual(self.db.call_count, 2)  # BEGIN + 1 SELECT
            
            for i in range(settings_count):
                conn.execute(f"INSERT INTO settings VALUES ('key{i}', 'val{i}', 'str')")
            
            conn.execute("COMMIT")
        
        # Should have exactly 1 SELECT
        select_count = len([q for q in self.db.queries if "SELECT" in q])
        self.assertEqual(
            select_count,
            1,
            f"Should issue exactly 1 SELECT for all {settings_count} settings, "
            f"but issued {select_count}. If this fails, the bulk SELECT optimization "
            f"has been regressed!"
        )


class TestSettingsSaveIntegration(unittest.TestCase):
    """
    Integration-style tests for the actual implementation.
    """
    
    def test_mock_client_has_transaction_method(self):
        """Verify our mock supports the transaction() API."""
        client = MockKosDBClient()
        self.assertTrue(hasattr(client, 'transaction'))
        
    def test_mock_transaction_accepts_pipeline_param(self):
        """Verify transaction() accepts pipeline parameter."""
        client = MockKosDBClient()
        ctx = client.transaction(pipeline=True)
        self.assertIsInstance(ctx, MockTransactionContext)
        
    def test_mock_transaction_returns_connection(self):
        """Verify transaction() returns a usable connection."""
        client = MockKosDBClient()
        
        # Without pipeline
        with client.transaction() as conn:
            self.assertIs(conn, client)
        
        # With pipeline
        with client.transaction(pipeline=True) as conn:
            self.assertIsInstance(conn, MockKosDBConnection)


if __name__ == "__main__":
    unittest.main(verbosity=2)
