"""
Test Universal Column Detection and Summarization on ALL Sales Dataset CSVs
"""
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.universal_column_detector import UniversalColumnDetector
from src.utils.duckdb_manager import db_manager
from src.agents.summarization_agent import SummarizationAgent
from src.utils.logger import logger


# All CSV files in Sales Dataset folder
CSV_FILES = [
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/Amazon Sale Report.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/International sale Report.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/Sale Report.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/May-2022.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/P  L March 2021.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/Cloud Warehouse Compersion Chart.csv",
    "/Users/manikanta/Desktop/Interview_prep_guide/AI Engineer/Blend/Assignment/Sales Dataset/Expense IIGF.csv",
]


def test_csv_file(csv_path: str, test_number: int, total_tests: int):
    """Test a single CSV file"""
    filename = Path(csv_path).name

    print("\n" + "=" * 80)
    print(f"TEST {test_number}/{total_tests}: {filename}")
    print("=" * 80)

    try:
        # Step 1: Load CSV preview
        print(f"\n📁 Loading CSV: {filename}")
        df = pd.read_csv(csv_path)
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")

        # Show sample data
        print(f"\n📊 Sample Data (first 3 rows, first 5 columns):")
        print(df.iloc[:3, :5].to_string())

        # Step 2: Load into DuckDB
        print(f"\n💾 Loading into DuckDB...")
        db_manager.connect()
        success = db_manager.load_csv(csv_path)

        if not success:
            print(f"   ❌ Failed to load CSV into DuckDB")
            return False

        print(f"   ✅ Loaded successfully")

        # Step 3: Get schema
        schema = db_manager.get_schema()
        print(f"\n📋 Schema ({len(schema)} columns):")
        for i, (col, dtype) in enumerate(schema.items(), 1):
            print(f"   {i:2d}. {col:30s} - {dtype}")

        # Step 4: Auto-detect columns
        print(f"\n🔍 Auto-detecting columns...")
        detected, confidence = UniversalColumnDetector.detect_columns_with_confidence(schema)

        print(f"\n✅ Detection Results:")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Categorical: {detected.get('categorical', [])[:3]}{'...' if len(detected.get('categorical', [])) > 3 else ''}")
        print(f"   Numeric:     {detected.get('numeric', [])[:3]}{'...' if len(detected.get('numeric', [])) > 3 else ''}")
        print(f"   Location:    {detected.get('location', [])[:3]}{'...' if len(detected.get('location', [])) > 3 else ''}")
        print(f"   Date:        {detected.get('date', [])[:3]}{'...' if len(detected.get('date', [])) > 3 else ''}")

        if confidence < 0.7:
            print(f"\n   ⚠️ LOW CONFIDENCE - Would ask user in production")
        else:
            print(f"\n   ✅ HIGH CONFIDENCE - Would proceed automatically")

        # Step 5: Create column mapping
        agent_mapping = {
            'categorical': detected.get('categorical', [])[0] if detected.get('categorical') else None,
            'numeric': detected.get('numeric', [])[0] if detected.get('numeric') else None,
            'location': detected.get('location', [])[0] if detected.get('location') else None,
            'date': detected.get('date', [])[0] if detected.get('date') else None,
        }

        print(f"\n📋 Selected Column Mapping:")
        print(f"   Categorical: {agent_mapping['categorical']}")
        print(f"   Numeric:     {agent_mapping['numeric']}")
        print(f"   Location:    {agent_mapping['location']}")
        print(f"   Date:        {agent_mapping['date']}")

        # Check if we have minimum required columns
        if not agent_mapping['categorical'] and not agent_mapping['numeric']:
            print(f"\n   ⚠️ SKIPPING SUMMARY - No categorical or numeric columns detected")
            return False

        # Step 6: Generate summary
        print(f"\n🤖 Generating Summary...")
        print(f"   (This may take 10-30 seconds...)")

        agent = SummarizationAgent(column_mapping=agent_mapping)
        summary, token_usage = agent.generate_summary()

        # Step 7: Display results
        print("\n" + "=" * 80)
        print("✅ SUMMARY GENERATED SUCCESSFULLY")
        print("=" * 80)
        print(f"\n{summary}")
        print("\n" + "=" * 80)
        print(f"📊 Metrics:")
        print(f"   Input tokens:  {token_usage['input_tokens']}")
        print(f"   Output tokens: {token_usage['output_tokens']}")
        print(f"   Total tokens:  {token_usage['total_tokens']}")
        print(f"   Cost:          ${token_usage.get('cost', 0):.4f}")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests on all CSV files"""
    print("\n" + "=" * 80)
    print("🚀 TESTING UNIVERSAL SUMMARIZATION ON ALL SALES DATASET CSVs")
    print("=" * 80)
    print(f"\nTotal files to test: {len(CSV_FILES)}")

    results = []

    for i, csv_path in enumerate(CSV_FILES, 1):
        success = test_csv_file(csv_path, i, len(CSV_FILES))
        filename = Path(csv_path).name
        results.append({
            'filename': filename,
            'success': success
        })

        # Small delay between tests
        if i < len(CSV_FILES):
            print("\n⏳ Waiting 2 seconds before next test...")
            import time
            time.sleep(2)

    # Final summary
    print("\n\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{i}. {result['filename']:50s} {status}")

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 80)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Universal summarization works on all CSVs!")
    elif passed > 0:
        print(f"\n⚠️ {total - passed} test(s) failed - check errors above")
    else:
        print(f"\n❌ ALL TESTS FAILED - check errors above")


if __name__ == "__main__":
    main()
