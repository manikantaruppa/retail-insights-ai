"""
Main CLI interface for Retail Insights Assistant
"""
import sys
import uuid
from pathlib import Path
from src.graph import insights_graph
from src.utils.duckdb_manager import db_manager
from src.utils.metrics import metrics_tracker
from src.utils.logger import logger
from src.config import Config


def main():
    """Main CLI interface"""
    print("=" * 60)
    print("      Retail Insights Assistant - CLI Mode")
    print("=" * 60)
    print()

    # Start session
    session_id = str(uuid.uuid4())[:8]
    metrics_tracker.start_session(session_id)
    logger.info(f"Started CLI session: {session_id}")

    # Load CSV file
    csv_path = input("Enter path to CSV file: ").strip()

    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return

    print(f"\n📁 Loading {csv_path}...")

    try:
        db_manager.connect()
        success = db_manager.load_csv(csv_path)

        if not success:
            print("❌ Failed to load CSV file")
            return

        print("✅ CSV loaded successfully")

        # Show data info
        stats = db_manager.get_table_stats()
        print(f"\n📊 Dataset Info:")
        print(f"   - Total Rows: {stats.get('total_rows', 0):,}")
        print(f"   - Columns: {stats.get('column_count', 0)}")

        if stats.get('date_range'):
            print(f"   - Date Range: {stats['date_range'].get('min')} to {stats['date_range'].get('max')}")

    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # Main loop
    print("\n" + "=" * 60)
    print("Choose mode:")
    print("1. Generate automatic summary")
    print("2. Ask questions (Q&A mode)")
    print("3. Exit")
    print("=" * 60)

    conversation_history = []

    while True:
        print()
        choice = input("Enter choice (1-3): ").strip()

        if choice == '1':
            # Summarization mode
            print("\n🔄 Generating summary...")
            try:
                result = insights_graph.process_query(mode="summarization")

                print("\n" + "=" * 60)
                print("📊 EXECUTIVE SUMMARY")
                print("=" * 60)
                print(result["response"])
                print("=" * 60)

                if result["success"]:
                    print(f"\n✅ Summary generated successfully")
                    print(f"   - Tokens used: {result['token_usage']['total_tokens']}")
                else:
                    print(f"\n⚠️ Summary generated with warnings")

            except Exception as e:
                print(f"\n❌ Error: {e}")

        elif choice == '2':
            # Q&A mode
            print("\n💬 Q&A Mode (type 'back' to return to menu)")
            print("-" * 60)

            while True:
                question = input("\nYour question: ").strip()

                if question.lower() == 'back':
                    break

                if not question:
                    continue

                print("\n🔄 Processing...")

                try:
                    result = insights_graph.process_query(
                        mode="qa",
                        user_question=question,
                        conversation_history=conversation_history
                    )

                    # Add to history
                    conversation_history.append({
                        "role": "user",
                        "content": question
                    })
                    conversation_history.append({
                        "role": "assistant",
                        "content": result["response"]
                    })

                    print("\n" + "-" * 60)
                    print("🤖 Answer:")
                    print("-" * 60)
                    print(result["response"])
                    print("-" * 60)

                    if result.get("sql_query"):
                        print(f"\n🔍 SQL Query:")
                        print(result["sql_query"])

                    if result.get("confidence_score") is not None:
                        confidence = result["confidence_score"]
                        emoji = "✅" if confidence >= 0.8 else "⚠️" if confidence >= 0.6 else "❌"
                        print(f"\n{emoji} Confidence: {confidence:.0%}")

                    print(f"\n📊 Metrics:")
                    print(f"   - Rows scanned: {result.get('rows_scanned', 0):,}")
                    print(f"   - Tokens used: {result['token_usage']['total_tokens']}")

                except Exception as e:
                    print(f"\n❌ Error: {e}")

        elif choice == '3':
            # Exit
            print("\n👋 Exiting...")

            # Export metrics
            print("💾 Exporting metrics...")
            metrics_tracker.export_session()

            # Show session summary
            summary = metrics_tracker.get_session_summary()
            print(f"\n📊 Session Summary:")
            print(f"   - Total queries: {summary.get('total_queries', 0)}")
            print(f"   - Success rate: {summary.get('success_rate', 0):.1f}%")
            print(f"   - Total cost: ${summary.get('total_cost', 0):.4f}")
            print(f"   - Avg latency: {summary.get('avg_latency_ms', 0):.0f} ms")

            print("\n✅ Metrics saved to logs/")
            print("\nThank you for using Retail Insights Assistant!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
