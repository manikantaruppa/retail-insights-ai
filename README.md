# 🤖 Retail Insights Assistant

An intelligent AI-powered system for analyzing large-scale retail sales data using natural language. Built with Google Gemini 2.0/2.5 (multi-model fallback), LangGraph multi-agent orchestration, and DuckDB for efficient analytics.

## 🌟 Features

- **📊 Automatic Summarization**: Generate executive summaries automatically
- **💬 Natural Language Q&A**: Ask business questions in plain English
- **🔒 Safe SQL Execution**: Multi-layer validation prevents dangerous queries
- **⚡ High Performance**: DuckDB handles million-row datasets efficiently
- **📈 Real-time Metrics**: Track cost, latency, and accuracy
- **🛡️ Security**: PII masking, SQL injection prevention, API key protection
- **🎨 Interactive UI**: Streamlit-based web interface

## 🏗️ System Architecture

### Overview: Production-Grade Multi-Agent AI System

Built with **BigQuery AI-inspired security model** for enterprise-ready data analysis.

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    🌐 USER INTERFACE (Streamlit)                  ┃
┃                    Natural Language Input/Output                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                               ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              🎯 ORCHESTRATOR (LangGraph StateGraph)              ┃
┃         • Mode Detection (Summarization vs Q&A)                  ┃
┃         • State Management (conversation memory)                 ┃
┃         • Metrics Tracking (cost, latency, confidence)           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                               ↓
                    ┌──────────┴──────────┐
                    ↓                     ↓
    ┏━━━━━━━━━━━━━━━━━━━━━┓   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ 📊 SUMMARIZATION    ┃   ┃ 💬 Q&A MODE (NL → Insights)    ┃
    ┃     MODE            ┃   ┃                                 ┃
    ┃ ┌─────────────────┐ ┃   ┃ ┌──────────────────────────┐   ┃
    ┃ │Auto-generate    │ ┃   ┃ │ 1️⃣ Language-to-Query    │   ┃
    ┃ │executive summary│ ┃   ┃ │    Gemini 2.0/2.5       │   ┃
    ┃ │with pre-defined │ ┃   ┃ │    NL → SQL generation  │   ┃
    ┃ │aggregation SQL  │ ┃   ┃ └───────────┬──────────────┘   ┃
    ┃ └────────┬────────┘ ┃   ┃             ↓                  ┃
    ┃          ↓          ┃   ┃ ┌──────────────────────────┐   ┃
    ┃ ┌─────────────────┐ ┃   ┃ │ 2️⃣ Enhanced Validation  │   ┃
    ┃ │Execute standard │ ┃   ┃ │    • PII Protection      │   ┃
    ┃ │SQL queries      │ ┃   ┃ │    • SQL Injection Check │   ┃
    ┃ └────────┬────────┘ ┃   ┃ │    • Syntax Validation   │   ┃
    ┗━━━━━━━━━━┷━━━━━━━━━━┛   ┃ └───────────┬──────────────┘   ┃
               ↓               ┃             ↓                  ┃
               └───────────────┃ ┌──────────────────────────┐   ┃
                               ┃ │ 3️⃣ Extraction Agent     │   ┃
                               ┃ │    Execute SQL on        │   ┃
                               ┃ │    DuckDB (128K rows)    │   ┃
                               ┃ └───────────┬──────────────┘   ┃
                               ┗━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━┛
                                             ↓
                         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                         ┃ 🔒 RESULT SUMMARIZER (LOCAL)        ┃
                         ┃ • Extracts statistics (no raw data) ┃
                         ┃ • Protects PII (GDPR/CCPA/HIPAA)    ┃
                         ┃ • Aggregates: COUNT, AVG, MIN, MAX  ┃
                         ┗━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┛
                                           ↓
                         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                         ┃ 4️⃣ Secure Insight Agent             ┃
                         ┃ • Receives statistics only          ┃
                         ┃ • Generates natural language output ┃
                         ┃ • Never sees raw customer data      ┃
                         ┗━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┛
                                           ↓
                         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                         ┃ 📊 CONVERSATIONAL INSIGHTS          ┃
                         ┃ "Sales totaled ₹5.2M across..."     ┃
                         ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### 🎯 Multi-Agent System (6 Specialized Agents)

