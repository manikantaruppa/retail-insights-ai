"""
Streamlit UI for Retail Insights Assistant
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import uuid
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph import insights_graph
from src.utils.duckdb_manager import db_manager
from src.utils.metrics import metrics_tracker
from src.utils.logger import logger
from src.config import Config
from src.utils.universal_column_detector import UniversalColumnDetector
from src.utils.column_mapping_store import ColumnMappingStore

# Page configuration
st.set_page_config(
    page_title="Retail Insights Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.conversation_history = []
        st.session_state.data_loaded = False
        st.session_state.csv_path = None
        st.session_state.csv_filename = None
        st.session_state.column_mapping = None
        st.session_state.column_mapping_confirmed = False
        st.session_state.show_column_config = False

        # Start metrics session
        metrics_tracker.start_session(st.session_state.session_id)
        logger.info(f"Started new session: {st.session_state.session_id}")


def load_csv_file(uploaded_file):
    """Load CSV file into DuckDB and detect/load column mapping"""
    try:
        with st.spinner("Loading CSV file..."):
            # Save uploaded file temporarily
            temp_path = Config.DATA_DIR / uploaded_file.name
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Connect and load
            db_manager.connect()
            success = db_manager.load_csv(str(temp_path))

            if success:
                st.session_state.data_loaded = True
                st.session_state.csv_path = str(temp_path)
                st.session_state.csv_filename = uploaded_file.name

                # Check for saved column mapping
                saved_mapping = ColumnMappingStore.load_column_mapping(uploaded_file.name)

                if saved_mapping:
                    # Use saved mapping
                    st.session_state.column_mapping = saved_mapping
                    st.session_state.column_mapping_confirmed = True
                    logger.info(f"Loaded saved column mapping for {uploaded_file.name}")
                    return True, f"✅ Successfully loaded {uploaded_file.name} (using saved column mapping)"
                else:
                    # Auto-detect columns
                    schema = db_manager.get_schema()
                    detected, confidence = UniversalColumnDetector.detect_columns_with_confidence(schema)

                    if confidence >= 0.7:
                        # High confidence - use auto-detected
                        st.session_state.column_mapping = detected
                        st.session_state.column_mapping_confirmed = True
                        logger.info(f"Auto-detected columns with {confidence:.0%} confidence")
                        return True, f"✅ Successfully loaded {uploaded_file.name} (auto-detected columns: {confidence:.0%} confidence)"
                    else:
                        # Low confidence - need user confirmation
                        st.session_state.column_mapping = detected
                        st.session_state.column_mapping_confirmed = False
                        st.session_state.show_column_config = True
                        logger.info(f"Low confidence ({confidence:.0%}) - requesting user confirmation")
                        return True, f"⚠️ Loaded {uploaded_file.name}. Please confirm column mapping below (confidence: {confidence:.0%})"
            else:
                return False, "Failed to load CSV file"

    except Exception as e:
        logger.error(f"CSV loading failed: {e}")
        return False, str(e)


def show_column_confirmation_ui():
    """Show interactive UI for column mapping confirmation"""
    st.markdown("---")
    st.markdown("### 📋 Column Mapping Confirmation")
    st.warning("⚠️ We're not sure about some columns. Please help us identify them:")

    # Load sample data
    df = pd.read_csv(st.session_state.csv_path)

    # Show sample data
    st.markdown("**Sample Data (first 3 rows):**")
    st.dataframe(df.head(3), use_container_width=True)

    detected = st.session_state.column_mapping
    all_columns = ['(None)'] + list(df.columns)

    # Create form for column selection
    with st.form("column_mapping_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Categorical column
            st.markdown("#### 1️⃣ Category/Type Column")
            st.caption("Examples: Product Category, Type, Class")
            default_cat = detected.get('categorical', [])[0] if detected.get('categorical') else '(None)'
            categorical = st.selectbox(
                "Select categorical column:",
                options=all_columns,
                index=all_columns.index(default_cat) if default_cat in all_columns else 0,
                help="Column for grouping (e.g., Product Category)"
            )

            if categorical != '(None)':
                unique_vals = df[categorical].unique()[:5]
                st.info(f"📊 Preview: {', '.join(map(str, unique_vals))}... ({len(df[categorical].unique())} unique)")

            # Numeric column
            st.markdown("#### 2️⃣ Revenue/Amount Column")
            st.caption("Examples: Amount, Price, Revenue, Sales")
            default_num = detected.get('numeric', [])[0] if detected.get('numeric') else '(None)'
            numeric = st.selectbox(
                "Select numeric column:",
                options=all_columns,
                index=all_columns.index(default_num) if default_num in all_columns else 0,
                help="Column to sum/average (e.g., Order Amount)"
            )

            if numeric != '(None)':
                sample_vals = df[numeric].head(3).values
                st.info(f"💰 Sample: {', '.join(map(str, sample_vals))}")

        with col2:
            # Location column
            st.markdown("#### 3️⃣ Location Column (Optional)")
            st.caption("Examples: State, City, Region, Country")
            default_loc = detected.get('location', [])[0] if detected.get('location') else '(None)'
            location = st.selectbox(
                "Select location column:",
                options=all_columns,
                index=all_columns.index(default_loc) if default_loc in all_columns else 0,
                help="Geographic column for regional analysis"
            )

            if location != '(None)':
                unique_locs = df[location].unique()[:5]
                st.info(f"📍 Preview: {', '.join(map(str, unique_locs))}...")

            # Date column
            st.markdown("#### 4️⃣ Date Column (Optional)")
            st.caption("Examples: Date, Order_Date, Created_At")
            default_date = detected.get('date', [])[0] if detected.get('date') else '(None)'
            date = st.selectbox(
                "Select date column:",
                options=all_columns,
                index=all_columns.index(default_date) if default_date in all_columns else 0,
                help="Date column for time-based analysis"
            )

            if date != '(None)':
                sample_dates = df[date].head(3).values
                st.info(f"📅 Sample: {', '.join(map(str, sample_dates))}")

        # Submit button
        submitted = st.form_submit_button("✅ Confirm Column Selection", use_container_width=True)

        if submitted:
            # Save mapping
            confirmed_mapping = {
                'categorical': categorical,
                'numeric': numeric,
                'location': location,
                'date': date
            }

            st.session_state.column_mapping = confirmed_mapping
            st.session_state.column_mapping_confirmed = True
            st.session_state.show_column_config = False

            # Save to store
            ColumnMappingStore.save_column_mapping(st.session_state.csv_filename, confirmed_mapping)

            st.success("✅ Column mapping saved! You won't be asked again for this file.")
            st.rerun()


def display_sidebar():
    """Display sidebar with controls and metrics"""
    st.sidebar.markdown("## 📊 Retail Insights Assistant")
    st.sidebar.markdown("---")

    # File upload
    st.sidebar.markdown("### 📁 Data Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="Upload your sales data CSV file"
    )

    if uploaded_file and not st.session_state.data_loaded:
        success, message = load_csv_file(uploaded_file)
        if success:
            st.sidebar.success(message)
        else:
            st.sidebar.error(message)

    # Show data info if loaded
    if st.session_state.data_loaded:
        st.sidebar.markdown("### 📈 Dataset Info")
        stats = db_manager.get_table_stats()
        st.sidebar.metric("Total Rows", f"{stats.get('total_rows', 0):,}")
        st.sidebar.metric("Columns", stats.get('column_count', 0))

        if stats.get('date_range'):
            st.sidebar.text(f"Date Range:")
            st.sidebar.text(f"{stats['date_range'].get('min', 'N/A')}")
            st.sidebar.text(f"to {stats['date_range'].get('max', 'N/A')}")

    st.sidebar.markdown("---")

    # Session metrics
    st.sidebar.markdown("### 📊 Session Metrics")
    session_summary = metrics_tracker.get_session_summary()

    if session_summary.get('total_queries', 0) > 0:
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Queries", session_summary.get('total_queries', 0))
        col2.metric("Success Rate", f"{session_summary.get('success_rate', 0):.1f}%")

        st.sidebar.metric("Avg Latency", f"{session_summary.get('avg_latency_ms', 0):.0f} ms")
        st.sidebar.metric("Total Cost", f"${session_summary.get('total_cost', 0):.4f}")

    st.sidebar.markdown("---")

    # Actions
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.rerun()

    if st.sidebar.button("💾 Export Metrics"):
        metrics_tracker.export_session()
        st.sidebar.success(f"Metrics exported to logs/")


def display_main_content():
    """Display main content area"""

    # Header
    st.markdown('<div class="main-header">🤖 Retail Insights Assistant</div>', unsafe_allow_html=True)
    st.markdown("*Ask questions about your sales data or generate automatic summaries*")

    if not st.session_state.data_loaded:
        st.info("👈 Please upload a CSV file to get started")
        return

    # Show column configuration UI if needed
    if st.session_state.show_column_config and not st.session_state.column_mapping_confirmed:
        show_column_confirmation_ui()
        return

    # Show column mapping info if configured
    if st.session_state.column_mapping_confirmed and st.session_state.column_mapping:
        mapping = st.session_state.column_mapping
        with st.expander("🔧 Column Configuration (click to view/change)", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Category", mapping.get('categorical', 'None'))
            col2.metric("Numeric", mapping.get('numeric', 'None'))
            col3.metric("Location", mapping.get('location', 'None'))
            col4.metric("Date", mapping.get('date', 'None'))

            if st.button("🔄 Change Column Mapping"):
                st.session_state.show_column_config = True
                st.rerun()

    # Mode selection
    col1, col2 = st.columns(2)

    with col1:
        # Only enable summary if column mapping is confirmed
        if st.session_state.column_mapping_confirmed:
            if st.button("📝 Generate Summary", use_container_width=True):
                generate_summary()
        else:
            st.button("📝 Generate Summary", use_container_width=True, disabled=True)
            st.caption("⚠️ Please confirm column mapping first")

    with col2:
        st.markdown("**or ask a question below**")

    st.markdown("---")

    # Chat interface
    display_chat_interface()


def generate_summary():
    """Generate automatic summary"""
    with st.spinner("Analyzing data and generating summary..."):
        try:
            # Pass column mapping to graph
            result = insights_graph.process_query(
                mode="summarization",
                column_mapping=st.session_state.column_mapping
            )

            # Add to conversation history
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": result["response"],
                "type": "summary",
                "timestamp": datetime.now().isoformat(),
                "success": result["success"]
            })

            st.rerun()

        except Exception as e:
            st.error(f"Summary generation failed: {e}")


def display_chat_interface():
    """Display chat interface"""

    # Display conversation history
    for msg in st.session_state.conversation_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

                # Show metadata
                if msg.get("type") == "qa" and msg.get("sql_query"):
                    with st.expander("🔍 View SQL Query"):
                        st.code(msg["sql_query"], language="sql")

                if msg.get("confidence_score") is not None:
                    confidence = msg["confidence_score"]
                    if confidence >= 0.8:
                        color = "green"
                    elif confidence >= 0.6:
                        color = "orange"
                    else:
                        color = "red"

                    st.markdown(f"**Confidence:** :{color}[{confidence:.0%}]")

    # Chat input
    user_question = st.chat_input("Ask a question about your sales data...")

    if user_question:
        # Add user message
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_question,
            "timestamp": datetime.now().isoformat()
        })

        # Process query
        with st.spinner("Thinking..."):
            try:
                result = insights_graph.process_query(
                    mode="qa",
                    user_question=user_question,
                    conversation_history=st.session_state.conversation_history
                )

                # Add assistant response
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": result["response"],
                    "type": "qa",
                    "sql_query": result.get("sql_query"),
                    "confidence_score": result.get("confidence_score"),
                    "timestamp": datetime.now().isoformat(),
                    "success": result["success"]
                })

                st.rerun()

            except Exception as e:
                st.error(f"Query processing failed: {e}")


def display_example_queries():
    """Display example queries"""
    st.markdown("### 💡 Example Questions")

    examples = [
        "What are the top 5 best-selling categories?",
        "Show me total revenue by region",
        "Which products were cancelled the most?",
        "What's the order fulfillment breakdown?",
        "Show sales trends over time",
    ]

    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        if col.button(example, use_container_width=True):
            st.session_state.conversation_history.append({
                "role": "user",
                "content": example,
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()


def main():
    """Main application"""
    initialize_session_state()
    display_sidebar()
    display_main_content()

    # Show example queries if no conversation yet
    if not st.session_state.conversation_history and st.session_state.data_loaded:
        st.markdown("---")
        display_example_queries()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Powered by Google Gemini 2.0/2.5 • LangGraph • DuckDB"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
