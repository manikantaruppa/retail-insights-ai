"""
Test script to demonstrate dirty data handling with TRY_CAST
"""
from src.utils.duckdb_manager import db_manager
from src.config import Config

print("=" * 70)
print("  DIRTY DATA HANDLING TEST - CAST vs TRY_CAST")
print("=" * 70)

# Connect and load data
csv_path = Config.DATA_DIR / "Amazon Sale Report.csv"
if csv_path.exists():
    db_manager.connect()
    db_manager.load_csv(str(csv_path))

    print("\n1️⃣ Testing OLD approach (CAST) - This will FAIL:")
    print("-" * 70)

    query_old = "SELECT AVG(CAST(GROSS_AMT AS DECIMAL)) as avg_gross FROM sales"
    print(f"Query: {query_old}")

    success, results, error = db_manager.execute_query(query_old)

    if not success:
        print(f"❌ FAILED (as expected): {error[:100]}...")
    else:
        print(f"✅ Result: {results}")

    print("\n" + "=" * 70)
    print("2️⃣ Testing NEW approach (TRY_CAST) - This will SUCCEED:")
    print("-" * 70)

    query_new = "SELECT AVG(TRY_CAST(GROSS_AMT AS DECIMAL)) as avg_gross FROM sales"
    print(f"Query: {query_new}")

    success, results, error = db_manager.execute_query(query_new)

    if success:
        print(f"✅ SUCCESS!")
        print(f"Result: {results}")
        print(f"\nAverage Gross Amount: ₹{results[0]['avg_gross']:.2f}")
    else:
        print(f"❌ Failed: {error}")

    print("\n" + "=" * 70)
    print("3️⃣ Understanding the data:")
    print("-" * 70)

    # Check what non-numeric values exist
    query_check = """
    SELECT GROSS_AMT, COUNT(*) as count
    FROM sales
    WHERE TRY_CAST(GROSS_AMT AS DECIMAL) IS NULL
      AND GROSS_AMT IS NOT NULL
    GROUP BY GROSS_AMT
    ORDER BY count DESC
    LIMIT 5
    """
    print(f"Query: Checking non-numeric values in GROSS_AMT...")

    success, results, error = db_manager.execute_query(query_check)

    if success and results:
        print(f"\n📊 Non-numeric values found:")
        for row in results:
            print(f"  '{row['GROSS_AMT']}' appears {row['count']} times")

    # Show stats
    query_stats = """
    SELECT
        COUNT(*) as total_rows,
        COUNT(TRY_CAST(GROSS_AMT AS DECIMAL)) as valid_numeric_rows,
        COUNT(*) - COUNT(TRY_CAST(GROSS_AMT AS DECIMAL)) as invalid_rows,
        ROUND(100.0 * COUNT(TRY_CAST(GROSS_AMT AS DECIMAL)) / COUNT(*), 2) as valid_percentage
    FROM sales
    """

    success, results, error = db_manager.execute_query(query_stats)

    if success and results:
        stats = results[0]
        print(f"\n📈 Data Quality Stats:")
        print(f"  Total rows: {stats['total_rows']:,}")
        print(f"  Valid numeric: {stats['valid_numeric_rows']:,}")
        print(f"  Invalid (skipped): {stats['invalid_rows']:,}")
        print(f"  Data quality: {stats['valid_percentage']}%")

    print("\n" + "=" * 70)
    print("✅ SOLUTION IMPLEMENTED")
    print("=" * 70)
    print("""
The SQL generation prompt has been updated to:
1. Use TRY_CAST() instead of CAST() for all numeric conversions
2. This handles dirty data gracefully (returns NULL for invalid values)
3. Aggregate functions (AVG, SUM) automatically ignore NULLs
4. Your query will now work without errors!

Next time you ask "What is the average gross amount?",
the system will generate: SELECT AVG(TRY_CAST(GROSS_AMT AS DECIMAL)) ...
                          ^^^^^^^^^ This won't fail on "Stock" or other text values
""")

    print("\n🧪 Now try your original query again in the UI!")
    print("   Query: 'what is the average of gross amount in this data'")
    print("   Expected: Should work and return average excluding invalid values")

else:
    print(f"❌ CSV file not found: {csv_path}")
