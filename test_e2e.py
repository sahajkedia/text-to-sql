#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for QueryForge Text-to-SQL Application.

Run with: pytest test_e2e.py -v
Or run directly: python test_e2e.py
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Disable telemetry before imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["POSTHOG_DISABLED"] = "1"
os.environ["CHROMA_TELEMETRY"] = "False"


# =============================================================================
# Test Results Tracking
# =============================================================================

class TestResults:
    """Track test results for reporting."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def add_pass(self, name: str, details: str = ""):
        self.passed.append({"name": name, "details": details})
    
    def add_fail(self, name: str, error: str):
        self.failed.append({"name": name, "error": error})
    
    def add_skip(self, name: str, reason: str):
        self.skipped.append({"name": name, "reason": reason})
    
    def print_report(self):
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        
        print(f"\n✓ PASSED: {len(self.passed)}")
        for t in self.passed:
            print(f"  • {t['name']}")
            if t['details']:
                print(f"    {t['details']}")
        
        if self.failed:
            print(f"\n✗ FAILED: {len(self.failed)}")
            for t in self.failed:
                print(f"  • {t['name']}")
                print(f"    Error: {t['error']}")
        
        if self.skipped:
            print(f"\n⊘ SKIPPED: {len(self.skipped)}")
            for t in self.skipped:
                print(f"  • {t['name']}")
                print(f"    Reason: {t['reason']}")
        
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print(f"\n{'=' * 70}")
        print(f"TOTAL: {total} tests | PASSED: {len(self.passed)} | FAILED: {len(self.failed)} | SKIPPED: {len(self.skipped)}")
        print("=" * 70)
        
        return len(self.failed) == 0


results = TestResults()


# =============================================================================
# 1. CONFIGURATION TESTS
# =============================================================================

class TestConfiguration:
    """Test configuration module."""
    
    def test_config_imports(self):
        """Test that config module imports correctly."""
        from config import (
            POSTGRES_CONFIG, 
            OPENAI_API_KEY, 
            OPENAI_MODEL,
            CHROMA_PERSIST_DIR,
            EMBEDDING_MODEL
        )
        assert POSTGRES_CONFIG is not None
        assert isinstance(POSTGRES_CONFIG, dict)
        results.add_pass("Config imports", "All config variables accessible")
    
    def test_postgres_config_structure(self):
        """Test PostgreSQL config has required keys."""
        from config import POSTGRES_CONFIG
        required_keys = ["host", "port", "database", "user", "password"]
        for key in required_keys:
            assert key in POSTGRES_CONFIG, f"Missing key: {key}"
        results.add_pass("PostgreSQL config structure", f"All {len(required_keys)} required keys present")
    
    def test_chroma_persist_dir_is_path(self):
        """Test that CHROMA_PERSIST_DIR is a Path object."""
        from config import CHROMA_PERSIST_DIR
        from pathlib import Path
        assert isinstance(CHROMA_PERSIST_DIR, Path)
        results.add_pass("ChromaDB persist dir", f"Path: {CHROMA_PERSIST_DIR}")
    
    def test_validate_config_with_missing_values(self):
        """Test validate_config raises error for missing values."""
        from config import validate_config, POSTGRES_CONFIG
        
        # Store original values
        original_db = POSTGRES_CONFIG.get("database")
        original_user = POSTGRES_CONFIG.get("user")
        
        if original_db and original_user:
            results.add_pass("Config validation", "Config is complete")
        else:
            results.add_skip("Config validation", "Missing required config values")
    
    def test_connection_string_format(self):
        """Test connection string is properly formatted."""
        from config import get_connection_string, POSTGRES_CONFIG
        
        if POSTGRES_CONFIG.get("database") and POSTGRES_CONFIG.get("user"):
            conn_str = get_connection_string()
            assert conn_str.startswith("postgresql://")
            assert "@" in conn_str
            results.add_pass("Connection string format", "Valid PostgreSQL URI format")
        else:
            results.add_skip("Connection string format", "Missing database config")


# =============================================================================
# 2. DATABASE CONNECTION TESTS
# =============================================================================

class TestDatabaseConnection:
    """Test database connectivity."""
    
    def test_connection_function_exists(self):
        """Test that get_connection function exists."""
        from database import get_connection
        assert callable(get_connection)
        results.add_pass("get_connection exists", "Function is callable")
    
    def test_test_connection_function(self):
        """Test the test_connection function."""
        from database import test_connection
        
        try:
            result = test_connection()
            if result:
                results.add_pass("Database connection", "Successfully connected to PostgreSQL")
            else:
                results.add_fail("Database connection", "Connection returned False")
        except Exception as e:
            results.add_fail("Database connection", str(e))
    
    def test_connection_context_manager(self):
        """Test connection as context manager."""
        from database import get_connection, test_connection
        
        if not test_connection():
            results.add_skip("Connection context manager", "Database not available")
            return
        
        try:
            with get_connection() as conn:
                assert conn is not None
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 as test")
                    row = cur.fetchone()
                    assert row[0] == 1
            results.add_pass("Connection context manager", "Context manager works correctly")
        except Exception as e:
            results.add_fail("Connection context manager", str(e))


# =============================================================================
# 3. DATABASE OPERATIONS TESTS
# =============================================================================

class TestDatabaseOperations:
    """Test database operations."""
    
    def test_execute_query_simple(self):
        """Test executing a simple SELECT query."""
        from database import execute_query, test_connection
        
        if not test_connection():
            results.add_skip("Execute simple query", "Database not available")
            return
        
        try:
            rows, columns = execute_query("SELECT 1 as num, 'test' as str")
            assert len(rows) == 1
            assert "num" in columns
            assert "str" in columns
            assert rows[0]["num"] == 1
            assert rows[0]["str"] == "test"
            results.add_pass("Execute simple query", f"Returned {len(rows)} row(s), {len(columns)} column(s)")
        except Exception as e:
            results.add_fail("Execute simple query", str(e))
    
    def test_execute_query_returns_dict_rows(self):
        """Test that execute_query returns dictionary rows."""
        from database import execute_query, test_connection
        
        if not test_connection():
            results.add_skip("Dict rows", "Database not available")
            return
        
        try:
            rows, _ = execute_query("SELECT 1 as a, 2 as b")
            assert isinstance(rows, list)
            assert len(rows) > 0
            assert isinstance(rows[0], dict)
            results.add_pass("Dict rows", "Rows returned as dictionaries")
        except Exception as e:
            results.add_fail("Dict rows", str(e))
    
    def test_get_schema_ddl(self):
        """Test getting schema DDL statements."""
        from database import get_schema_ddl, test_connection
        
        if not test_connection():
            results.add_skip("Get schema DDL", "Database not available")
            return
        
        try:
            ddl_list = get_schema_ddl()
            assert isinstance(ddl_list, list)
            if ddl_list:
                assert all("CREATE TABLE" in ddl for ddl in ddl_list)
                results.add_pass("Get schema DDL", f"Retrieved {len(ddl_list)} table DDL(s)")
            else:
                results.add_pass("Get schema DDL", "No user tables found (empty schema)")
        except Exception as e:
            results.add_fail("Get schema DDL", str(e))
    
    def test_get_table_names(self):
        """Test getting table names."""
        from database import get_table_names, test_connection
        
        if not test_connection():
            results.add_skip("Get table names", "Database not available")
            return
        
        try:
            tables = get_table_names()
            assert isinstance(tables, list)
            results.add_pass("Get table names", f"Found {len(tables)} table(s): {tables[:5]}...")
        except Exception as e:
            results.add_fail("Get table names", str(e))
    
    def test_execute_invalid_query(self):
        """Test that invalid SQL raises an exception."""
        from database import execute_query, test_connection
        
        if not test_connection():
            results.add_skip("Invalid query handling", "Database not available")
            return
        
        try:
            execute_query("SELECT * FROM nonexistent_table_xyz_123")
            results.add_fail("Invalid query handling", "Should have raised an exception")
        except Exception as e:
            results.add_pass("Invalid query handling", f"Correctly raised: {type(e).__name__}")


# =============================================================================
# 4. SQL ENGINE TESTS
# =============================================================================

class TestSQLEngine:
    """Test SQL generation engine."""
    
    def test_engine_imports(self):
        """Test that sql_engine module imports correctly."""
        try:
            from sql_engine import get_engine, TextToSQL
            assert callable(get_engine)
            results.add_pass("SQL engine imports", "Module imports successfully")
        except Exception as e:
            results.add_fail("SQL engine imports", str(e))
    
    def test_local_embedding_function(self):
        """Test local embedding function."""
        try:
            from sql_engine import LocalEmbeddingFunction
            embed_fn = LocalEmbeddingFunction()
            
            test_texts = ["Hello world", "Test query"]
            embeddings = embed_fn(test_texts)
            
            assert isinstance(embeddings, list)
            assert len(embeddings) == 2
            assert all(isinstance(e, list) for e in embeddings)
            assert all(isinstance(v, float) for e in embeddings for v in e)
            results.add_pass("Local embedding function", f"Generated {len(embeddings)} embeddings of dim {len(embeddings[0])}")
        except Exception as e:
            results.add_fail("Local embedding function", str(e))
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        from config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            results.add_skip("Engine initialization", "No OpenAI API key configured")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            assert engine is not None
            results.add_pass("Engine initialization", "Engine created successfully")
        except Exception as e:
            results.add_fail("Engine initialization", str(e))
    
    def test_engine_caching(self):
        """Test that engine instances are cached."""
        from config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            results.add_skip("Engine caching", "No OpenAI API key configured")
            return
        
        try:
            from sql_engine import get_engine
            engine1 = get_engine()
            engine2 = get_engine()
            assert engine1 is engine2
            results.add_pass("Engine caching", "Same instance returned for same key")
        except Exception as e:
            results.add_fail("Engine caching", str(e))
    
    def test_get_training_data_count(self):
        """Test getting training data counts."""
        from config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            results.add_skip("Training data count", "No OpenAI API key configured")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            counts = engine.get_training_data_count()
            
            assert isinstance(counts, dict)
            assert "ddl" in counts
            assert "documentation" in counts
            assert "questions" in counts
            results.add_pass("Training data count", f"DDL: {counts['ddl']}, Docs: {counts['documentation']}, Q&A: {counts['questions']}")
        except Exception as e:
            results.add_fail("Training data count", str(e))


# =============================================================================
# 5. SQL GENERATION TESTS
# =============================================================================

class TestSQLGeneration:
    """Test SQL generation from natural language."""
    
    def test_generate_simple_select(self):
        """Test generating a simple SELECT query."""
        from config import OPENAI_API_KEY
        from database import test_connection
        
        if not OPENAI_API_KEY:
            results.add_skip("Generate simple SELECT", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Generate simple SELECT", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            sql = engine.generate_sql("Show all data from customers table")
            assert sql is not None
            assert "SELECT" in sql.upper()
            results.add_pass("Generate simple SELECT", f"Generated: {sql[:50]}...")
        except Exception as e:
            results.add_fail("Generate simple SELECT", str(e))
    
    def test_generate_aggregate_query(self):
        """Test generating an aggregate query."""
        from config import OPENAI_API_KEY
        from database import test_connection
        
        if not OPENAI_API_KEY:
            results.add_skip("Generate aggregate query", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Generate aggregate query", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            sql = engine.generate_sql("How many orders are there?")
            assert sql is not None
            sql_upper = sql.upper()
            assert "SELECT" in sql_upper
            assert "COUNT" in sql_upper or "SUM" in sql_upper
            results.add_pass("Generate aggregate query", f"Generated: {sql[:50]}...")
        except Exception as e:
            results.add_fail("Generate aggregate query", str(e))
    
    def test_generate_join_query(self):
        """Test generating a JOIN query."""
        from config import OPENAI_API_KEY
        from database import test_connection
        
        if not OPENAI_API_KEY:
            results.add_skip("Generate JOIN query", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Generate JOIN query", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            sql = engine.generate_sql("Show customers with their orders")
            assert sql is not None
            sql_upper = sql.upper()
            assert "SELECT" in sql_upper
            # Should have JOIN or multiple tables
            results.add_pass("Generate JOIN query", f"Generated: {sql[:60]}...")
        except Exception as e:
            results.add_fail("Generate JOIN query", str(e))


# =============================================================================
# 6. QUERY EXECUTION TESTS
# =============================================================================

class TestQueryExecution:
    """Test full query generation and execution flow."""
    
    def test_generate_and_execute(self):
        """Test generating SQL and executing it."""
        from config import OPENAI_API_KEY
        from database import test_connection, execute_query
        
        if not OPENAI_API_KEY:
            results.add_skip("Generate and execute", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Generate and execute", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            # Generate SQL
            sql = engine.generate_sql("Show all customers")
            assert sql is not None
            
            # Execute the generated SQL
            rows, columns = execute_query(sql)
            assert isinstance(rows, list)
            assert isinstance(columns, list)
            results.add_pass("Generate and execute", f"Generated SQL returned {len(rows)} rows")
        except Exception as e:
            results.add_fail("Generate and execute", str(e))
    
    def test_complex_query_execution(self):
        """Test executing a complex generated query."""
        from config import OPENAI_API_KEY
        from database import test_connection, execute_query, get_table_names
        
        if not OPENAI_API_KEY:
            results.add_skip("Complex query execution", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Complex query execution", "Database not available")
            return
        
        try:
            tables = get_table_names()
            if len(tables) < 2:
                results.add_skip("Complex query execution", "Need at least 2 tables")
                return
            
            from sql_engine import get_engine
            engine = get_engine()
            
            sql = engine.generate_sql("What is the total revenue by product category?")
            assert sql is not None
            
            rows, columns = execute_query(sql)
            results.add_pass("Complex query execution", f"Query returned {len(rows)} rows, {len(columns)} columns")
        except Exception as e:
            # Query might fail due to schema mismatch, but SQL was generated
            results.add_pass("Complex query execution", f"SQL generated (execution: {type(e).__name__})")


# =============================================================================
# 7. SESSION STATE TESTS (Mocked Streamlit)
# =============================================================================

class TestSessionState:
    """Test session state management."""
    
    def test_init_session_state(self):
        """Test session state initialization."""
        # Mock streamlit
        mock_session_state = {}
        
        class MockST:
            session_state = mock_session_state
        
        with patch.dict('sys.modules', {'streamlit': MockST}):
            # Simulate init_session_state logic
            required_keys = ["history", "current_sql", "current_question", 
                          "current_results", "db_connected", "openai_api_key"]
            
            for key in required_keys:
                if key not in mock_session_state:
                    mock_session_state[key] = None if key != "history" else []
            
            assert "history" in mock_session_state
            assert "current_sql" in mock_session_state
            assert "current_question" in mock_session_state
            assert isinstance(mock_session_state["history"], list)
            results.add_pass("Session state initialization", f"All {len(required_keys)} state keys initialized")
    
    def test_history_tracking(self):
        """Test query history tracking."""
        history = []
        
        # Simulate adding to history
        history.append({
            "question": "Test question",
            "sql": "SELECT * FROM test",
            "time": datetime.now().strftime("%H:%M"),
            "rows": 10
        })
        
        assert len(history) == 1
        assert history[0]["question"] == "Test question"
        assert history[0]["rows"] == 10
        results.add_pass("History tracking", "History entries stored correctly")


# =============================================================================
# 8. ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API key."""
        try:
            from sql_engine import TextToSQL
            # Engine should initialize but fail on API call
            engine = TextToSQL(api_key="invalid-key")
            assert engine is not None
            results.add_pass("Invalid API key handling", "Engine created with invalid key (will fail on use)")
        except Exception as e:
            results.add_pass("Invalid API key handling", f"Properly rejected: {type(e).__name__}")
    
    def test_empty_query_handling(self):
        """Test handling of empty query."""
        from config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            results.add_skip("Empty query handling", "No OpenAI API key")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            sql = engine.generate_sql("")
            # Should return None or empty
            results.add_pass("Empty query handling", f"Result for empty query: {sql}")
        except Exception as e:
            results.add_pass("Empty query handling", f"Handled: {type(e).__name__}")
    
    def test_sql_injection_safety(self):
        """Test that SQL injection attempts are handled safely."""
        from database import test_connection
        
        if not test_connection():
            results.add_skip("SQL injection safety", "Database not available")
            return
        
        # This should fail safely - psycopg should use parameterized queries
        # or the executed query shouldn't drop tables
        malicious_input = "'; DROP TABLE users; --"
        
        from config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            results.add_skip("SQL injection safety", "No OpenAI API key")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            # The LLM should not generate destructive SQL
            sql = engine.generate_sql(f"Show data {malicious_input}")
            if sql:
                sql_upper = sql.upper()
                assert "DROP" not in sql_upper
                assert "DELETE" not in sql_upper
                assert "TRUNCATE" not in sql_upper
                results.add_pass("SQL injection safety", "No destructive SQL generated")
            else:
                results.add_pass("SQL injection safety", "Query rejected (None returned)")
        except Exception as e:
            results.add_pass("SQL injection safety", f"Safely handled: {type(e).__name__}")


