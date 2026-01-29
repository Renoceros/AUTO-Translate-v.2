"""Test installation and configuration."""
import sys
from pathlib import Path


def test_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False


def test_imports():
    """Test critical imports."""
    print("\nTesting imports...")

    required_packages = {
        "streamlit": "Streamlit",
        "playwright": "Playwright",
        "PIL": "Pillow",
        "cv2": "OpenCV",
        "anthropic": "Anthropic",
        "yaml": "PyYAML",
        "dotenv": "python-dotenv",
        "pydantic": "Pydantic",
        "numpy": "NumPy",
    }

    all_ok = True
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - run: pip install {name.lower()}")
            all_ok = False

    return all_ok


def test_ocr_engines():
    """Test OCR engines."""
    print("\nTesting OCR engines...")

    # PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("✓ PaddleOCR")
        paddle_ok = True
    except ImportError:
        print("✗ PaddleOCR - run: pip install paddleocr")
        paddle_ok = False

    # EasyOCR
    try:
        import easyocr
        print("✓ EasyOCR")
        easy_ok = True
    except ImportError:
        print("✗ EasyOCR - run: pip install easyocr")
        easy_ok = False

    return paddle_ok or easy_ok  # At least one should work


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")

    # Check config.yaml
    if Path("config.yaml").exists():
        print("✓ config.yaml exists")
    else:
        print("✗ config.yaml missing")
        return False

    # Check .env
    if Path(".env").exists():
        print("✓ .env exists")

        # Try to load API key
        from dotenv import load_dotenv
        import os

        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            print(f"✓ ANTHROPIC_API_KEY set (length: {len(api_key)})")
        else:
            print("✗ ANTHROPIC_API_KEY not set in .env")
            return False
    else:
        print("✗ .env missing - copy .env.example to .env and add your API key")
        return False

    return True


def test_playwright():
    """Test Playwright installation."""
    print("\nTesting Playwright browsers...")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✓ Playwright Chromium installed")
                return True
            except Exception as e:
                print(f"✗ Playwright Chromium not installed")
                print("  Run: playwright install chromium")
                return False

    except Exception as e:
        print(f"✗ Playwright error: {e}")
        return False


def test_workspace():
    """Test workspace directory."""
    print("\nTesting workspace...")

    workspace = Path("workspace")
    if workspace.exists():
        print("✓ workspace directory exists")
    else:
        print("ℹ workspace will be created on first run")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("AUTO-Translate v.2 - Installation Test")
    print("=" * 60)

    results = []

    results.append(("Python Version", test_python_version()))
    results.append(("Python Packages", test_imports()))
    results.append(("OCR Engines", test_ocr_engines()))
    results.append(("Configuration", test_config()))
    results.append(("Playwright", test_playwright()))
    results.append(("Workspace", test_workspace()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)

    if all_passed:
        print("✓ All tests passed! You're ready to use AUTO-Translate v.2")
        print("\nNext steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Or:  python cli.py <manhwa-url>")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Install Playwright: playwright install chromium")
        print("  - Create .env file with ANTHROPIC_API_KEY")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
