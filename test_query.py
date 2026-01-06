#!/usr/bin/env python3
"""Quick test to verify end-to-end SQL generation."""

from sql_engine import get_engine
from database import execute_query, test_connection
from config import validate_config

def main():
    print("QueryForge End-to-End Test")
    print("=" * 40)
    
    try:
        validate_config()
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nAdd your OpenAI key to .env:")
        print("  OPENAI_API_KEY=sk-...")
        return
    
    if not test_connection():
        print("\n✗ Database connection failed")
        return
    
    print("\n1. Database: Connected")
    
    engine = get_engine()
    counts = engine.get_training_data_count()
    print(f"2. Training data: {counts['ddl']} tables, {counts['questions']} examples")
    
    question = "Show all customers and their total order amounts"
    print(f"\n3. Test question: {question}")
    
    print("\n4. Generating SQL...")
    sql = engine.generate_sql(question)
    
    if sql:
        print(f"\n   Generated SQL:\n   {sql}")
        
        print("\n5. Executing query...")
        try:
            rows, cols = execute_query(sql)
            print(f"\n   ✓ Query returned {len(rows)} rows")
            if rows:
                print(f"   Columns: {cols}")
                for row in rows[:5]:
                    print(f"   {row}")
                if len(rows) > 5:
                    print(f"   ... and {len(rows) - 5} more rows")
        except Exception as e:
            print(f"\n   ✗ Query execution error: {e}")
    else:
        print("\n   ✗ Failed to generate SQL")


if __name__ == "__main__":
    main()

