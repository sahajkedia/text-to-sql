# QueryForge

Natural language to SQL powered by semantic search and LLMs.

## How It Works

1. **Local Embeddings**: Questions are embedded using all-MiniLM-L6-v2 (384 dimensions, runs locally)
2. **Vector Search**: HNSW indexing in ChromaDB provides O(log N) similarity lookup
3. **Context Assembly**: The 5 most similar training examples, full schema DDL, and documentation are assembled into a prompt
4. **SQL Generation**: OpenAI generates a PostgreSQL query based on the context
5. **Execution**: The query runs against your database and returns results

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Edit `.env` with your settings:

```
OPENAI_API_KEY=sk-...
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=mydb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
```

## Training

The system needs training data to generate accurate SQL. Train it with:

### 1. Schema (DDL)

Extract from your database:
```bash
python train.py ddl --from-db
```

Or from a SQL file:
```bash
python train.py ddl --file schema.sql
```

### 2. Documentation

Add business context:
```bash
python train.py docs docs/database.md
```

### 3. Question-SQL Examples

Add example pairs (JSON format):
```bash
python train.py examples examples/queries.json
```

Example format:
```json
[
  {
    "question": "Show customers who signed up this month",
    "sql": "SELECT * FROM customers WHERE created_at >= date_trunc('month', CURRENT_DATE);"
  }
]
```

### Check Training Status

```bash
python train.py stats
```

## Running

```bash
streamlit run app.py
```

Open http://localhost:8501

## Project Structure

```
├── app.py           # Streamlit interface
├── sql_engine.py    # Vanna.ai + ChromaDB + OpenAI integration
├── database.py      # PostgreSQL connection handling
├── train.py         # Training CLI
├── config.py        # Configuration management
├── examples/        # Sample training data
│   ├── sample_ddl.sql
│   ├── sample_docs.md
│   └── sample_examples.json
└── chroma_data/     # Vector store (gitignored)
```

## Training Tips

- **Quality over quantity**: 10 well-chosen examples outperform 100 generic ones
- **Cover your domain**: Include examples that match how your users phrase questions
- **Include edge cases**: Add examples for tricky joins, date ranges, aggregations
- **Keep DDL current**: Re-train when schema changes
- **Add documentation**: Business context helps with ambiguous terms

