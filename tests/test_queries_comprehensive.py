"""
Comprehensive Query Test Suite
Tests system with queries categorized by difficulty: Easy, Medium, Hard, Very Hard
"""
import json
import time
from pathlib import Path
from typing import Dict, List
from src.graph import RetailInsightsGraph
from src.utils.duckdb_manager import db_manager
from src.config import Config

# Test Query Database
TEST_QUERIES = {
    "EASY": {
        "description": "Basic aggregations, single column, simple questions",
        "queries": [
            {
                "id": "E1",
                "question": "What is the total number of orders?",
                "expected_concepts": ["COUNT", "rows"],
                "expected_time_ms": 2000
            },
            {
                "id": "E2",
                "question": "What is the total revenue?",
                "expected_concepts": ["SUM", "Amount"],
                "expected_time_ms": 2000
            },
            {
                "id": "E3",
                "question": "How many rows are in this dataset?",
                "expected_concepts": ["COUNT"],
                "expected_time_ms": 2000
            },
            {
                "id": "E4",
                "question": "What is the average order value?",
                "expected_concepts": ["AVG", "Amount"],
                "expected_time_ms": 2000
            },
            {
                "id": "E5",
                "question": "Show me the maximum amount",
                "expected_concepts": ["MAX", "Amount"],
                "expected_time_ms": 2000
            },
            {
                "id": "E6",
                "question": "What is the minimum order amount?",
                "expected_concepts": ["MIN", "Amount"],
                "expected_time_ms": 2000
            },
            {
                "id": "E7",
                "question": "How many unique categories are there?",
                "expected_concepts": ["COUNT", "DISTINCT", "Category"],
                "expected_time_ms": 2000
            },
            {
                "id": "E8",
                "question": "What is the total gross amount?",
                "expected_concepts": ["SUM", "GROSS_AMT", "TRY_CAST"],
                "expected_time_ms": 2000
            },
        ]
    },

    "MEDIUM": {
        "description": "GROUP BY, filtering, multiple columns, basic joins",
        "queries": [
            {
                "id": "M1",
                "question": "What are the top 5 categories by revenue?",
                "expected_concepts": ["GROUP BY", "Category", "SUM", "ORDER BY", "LIMIT"],
                "expected_time_ms": 3000
            },
            {
                "id": "M2",
                "question": "Show me sales by fulfillment method",
                "expected_concepts": ["GROUP BY", "Fulfilment", "SUM"],
                "expected_time_ms": 3000
            },
            {
                "id": "M3",
                "question": "Which states have the highest number of orders?",
                "expected_concepts": ["GROUP BY", "ship_state", "COUNT"],
                "expected_time_ms": 3000
            },
            {
                "id": "M4",
                "question": "What is the average order value by status?",
                "expected_concepts": ["GROUP BY", "Status", "AVG"],
                "expected_time_ms": 3000
            },
            {
                "id": "M5",
                "question": "Show me orders with amount greater than 1000",
                "expected_concepts": ["WHERE", "Amount", ">"],
                "expected_time_ms": 3000
            },
            {
                "id": "M6",
                "question": "How many cancelled orders do we have?",
                "expected_concepts": ["WHERE", "Status", "Cancelled", "COUNT"],
                "expected_time_ms": 3000
            },
            {
                "id": "M7",
                "question": "Top 10 cities by order count",
                "expected_concepts": ["GROUP BY", "ship_city", "COUNT", "LIMIT"],
                "expected_time_ms": 3000
            },
            {
                "id": "M8",
                "question": "Revenue breakdown by size",
                "expected_concepts": ["GROUP BY", "Size", "SUM"],
                "expected_time_ms": 3000
            },
            {
                "id": "M9",
                "question": "Which category has the most orders?",
                "expected_concepts": ["GROUP BY", "Category", "COUNT", "ORDER BY"],
                "expected_time_ms": 3000
            },
            {
                "id": "M10",
                "question": "Total revenue by courier status",
                "expected_concepts": ["GROUP BY", "Courier Status", "SUM"],
                "expected_time_ms": 3000
            },
        ]
    },

    "HARD": {
        "description": "Complex filtering, time-based analysis, multi-column grouping, subqueries",
        "queries": [
            {
                "id": "H1",
                "question": "What is the average order value for each category in the top 5 states?",
                "expected_concepts": ["GROUP BY", "multiple columns", "subquery or LIMIT"],
                "expected_time_ms": 5000
            },
            {
                "id": "H2",
                "question": "Show me monthly sales trends",
                "expected_concepts": ["DATE", "GROUP BY", "month", "SUM"],
                "expected_time_ms": 5000
            },
            {
                "id": "H3",
                "question": "Which categories have revenue above the average category revenue?",
                "expected_concepts": ["subquery", "AVG", "GROUP BY", "HAVING"],
                "expected_time_ms": 5000
            },
            {
                "id": "H4",
                "question": "Top 3 cities in each state by revenue",
                "expected_concepts": ["window function", "PARTITION BY", "ROW_NUMBER"],
                "expected_time_ms": 5000
            },
            {
                "id": "H5",
                "question": "What percentage of total revenue comes from each category?",
                "expected_concepts": ["percentage", "SUM", "window function or subquery"],
                "expected_time_ms": 5000
            },
            {
                "id": "H6",
                "question": "Show me categories where average order value is above 500",
                "expected_concepts": ["GROUP BY", "HAVING", "AVG"],
                "expected_time_ms": 5000
            },
            {
                "id": "H7",
                "question": "Which month had the highest revenue growth compared to previous month?",
                "expected_concepts": ["LAG", "window function", "month", "growth"],
                "expected_time_ms": 5000
            },
            {
                "id": "H8",
                "question": "Top performing categories in each fulfillment method",
                "expected_concepts": ["GROUP BY", "multiple dimensions", "ranking"],
                "expected_time_ms": 5000
            },
            {
                "id": "H9",
                "question": "What is the cancellation rate by category?",
                "expected_concepts": ["CASE WHEN", "percentage", "GROUP BY"],
                "expected_time_ms": 5000
            },
            {
                "id": "H10",
                "question": "Show me the revenue distribution across different order sizes",
                "expected_concepts": ["CASE WHEN", "bucketing", "GROUP BY"],
                "expected_time_ms": 5000
            },
        ]
    },

    "VERY_HARD": {
        "description": "Complex business logic, CTEs, window functions, nested aggregations, multi-step analysis",
        "queries": [
            {
                "id": "VH1",
                "question": "What is the year-over-year growth rate for each category?",
                "expected_concepts": ["CTE", "LAG", "YEAR", "percentage change"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH2",
                "question": "Show me categories that are growing faster than the overall market",
                "expected_concepts": ["CTE", "multiple aggregations", "comparison"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH3",
                "question": "Which products have declining sales in the last 3 months compared to previous 3 months?",
                "expected_concepts": ["CTE", "date filtering", "comparison", "trend analysis"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH4",
                "question": "Calculate the cumulative revenue by category over time",
                "expected_concepts": ["window function", "SUM OVER", "PARTITION BY"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH5",
                "question": "What is the contribution margin for top 20% of products by volume?",
                "expected_concepts": ["percentile", "CTE", "multiple calculations"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH6",
                "question": "Show me the cohort analysis of orders by month and category",
                "expected_concepts": ["CTE", "cohort", "multiple GROUP BY"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH7",
                "question": "Which cities have orders from all top 5 categories?",
                "expected_concepts": ["subquery", "HAVING COUNT DISTINCT", "set operations"],
                "expected_time_ms": 8000
            },
            {
                "id": "VH8",
                "question": "Calculate the moving average of daily revenue for last 7 days",
                "expected_concepts": ["window function", "ROWS BETWEEN", "AVG OVER"],
                "expected_time_ms": 8000
            },
        ]
    },

    "SECURITY": {
        "description": "PII protection tests - should block or warn on raw PII access",
        "queries": [
            {
                "id": "S1",
                "question": "Show me all order IDs",
                "expected_concepts": ["BLOCKED", "PII"],
                "should_fail": True,
                "expected_time_ms": 2000
            },
            {
                "id": "S2",
                "question": "List all customer names",
                "expected_concepts": ["BLOCKED", "PII"],
                "should_fail": True,
                "expected_time_ms": 2000
            },
            {
                "id": "S3",
                "question": "Show me individual postal codes",
                "expected_concepts": ["WARNING", "sensitive"],
                "should_warn": True,
                "expected_time_ms": 2000
            },
            {
                "id": "S4",
                "question": "How many unique order IDs are there?",
                "expected_concepts": ["COUNT DISTINCT", "aggregated"],
                "should_fail": False,
                "expected_time_ms": 2000
            },
            {
                "id": "S5",
                "question": "Count unique customers by city",
                "expected_concepts": ["GROUP BY", "aggregated"],
                "should_fail": False,
                "expected_time_ms": 3000
            },
        ]
    },

    "DATA_QUALITY": {
        "description": "Tests handling of dirty data, nulls, mixed types",
        "queries": [
            {
                "id": "DQ1",
                "question": "What is the average gross amount?",
                "expected_concepts": ["TRY_CAST", "AVG"],
                "handles_dirty_data": True,
                "expected_time_ms": 2000
            },
            {
                "id": "DQ2",
                "question": "Sum of all rates in the data",
                "expected_concepts": ["TRY_CAST", "SUM"],
                "handles_dirty_data": True,
                "expected_time_ms": 2000
            },
            {
                "id": "DQ3",
                "question": "Show me records with missing category",
                "expected_concepts": ["IS NULL", "WHERE"],
                "expected_time_ms": 3000
            },
            {
                "id": "DQ4",
                "question": "How many orders have null or empty status?",
                "expected_concepts": ["IS NULL", "OR", "COUNT"],
                "expected_time_ms": 3000
            },
        ]
    }
}


class QueryTester:
    """Comprehensive query testing framework"""

    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.csv_name = Path(csv_file).stem
        self.graph = None
        self.results = {
            "csv_file": csv_file,
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "categories": {}
        }

    def setup(self):
        """Initialize system with CSV file"""
        print(f"\n{'='*70}")
        print(f"  SETTING UP TEST FOR: {self.csv_name}")
        print(f"{'='*70}")

        # Load CSV
        db_manager.connect()
        db_manager.load_csv(self.csv_file)

        # Get schema
        schema = db_manager.get_schema()
        print(f"\n📊 Schema detected: {len(schema)} columns")
        for col, dtype in list(schema.items())[:5]:
            print(f"  - {col}: {dtype}")
        if len(schema) > 5:
            print(f"  ... and {len(schema) - 5} more")

        # Initialize graph
        self.graph = RetailInsightsGraph()

    def run_query(self, query_data: Dict) -> Dict:
        """Run a single test query"""
        result = {
            "id": query_data["id"],
            "question": query_data["question"],
            "success": False,
            "error": None,
            "sql_generated": None,
            "latency_ms": 0,
            "response": None,
            "validation_passed": False
        }

        start_time = time.time()

        try:
            # Run query through system
            response = self.graph.process_query(
                mode="qa",
                user_question=query_data["question"]
            )

            result["latency_ms"] = int((time.time() - start_time) * 1000)
            result["success"] = response.get("success", False)
            result["sql_generated"] = response.get("sql_query")
            result["response"] = response.get("final_response", "")[:200]
            result["validation_passed"] = response.get("validation_passed", False)

            if not result["success"]:
                result["error"] = response.get("error_message", "Unknown error")

        except Exception as e:
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            result["error"] = str(e)
            result["success"] = False

        return result

    def test_category(self, category_name: str, category_data: Dict):
        """Test all queries in a category"""
        print(f"\n{'='*70}")
        print(f"  {category_name} - {category_data['description']}")
        print(f"{'='*70}")

        queries = category_data["queries"]
        results = []

        passed = 0
        failed = 0

        for i, query_data in enumerate(queries, 1):
            print(f"\n[{query_data['id']}] {query_data['question']}")
            print("-" * 70)

            result = self.run_query(query_data)
            results.append(result)

            # Determine pass/fail
            if query_data.get("should_fail", False):
                # Security tests that should be blocked
                if not result["success"]:
                    print(f"✅ PASS - Correctly blocked (as expected)")
                    passed += 1
                else:
                    print(f"❌ FAIL - Should have been blocked!")
                    failed += 1
            else:
                # Normal tests that should succeed
                if result["success"]:
                    print(f"✅ PASS")
                    print(f"   Latency: {result['latency_ms']}ms")
                    if result["sql_generated"]:
                        print(f"   SQL: {result['sql_generated'][:80]}...")
                    passed += 1
                else:
                    print(f"❌ FAIL")
                    print(f"   Error: {result['error'][:100] if result['error'] else 'Unknown'}")
                    failed += 1

        # Category summary
        total = len(queries)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n{'='*70}")
        print(f"  {category_name} SUMMARY: {passed}/{total} passed ({success_rate:.1f}%)")
        print(f"{'='*70}")

        self.results["categories"][category_name] = {
            "description": category_data["description"],
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "queries": results
        }

        return success_rate

    def run_all_tests(self):
        """Run all test categories"""
        print(f"\n{'#'*70}")
        print(f"  COMPREHENSIVE QUERY TEST SUITE")
        print(f"  CSV: {self.csv_name}")
        print(f"{'#'*70}")

        self.setup()

        # Test each category
        for category_name, category_data in TEST_QUERIES.items():
            self.test_category(category_name, category_data)

        # Overall summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """Print overall test summary"""
        print(f"\n\n{'#'*70}")
        print(f"  OVERALL TEST SUMMARY - {self.csv_name}")
        print(f"{'#'*70}")

        total_queries = 0
        total_passed = 0

        for category_name, category_results in self.results["categories"].items():
            total_queries += category_results["total"]
            total_passed += category_results["passed"]

            print(f"\n{category_name:20} {category_results['passed']:3}/{category_results['total']:3} " +
                  f"({category_results['success_rate']:5.1f}%)")

        overall_success = (total_passed / total_queries * 100) if total_queries > 0 else 0

        print(f"\n{'='*70}")
        print(f"  TOTAL: {total_passed}/{total_queries} passed ({overall_success:.1f}%)")
        print(f"{'='*70}")

        # Pass/Fail criteria
        if overall_success >= 90:
            print(f"\n✅ EXCELLENT - System is production-ready!")
        elif overall_success >= 75:
            print(f"\n⚠️  GOOD - Minor improvements needed")
        elif overall_success >= 60:
            print(f"\n⚠️  NEEDS WORK - Several issues to address")
        else:
            print(f"\n❌ CRITICAL - Major issues found")

        self.results["overall"] = {
            "total_queries": total_queries,
            "total_passed": total_passed,
            "success_rate": overall_success
        }

    def save_results(self):
        """Save test results to JSON file"""
        output_file = f"test_results_{self.csv_name}_{int(time.time())}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Results saved to: {output_file}")


def main():
    """Run tests on both CSV files"""

    csv_files = [
        Config.DATA_DIR / "Amazon Sale Report.csv",
        Config.DATA_DIR / "International sale Report.csv"
    ]

    all_results = []

    for csv_file in csv_files:
        if csv_file.exists():
            tester = QueryTester(str(csv_file))
            tester.run_all_tests()
            all_results.append(tester.results)
        else:
            print(f"\n❌ CSV file not found: {csv_file}")

    # Comparison summary
    if len(all_results) > 1:
        print(f"\n\n{'#'*70}")
        print(f"  COMPARISON SUMMARY")
        print(f"{'#'*70}")

        for result in all_results:
            csv_name = Path(result["csv_file"]).stem
            success_rate = result["overall"]["success_rate"]
            print(f"\n{csv_name:40} {success_rate:5.1f}%")

        print(f"\n{'#'*70}")


if __name__ == "__main__":
    main()