| Agent | Role | Technology | Key Features |
|-------|------|------------|--------------|
| **1️⃣ Orchestrator** | Route requests, manage state | LangGraph StateGraph | Mode detection, conversation memory, metrics tracking |
| **2️⃣ Summarization** | Auto-generate summaries | Pre-defined SQL + Gemini | Executive insights, trend analysis, top performers |
| **3️⃣ Language-to-Query** | NL → SQL conversion | Gemini 2.0/2.5 + TRY_CAST | Handles dirty data, schema-aware, confidence scoring |
| **4️⃣ Enhanced Validation** | Security & safety checks | Pattern matching + PII detector | Blocks raw PII queries, SQL injection prevention |
| **5️⃣ Extraction** | Execute queries | DuckDB | Columnar storage, vectorized execution, <2s latency |
| **6️⃣ Secure Insight** | Privacy-preserving insights | Result summarizer + Gemini | Statistics only (no raw data), GDPR/CCPA compliant |

### 🔒 Security Model (BigQuery AI Approach)

**Zero Raw Data Exposure to LLM:**

```
Traditional Approach (❌ INSECURE):
Query Results (20 rows) → LLM → Insights
Problem: LLM sees customer names, emails, order IDs

Our Approach (✅ SECURE - BigQuery AI Level):
Query Results → Local Summarizer → Statistics → LLM → Insights
                                    ↑
                        Only aggregated numbers
                        (COUNT, AVG, MIN, MAX)
```

**Benefits:**
- ✅ **GDPR/CCPA/HIPAA Compliant** - No PII exposed to LLM
- ✅ **Validation Blocking** - Prevents `SELECT DISTINCT customer_id`
- ✅ **Local Processing** - Data never leaves your machine
- ✅ **Audit Trail** - All queries logged (no sensitive data)

### 🚀 Data Flow Example

```
User: "What are the top 5 selling categories?"
  ↓
1. Orchestrator → Routes to Q&A Mode
  ↓
2. Language-to-Query Agent:
   SQL: SELECT category, SUM(TRY_CAST(amount AS DECIMAL)) as total
        FROM sales GROUP BY category ORDER BY total DESC LIMIT 5
  ↓
3. Enhanced Validation:
   ✅ No PII columns (✓)
   ✅ No dangerous keywords (✓)
   ✅ Valid SQL syntax (✓)
  ↓
4. Extraction Agent:
   DuckDB executes query → Returns 5 rows
  ↓
5. Result Summarizer (LOCAL):
   Raw: [{cat: "Kurta", amt: 2.1M}, {cat: "Set", amt: 1.1M}, ...]
   Stats: {top_category: "Kurta", top_revenue: 2.1M, categories: 5, ...}
  ↓
6. Secure Insight Agent:
   Input: Statistics only (no raw data)
   Output: "The top-selling category is Kurta with ₹2.1M in revenue,
            followed by Set (₹1.1M) and Western Dress (₹750K)..."
```

### 📊 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | Google Gemini 2.0/2.5 | NL understanding, SQL generation, insight formatting |
| **Orchestration** | LangGraph (StateGraph) | Multi-agent workflow, state management, routing |
| **Database** | DuckDB | In-memory analytics, columnar storage, 128K rows tested |
| **Security** | PII Detector + Result Summarizer | BigQuery AI-level privacy protection |
| **UI** | Streamlit | Interactive web interface, real-time metrics |
| **Language** | Python 3.13 | Modern async/await, type hints, pydantic models |

## 🚀 Quick Start

> **📸 For visual demo walkthrough with screenshots, see [DEMO.md](DEMO.md)**

### Prerequisites

- Python 3.13+ (tested with 3.13, works with 3.10+)
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Installation

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/retail-insights-assistant.git
cd retail-insights-assistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Application

