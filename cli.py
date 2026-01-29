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

    # Make URL optional and add ZIP/HTML file option
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "url",
        nargs="?",
        help="Manhwa chapter URL to translate"
    )
    input_group.add_argument(
        "--zip",
        type=str,
        help="Path to ZIP file containing HTML and images"
    )
    input_group.add_argument(
        "--html",
        type=str,
        help="Path to HTML file (images must be in same folder)"
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

    # Validate input
    if not args.url and not args.html and not args.zip:
        parser.error("Provide a URL, --html, or --zip")

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

    # Handle ZIP extraction
    html_path = None
    if args.zip:
        import zipfile
        import tempfile

        zip_path = Path(args.zip)
        if not zip_path.exists():
            print(f"Error: ZIP file not found: {zip_path}", file=sys.stderr)
            sys.exit(1)

        # Extract to temp directory
        temp_dir = Path(tempfile.gettempdir()) / "manhwa_cli" / zip_path.stem
        temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"Extracting ZIP: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find HTML file
        html_files = list(temp_dir.glob("**/*.html")) + list(temp_dir.glob("**/*.htm"))
        if not html_files:
            print("Error: No HTML file found in ZIP", file=sys.stderr)
            sys.exit(1)

        html_path = html_files[0]
        print(f"Found HTML: {html_path}")

    elif args.html:
        html_path = Path(args.html)
        if not html_path.exists():
            print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
            sys.exit(1)

    # Create and run pipeline
    if args.url:
        print(f"Starting translation pipeline for URL: {args.url}")
    else:
        print(f"Starting translation pipeline for HTML: {html_path}")

    print(f"Workspace: {config.workspace_dir}")

    pipeline = Pipeline(config)

    # Set up progress callback
    def print_progress(state):
        print(f"[{state.current_stage.value}] {state.progress:.0f}% - {state.message}")

    pipeline.set_progress_callback(print_progress)

    # Run pipeline
    if args.url:
        result = pipeline.run(url=args.url)
    else:
        result = pipeline.run(html_path=html_path)

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