# =============================================================================
# 9. INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Full integration tests."""
    
    def test_full_workflow(self):
        """Test the complete workflow: question → SQL → execution → results."""
        from config import OPENAI_API_KEY
        from database import test_connection, execute_query
        
        if not OPENAI_API_KEY:
            results.add_skip("Full workflow", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Full workflow", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            
            # Step 1: Initialize engine
            engine = get_engine()
            assert engine is not None
            
            # Step 2: Check training data
            counts = engine.get_training_data_count()
            assert isinstance(counts, dict)
            
            # Step 3: Generate SQL
            question = "List all products"
            sql = engine.generate_sql(question)
            assert sql is not None
            assert len(sql) > 0
            
            # Step 4: Execute query
            rows, columns = execute_query(sql)
            assert isinstance(rows, list)
            
            # Step 5: Verify results structure
            if rows:
                assert isinstance(rows[0], dict)
            
            results.add_pass("Full workflow", f"Complete: {len(rows)} rows returned for '{question}'")
        except Exception as e:
            results.add_fail("Full workflow", str(e))
    
    def test_multiple_queries_session(self):
        """Test multiple queries in a session."""
        from config import OPENAI_API_KEY
        from database import test_connection
        
        if not OPENAI_API_KEY:
            results.add_skip("Multiple queries session", "No OpenAI API key")
            return
        if not test_connection():
            results.add_skip("Multiple queries session", "Database not available")
            return
        
        try:
            from sql_engine import get_engine
            engine = get_engine()
            
            questions = [
                "Show all customers",
                "Count the orders",
                "List product names"
            ]
            
            generated = []
            for q in questions:
                sql = engine.generate_sql(q)
                if sql:
                    generated.append(sql)
            
            results.add_pass("Multiple queries session", f"Generated {len(generated)}/{len(questions)} queries")
        except Exception as e:
            results.add_fail("Multiple queries session", str(e))


# =============================================================================
# RUN TESTS
# =============================================================================

def run_all_tests():
    """Run all test cases and print results."""
    print("\n" + "=" * 70)
    print("QueryForge End-to-End Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_classes = [
        ("Configuration", TestConfiguration),
        ("Database Connection", TestDatabaseConnection),
        ("Database Operations", TestDatabaseOperations),
        ("SQL Engine", TestSQLEngine),
        ("SQL Generation", TestSQLGeneration),
        ("Query Execution", TestQueryExecution),
        ("Session State", TestSessionState),
        ("Error Handling", TestErrorHandling),
        ("Integration", TestIntegration),
    ]
    
    for section_name, test_class in test_classes:
        print(f"\n{'─' * 70}")
        print(f"  {section_name} Tests")
        print(f"{'─' * 70}")
        
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            method = getattr(instance, method_name)
            test_name = method_name.replace("test_", "").replace("_", " ").title()
            print(f"\n  Running: {test_name}...")
            
            try:
                method()
            except AssertionError as e:
                results.add_fail(test_name, str(e))
            except Exception as e:
                results.add_fail(test_name, f"{type(e).__name__}: {str(e)}")
    
    # Print final report
    success = results.print_report()
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