#### Option 1: Streamlit UI (Recommended)

```bash
streamlit run ui/streamlit_app.py
```

Then open http://localhost:8501 in your browser.

#### Option 2: CLI Mode

```bash
python -m src.main
```

## 📖 Usage Guide

### Summarization Mode

Automatically generates an executive summary of your sales data:

1. Upload CSV file
2. Click "Generate Summary"
3. Get insights on:
   - Overall performance
   - Top categories/regions
   - Trends and patterns
   - Key opportunities

**Example Output:**
```
Overall sales in the dataset total ₹5.2M across 128,976 orders.
The Kurta category leads with 40% of revenue, followed by Sets (22%)
and Western Dress (15%). Maharashtra accounts for the highest order
volume with 25,432 orders...
```

### Q&A Mode

Ask natural language questions about your data:

**Example Questions:**
- "What are the top 5 best-selling categories?"
- "Show me total revenue by region"
- "Which products had the most cancellations?"
- "What's the average order value?"
- "Show sales trends by month"

**Features:**
- Conversation memory (contextual follow-ups)
- Confidence scoring (see how confident the AI is)
- View generated SQL (full transparency)
- Error handling with helpful suggestions

## 📊 Dataset Format

### Supported Input Formats

- CSV files (primary)
- Excel, JSON (documented for future enhancement)

### Required Columns (Amazon Sales Dataset)

The system works with the provided Amazon Sale Report CSV containing:

- Order ID, Date, Status
- Category, Style, SKU, Size
- Amount, Qty, Currency
- Ship City, Ship State, Ship Postal Code
- Fulfilment method
- B2B flag

**Schema is auto-detected** - the system adapts to your column names.

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
GEMINI_MODEL=models/gemini-2.0-flash-exp  # Primary model (auto-fallback enabled)
LOG_LEVEL=INFO
GEMINI_INPUT_COST=0.0      # Free tier
GEMINI_OUTPUT_COST=0.0     # Free tier
```

### Multi-Model Fallback System

The system uses **10+ Gemini models** with automatic fallback for 99.9% uptime:

**Tier 1 (Fastest, Free Tier Optimized):**
- `gemini-2.0-flash-lite` - Primary for free tier quota
- `gemini-2.0-flash-lite-001`

**Tier 2 (Balanced, Recommended):**
- `gemini-2.0-flash` - Good speed/capability balance
- `gemini-2.5-flash` - **Currently working** (best performance)

**Tier 3 (Experimental):**
- `gemini-exp-1206` - Latest experimental features

**Tier 4 (Most Capable):**
- `gemini-2.5-pro` - Highest quality responses

**Tier 5 (Legacy Fallback):**
- `gemini-1.5-flash-002`, `gemini-1.5-pro-002` - Backup models

If quota is exceeded on one model, the system automatically tries the next model in the tier list.

### System Limits

```python
MAX_QUERY_TIMEOUT = 300     # 5 minutes
MAX_RESULT_ROWS = 10000
MAX_RETRIES = 3
```

## 📈 Performance & Scalability

### Current Implementation (Local)

- **Dataset Size**: Up to 10GB
- **Engine**: DuckDB (columnar, vectorized execution)
- **Query Performance**: Sub-second for aggregations on millions of rows
- **Memory**: Efficient streaming, doesn't load entire dataset

### 100GB+ Scaling Architecture

For production deployment with 100GB+ data:

#### Data Engineering Layer
```
Raw CSV → PySpark/Dask → Parquet/Delta Lake
                ↓
        Partitioned by date/region
                ↓
    Cloud Data Warehouse (BigQuery/Snowflake)
