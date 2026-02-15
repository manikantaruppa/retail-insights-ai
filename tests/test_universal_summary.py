"""
Test script for Universal Column Detection and Dynamic Summarization
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.universal_column_detector import UniversalColumnDetector
from src.utils.duckdb_manager import db_manager
from src.agents.summarization_agent import SummarizationAgent
from src.utils.logger import logger


def test_column_detection():
    """Test column detection on Amazon sales data"""
    print("=" * 70)
    print("TEST 1: Column Detection")
    print("=" * 70)

    # Connect and get schema
    db_manager.connect()
    schema = db_manager.get_schema()

    print(f"\n📊 Schema: {len(schema)} columns")
    for col, dtype in list(schema.items())[:10]:
        print(f"  - {col}: {dtype}")
    print("  ...")

    # Detect columns
    print("\n🔍 Detecting columns...")
    detected, confidence = UniversalColumnDetector.detect_columns_with_confidence(schema)

    print(f"\n✅ Detection Results (Confidence: {confidence:.0%}):")
    print(f"  Categorical: {detected.get('categorical', [])}")
    print(f"  Numeric: {detected.get('numeric', [])}")
    print(f"  Location: {detected.get('location', [])}")
    print(f"  Date: {detected.get('date', [])}")

    return detected, confidence


def test_dynamic_summarization(column_mapping):
    """Test dynamic summarization with column mapping"""
    print("\n" + "=" * 70)
    print("TEST 2: Dynamic Summarization")
    print("=" * 70)

    print(f"\n📋 Column Mapping:")
    for key, value in column_mapping.items():
        if value:
            print(f"  {key}: {value[0] if isinstance(value, list) else value}")

    # Create mapping dict for agent
    agent_mapping = {
        'categorical': column_mapping.get('categorical', [])[0] if column_mapping.get('categorical') else None,
        'numeric': column_mapping.get('numeric', [])[0] if column_mapping.get('numeric') else None,
        'location': column_mapping.get('location', [])[0] if column_mapping.get('location') else None,
        'date': column_mapping.get('date', [])[0] if column_mapping.get('date') else None,
    }

    print(f"\n🤖 Creating SummarizationAgent with mapping...")
    agent = SummarizationAgent(column_mapping=agent_mapping)

    print(f"\n📊 Generating summary...")
    try:
        summary, token_usage = agent.generate_summary()

        print("\n" + "=" * 70)
        print("✅ SUMMARY GENERATED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n{summary}")
        print("\n" + "=" * 70)
        print(f"📊 Token Usage:")
        print(f"  Input: {token_usage['input_tokens']}")
        print(f"  Output: {token_usage['output_tokens']}")
        print(f"  Total: {token_usage['total_tokens']}")
        print(f"  Cost: ${token_usage.get('cost', 0):.4f}")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Summarization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests"""
    print("\n🚀 Testing Universal Column Detection & Dynamic Summarization")
    print("=" * 70)

    try:
        # Test 1: Column Detection
        detected, confidence = test_column_detection()

        if confidence < 0.7:
            print(f"\n⚠️ Low confidence ({confidence:.0%}) - would ask user in production")

        # Test 2: Dynamic Summarization
        success = test_dynamic_summarization(detected)

        if success:
            print("\n✅ All tests passed!")
            print("\n💡 Next steps:")
            print("  1. Run Streamlit: streamlit run ui/streamlit_app.py")
            print("  2. Upload CSV file")
            print("  3. Confirm column mapping (if needed)")
            print("  4. Click 'Generate Summary'")
        else:
            print("\n❌ Tests failed - check errors above")

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
