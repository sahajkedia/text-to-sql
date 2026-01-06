import os

# Disable chromadb telemetry before imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["POSTHOG_DISABLED"] = "1"
os.environ["CHROMA_TELEMETRY"] = "False"

import streamlit as st
import pandas as pd
from datetime import datetime
from sql_engine import get_engine
from database import execute_query, test_connection, get_table_names
from config import POSTGRES_CONFIG

st.set_page_config(
    page_title="QueryForge",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #0a0a0b;
    --bg-secondary: #111113;
    --bg-tertiary: #1a1a1d;
    --border-color: #2a2a2d;
    --text-primary: #fafafa;
    --text-secondary: #a1a1a6;
    --accent: #f97316;
    --accent-dim: #c2410c;
    --success: #22c55e;
    --error: #ef4444;
}

.stApp {
    background: linear-gradient(180deg, var(--bg-primary) 0%, #0d0d0f 100%);
}

.main .block-container {
    padding: 2rem 3rem;
    max-width: 1400px;
}

h1, h2, h3, h4, h5, h6, p, span, div, label {
    font-family: 'Outfit', sans-serif !important;
}

code, pre, .stCode {
    font-family: 'JetBrains Mono', monospace !important;
}

.main-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.5rem;
}

.main-header h1 {
    font-size: 2.25rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    font-weight: 300;
    margin-bottom: 2rem;
}

.stTextArea textarea, .stTextInput input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1rem !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}

.stTextArea textarea::placeholder, .stTextInput input::placeholder {
    color: var(--text-secondary) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 2rem !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.3) !important;
}

.stButton > button:active {
    transform: translateY(0);
}

.sql-output {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1rem 0;
}

.sql-output pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: var(--text-primary) !important;
    background: var(--bg-tertiary) !important;
    font-size: 0.9rem;
    line-height: 1.6;
    padding: 1rem;
    border-radius: 8px;
}

.sql-output pre code {
    color: var(--text-primary) !important;
    background: transparent !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem;
}