```

#### Storage Strategy
- **Data Lake**: S3/GCS for raw data
- **Warehouse**: BigQuery for analytics
- **Caching**: Redis for query results
- **Pre-aggregation**: Materialized views for common queries

#### Query Optimization
- Partition pruning (by date, region)
- Column projection (only read needed columns)
- Query result caching (semantic similarity)
- Incremental refresh for aggregates

#### Cost Controls
- Query complexity validation
- Execution cost estimation
- Budget alerts and limits
- Result size constraints

**Note:** For 100GB+ production deployment, consider BigQuery/Snowflake with partitioning, materialized views, and result caching.

## 🛡️ Security Features

### Data Protection
- ✅ PII masking in logs (names, addresses, order IDs)
- ✅ API keys stored in .env (never committed)
- ✅ Local execution (data never leaves your machine)

### SQL Safety
- ✅ Only SELECT queries allowed
- ✅ SQL injection pattern detection
- ✅ Schema validation
- ✅ Dangerous keyword blocking (DROP, DELETE, etc.)
- ✅ Multi-layer validation before execution

### Error Handling
- ✅ Graceful degradation
- ✅ User-friendly error messages
- ✅ Confidence scoring for low-certainty queries
- ✅ Retry logic with exponential backoff

## 📊 Metrics & Monitoring

### Tracked Metrics

The system automatically tracks:

- **Performance**: Query latency (p50, p95, p99), SQL execution time
- **Cost**: Token usage, API costs per query
- **Quality**: Success rate, confidence scores, error rate
- **Usage**: Total queries, conversation length

### Viewing Metrics

1. **Streamlit UI**: Live metrics in sidebar
2. **CLI**: Session summary on exit
3. **Exported JSON**: `logs/metrics_<session_id>.json`

### Example Metrics Export

```json
{
  "summary": {
    "total_queries": 15,
    "success_rate": 93.3,
    "avg_latency_ms": 1247.5,
    "total_cost": 0.0456
  },
  "queries": [...]
}
```

## 🧪 Testing

The project includes a comprehensive test suite with **45 test queries** across **6 difficulty levels**.

### Run Tests

```bash
# Run all tests
pytest tests/

# Run comprehensive query tests (45 queries)
python tests/test_queries_comprehensive.py

# Test CSV flexibility (7 different formats)
python tests/test_all_csvs_summary.py

# Test security (PII protection)
python tests/test_bigquery_ai_security.py

# Test dirty data handling
python tests/test_dirty_data_fix.py

