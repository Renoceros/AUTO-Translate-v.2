"""CLI entry point for pipeline."""
import argparse
import sys
from pathlib import Path

from src.config import Config
from src.pipeline import Pipeline


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AUTO-Translate v.2 - Automated Manhwa Translation System"
    )
    parser.add_argument(
        "url",
        help="Manhwa chapter URL to translate"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = Config.load(args.config)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("Please create a .env file with your ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    # Override debug mode if specified
    if args.debug:
        config.debug.debug_mode = True

    # Create and run pipeline
    print(f"Starting translation pipeline for: {args.url}")
    print(f"Workspace: {config.workspace_dir}")

    pipeline = Pipeline(config)

    # Set up progress callback
    def print_progress(state):
        print(f"[{state.current_stage.value}] {state.progress:.0f}% - {state.message}")

    pipeline.set_progress_callback(print_progress)

    # Run pipeline
    result = pipeline.run(args.url)

    if result["status"] == "success":
        print("\n✓ Translation complete!")

        final_paths = result["artifacts"].get("final_paths", [])
        print(f"\nGenerated {len(final_paths)} translated pages:")
        for path in final_paths:
            print(f"  - {path}")

        print(f"\nAll artifacts saved to: {config.workspace_dir}")

    else:
        print(f"\n✗ Translation failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
