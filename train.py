#!/usr/bin/env python3
"""
Training script for the text-to-SQL system.
Loads DDL statements, documentation, and example question-SQL pairs into the vector store.
"""

import argparse
import json
from pathlib import Path
from database import get_schema_ddl, test_connection
from sql_engine import get_engine
from config import validate_config


def train_ddl_from_database():
    print("Extracting DDL from database...")
    ddl_statements = get_schema_ddl()
    engine = get_engine()

    for ddl in ddl_statements:
        engine.train(ddl=ddl)
        print(f"  Trained: {ddl[:60]}...")

    print(f"Added {len(ddl_statements)} DDL statements")


def train_ddl_from_file(file_path: str):
    print(f"Loading DDL from {file_path}...")
    content = Path(file_path).read_text()
    statements = [s.strip() for s in content.split(";") if s.strip()]
    engine = get_engine()

    for ddl in statements:
        if ddl.upper().startswith(("CREATE", "ALTER")):
            engine.train(ddl=ddl + ";")
            print(f"  Trained: {ddl[:60]}...")

    print(f"Added {len(statements)} DDL statements")


def train_documentation(file_path: str):
    print(f"Loading documentation from {file_path}...")
    content = Path(file_path).read_text()
    engine = get_engine()
    engine.train(documentation=content)
    print("Documentation added")


def train_examples(file_path: str):
    print(f"Loading examples from {file_path}...")
    examples = json.loads(Path(file_path).read_text())
    engine = get_engine()

    for example in examples:
        question = example.get("question")
        sql = example.get("sql")
        if question and sql:
            engine.train(question=question, sql=sql)
            print(f"  Trained: {question[:50]}...")

    print(f"Added {len(examples)} question-SQL pairs")


def show_stats():
    engine = get_engine()
    counts = engine.get_training_data_count()
    print("\nTraining Data Statistics:")
    print(f"  DDL statements:    {counts['ddl']}")
    print(f"  Documentation:     {counts['documentation']}")
    print(f"  Question-SQL pairs: {counts['questions']}")


def main():
    parser = argparse.ArgumentParser(description="Train the text-to-SQL system")
    subparsers = parser.add_subparsers(dest="command", help="Training commands")

    ddl_parser = subparsers.add_parser("ddl", help="Train with DDL statements")
    ddl_parser.add_argument("--from-db", action="store_true", help="Extract DDL from connected database")
    ddl_parser.add_argument("--file", type=str, help="Path to SQL file with DDL statements")

    doc_parser = subparsers.add_parser("docs", help="Train with documentation")
    doc_parser.add_argument("file", type=str, help="Path to documentation file")

    examples_parser = subparsers.add_parser("examples", help="Train with question-SQL pairs")
    examples_parser.add_argument("file", type=str, help="Path to JSON file with examples")

    subparsers.add_parser("stats", help="Show training data statistics")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    validate_config()

    if args.command == "ddl":
        if args.from_db:
            if not test_connection():
                print("Error: Cannot connect to database")
                return
            train_ddl_from_database()
        elif args.file:
            train_ddl_from_file(args.file)
        else:
            print("Specify --from-db or --file")

    elif args.command == "docs":
        train_documentation(args.file)

    elif args.command == "examples":
        train_examples(args.file)

    elif args.command == "stats":
        show_stats()


if __name__ == "__main__":
    main()