# Run with coverage
pytest --cov=src tests/
```

### Test Categories

- **EASY (8 queries)**: Basic aggregations, simple GROUP BY
- **MEDIUM (10 queries)**: Multiple filters, date operations
- **HARD (10 queries)**: Complex CTEs, window functions
- **VERY HARD (8 queries)**: Advanced analytics, cohort analysis
- **SECURITY (5 queries)**: PII validation, SQL injection prevention
- **DATA QUALITY (4 queries)**: Dirty data handling (TRY_CAST)

See test files in `tests/` directory for complete query examples.

### Manual Testing Checklist

- [ ] Upload CSV file
- [ ] Generate summary
- [ ] Ask 5+ different questions
- [ ] Test conversation memory (follow-up questions)
- [ ] Verify SQL safety (try dangerous query)
- [ ] Check metrics accuracy
- [ ] Export session metrics

## 📁 Project Structure

```
retail-insights-assistant/
├── src/                     # Source code
│   ├── agents/              # Multi-agent system (6 agents)
│   │   ├── base_agent.py                    # Base agent with Gemini integration
│   │   ├── language_to_query_agent.py       # Natural language → SQL
│   │   ├── enhanced_validation_agent.py     # PII protection & security
│   │   ├── extraction_agent.py              # SQL execution
│   │   ├── secure_insight_agent.py          # Privacy-preserving insights
│   │   └── summarization_agent.py           # Auto-summarization
│   ├── utils/               # Utility modules
│   │   ├── duckdb_manager.py               # Database management
│   │   ├── prompts.py                      # LLM prompts (with TRY_CAST)
│   │   ├── pii_detector.py                 # Column classification
│   │   ├── result_summarizer.py            # Statistics extraction
│   │   ├── universal_column_detector.py    # CSV flexibility
│   │   ├── logger.py                       # Logging
│   │   └── metrics.py                      # Performance tracking
│   ├── config.py            # Configuration management
│   ├── graph.py             # LangGraph orchestrator (RetailInsightsGraph)
│   └── main.py              # CLI interface
├── ui/
│   └── streamlit_app.py     # Streamlit web application
├── tests/                   # Comprehensive test suite
│   ├── test_queries_comprehensive.py       # 45 test queries
│   ├── test_bigquery_ai_security.py        # PII protection tests
│   ├── test_dirty_data_fix.py              # TRY_CAST validation
│   ├── test_all_csvs_summary.py            # CSV flexibility (7 formats)
│   ├── test_full_system.py                 # End-to-end tests
│   ├── test_gemini_models.py               # Multi-model fallback
│   ├── test_response_structure.py          # Output validation
│   └── test_universal_summary.py           # Universal summarization
├── requirements.txt         # Python dependencies (with versions)
├── .env.example             # Environment template
├── .gitignore               # Git exclusions
└── README.md                # This file
```

**Note:** Upload your own CSV files to analyze. The system auto-detects schemas and works with any CSV format.

## 🎯 Assignment Requirements Compliance

### ✅ Functional Requirements
- [x] Accepts CSV dataset
- [x] Summarization mode
- [x] Conversational Q&A mode
- [x] Natural language understanding

### ✅ Technical Requirements
- [x] Python implementation
- [x] Gemini API integration
- [x] Multi-agent system (6 agents, required minimum: 3)
  - [x] Language-to-Query Agent
  - [x] Data Extraction Agent
  - [x] Validation Agent
- [x] LangGraph orchestration
- [x] DuckDB data layer
- [x] Streamlit UI
- [x] Prompt engineering layer
- [x] Conversation memory
- [x] Consistent, contextual responses

### ✅ Scalability Requirements
- [x] 100GB+ architecture designed
- [x] Data engineering strategy
- [x] Storage & indexing plan
- [x] Retrieval optimization
- [x] Model orchestration
- [x] Cost & latency tracking
- [x] Monitoring & evaluation metrics

## ⚠️ Known Limitations

1. **Input Formats**: Currently only supports CSV. Excel/JSON support documented but not implemented.
2. **Vector Search**: Not implemented in current version. Documented in scaling architecture.
3. **Multi-table Joins**: Designed for single table analysis. Multi-table support requires schema extension.
4. **Real-time Data**: Batch processing only. Streaming data requires architecture changes.
5. **Authentication**: Single-user mode. Multi-tenant support requires auth layer.

## 🚀 Future Enhancements

1. **Input Flexibility**
   - Excel file support
   - JSON/text summary documents
   - Direct database connections

2. **Advanced Analytics**
   - Time series forecasting
   - Anomaly detection
   - Cohort analysis

3. **Visualization**
   - Auto-generated charts
   - Interactive dashboards
   - Export to BI tools

4. **Collaboration**
   - Multi-user support
   - Shared sessions
   - Report scheduling

5. **RAG Enhancement**
   - Vector embeddings for historical queries
   - Semantic search across conversations
   - Knowledge base integration

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
```bash
# Make sure .env file exists and contains:
GEMINI_API_KEY=your_actual_key_here
```

**"Failed to load CSV"**
- Check file path is correct
- Ensure CSV is not corrupted
- Verify sufficient disk space

**"Query validation failed"**
- The query contains unsafe operations
- Check the validation error message
- Rephrase your question more clearly

**"Low confidence score"**
- Question may be ambiguous
- Try being more specific
- Provide more context in your question

## 📞 Support

For issues or questions:
1. Check this README
2. Review logs in `logs/system.log`
3. Check exported metrics for insights

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- **LangGraph**: Multi-agent orchestration framework
- **Google Gemini**: LLM capabilities
- **DuckDB**: High-performance analytics engine
- **Streamlit**: Interactive web interface

---


*Delivered by: Manikanta Ruppa*
*Date: February 2026*