.sql-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.75rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.results-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.results-count {
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.stDataFrame {
    background: transparent !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: var(--bg-tertiary) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 2rem 1.5rem;
}

.sidebar-section {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.sidebar-title {
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.75rem;
}

.stat-value {
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 600;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
}

.status-connected {
    background: rgba(34, 197, 94, 0.15);
    color: var(--success);
}

.status-disconnected {
    background: rgba(239, 68, 68, 0.15);
    color: var(--error);
}

.status-warning {
    background: rgba(249, 115, 22, 0.15);
    color: var(--accent);
}

.history-item {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: border-color 0.15s ease;
}

.history-item:hover {
    border-color: var(--accent);
}

.history-question {
    color: var(--text-primary);
    font-size: 0.85rem;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.history-time {
    color: var(--text-secondary);
    font-size: 0.7rem;
}

.stSpinner > div {
    border-color: var(--accent) transparent transparent transparent !important;
}

.error-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 10px;
    padding: 1rem;
    color: var(--error);
}

.stAlert {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
}

div[data-testid="stExpander"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
}

.table-chip {
    display: inline-block;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 4px 8px;
    margin: 2px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-family: 'JetBrains Mono', monospace;
}

.api-key-section {
    margin-bottom: 1.5rem;
}

.api-key-label {
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "current_sql" not in st.session_state:
        st.session_state.current_sql = None
    if "current_results" not in st.session_state:
        st.session_state.current_results = None
    if "db_connected" not in st.session_state:
        st.session_state.db_connected = False
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""


def check_connection():
    try:
        st.session_state.db_connected = test_connection()
    except Exception:
        st.session_state.db_connected = False


def render_sidebar():
    with st.sidebar:
        # OpenAI API Key input
        st.markdown('<div class="sidebar-title">OpenAI API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.openai_api_key,
            placeholder="sk-...",
            label_visibility="collapsed",
            key="api_key_input",
        )
        if api_key != st.session_state.openai_api_key:
            st.session_state.openai_api_key = api_key
        
        if api_key and api_key.startswith("sk-"):
            st.markdown(
                '<span class="status-badge status-connected" style="margin-bottom: 1rem; display: inline-flex;">● Key configured</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-badge status-warning" style="margin-bottom: 1rem; display: inline-flex;">● Enter your key</span>',
                unsafe_allow_html=True,
            )
        
        st.markdown("---")
        
        # Connection Status
        st.markdown('<div class="sidebar-title">Database</div>', unsafe_allow_html=True)

        if st.session_state.db_connected:
            st.markdown(
                f"""
                <div class="sidebar-section">
                    <span class="status-badge status-connected">● Connected</span>
                    <div style="margin-top: 8px; color: var(--text-secondary); font-size: 0.8rem;">
                        {POSTGRES_CONFIG['database']}@{POSTGRES_CONFIG['host']}
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            engine = get_engine(st.session_state.openai_api_key or None)
            counts = engine.get_training_data_count()

            st.markdown('<div class="sidebar-title">Training Data</div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    f'<div class="stat-value">{counts["ddl"]}</div><div class="stat-label">Tables</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f'<div class="stat-value">{counts["documentation"]}</div><div class="stat-label">Docs</div>',
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f'<div class="stat-value">{counts["questions"]}</div><div class="stat-label">Examples</div>',
                    unsafe_allow_html=True,
                )

            try:
                tables = get_table_names()
                if tables:
                    st.markdown('<div class="sidebar-title" style="margin-top: 1.5rem;">Available Tables</div>', unsafe_allow_html=True)
                    chips_html = "".join([f'<span class="table-chip">{t}</span>' for t in tables[:15]])
                    if len(tables) > 15:
                        chips_html += f'<span class="table-chip">+{len(tables) - 15} more</span>'
                    st.markdown(f'<div style="margin-bottom: 1rem;">{chips_html}</div>', unsafe_allow_html=True)
            except Exception:
                pass

        else:
            st.markdown(
                """
                <div class="sidebar-section">
                    <span class="status-badge status-disconnected">● Disconnected</span>
                    <div style="margin-top: 8px; color: var(--text-secondary); font-size: 0.8rem;">
                        Check your .env configuration
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        if st.session_state.history:
            st.markdown('<div class="sidebar-title" style="margin-top: 1.5rem;">Recent Queries</div>', unsafe_allow_html=True)
            for i, item in enumerate(reversed(st.session_state.history[-8:])):
                truncated = item["question"][:40] + "..." if len(item["question"]) > 40 else item["question"]
                st.markdown(
                    f"""
                    <div class="history-item">
                        <div class="history-question">{truncated}</div>
                        <div class="history-time">{item['time']}</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )


def process_question(question: str):
    api_key = st.session_state.openai_api_key
    
    if not api_key or not api_key.startswith("sk-"):
        st.error("Please enter your OpenAI API key in the sidebar.")
        return
    
    engine = get_engine(api_key)

    with st.spinner("Generating SQL..."):
        try:
            sql = engine.generate_sql(question)
        except Exception as e:
            error_msg = str(e).lower()
            if "api_key" in error_msg or "auth" in error_msg or "invalid" in error_msg:
                st.error("Invalid API key. Please check your OpenAI API key.")
            else:
                st.error(f"Error generating SQL: {e}")
            return

    if not sql:
        st.error("Could not generate SQL for this question.")
        return

    st.session_state.current_sql = sql

    st.markdown(
        f"""
        <div class="sql-output">
            <div class="sql-label">
                <span>Generated SQL</span>
            </div>
            <pre><code>{sql}</code></pre>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_query = st.button("Execute Query", use_container_width=True)

    if run_query:
        try:
            with st.spinner("Running query..."):
                rows, columns = execute_query(sql)

            st.session_state.current_results = rows
            st.session_state.history.append(
                {
                    "question": question,
                    "sql": sql,
                    "time": datetime.now().strftime("%H:%M"),
                    "rows": len(rows),
                }
            )

            if rows:
                df = pd.DataFrame(rows)
                st.markdown(
                    f"""
                    <div class="results-header">
                        <span style="color: var(--text-primary); font-weight: 500;">Results</span>
                        <span class="results-count">{len(rows)} row{'s' if len(rows) != 1 else ''}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Query executed successfully. No rows returned.")

        except Exception as e:
            st.markdown(
                f"""
                <div class="error-box">
                    <strong>Query Error</strong><br>
                    {str(e)}
                </div>
            """,
                unsafe_allow_html=True,
            )


def main():
    init_session_state()
    check_connection()

    st.markdown(
        """
        <div class="main-header">
            <h1>QueryForge</h1>
        </div>
        <p class="subtitle">Natural language to SQL, powered by your schema</p>
    """,
        unsafe_allow_html=True,
    )

    render_sidebar()

    if not st.session_state.db_connected:
        st.warning("Database not connected. Please check your configuration in `.env`")

        with st.expander("Configuration Guide"):
            st.code(
                """
# Create a .env file with:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
            """,
                language="bash",
            )
        return

    question = st.text_area(
        "Ask a question about your data",
        placeholder="e.g., Show me the top 10 customers by total order value last month",
        height=100,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        submitted = st.button("Generate SQL", use_container_width=True)

    if submitted and question.strip():
        process_question(question.strip())
    elif submitted:
        st.warning("Please enter a question.")


if __name__ == "__main__":
    main()
