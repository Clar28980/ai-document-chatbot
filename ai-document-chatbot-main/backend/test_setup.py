#!/usr/bin/env python3
"""
Verify the AI Document Chatbot setup.
Run this after installation to check if the local environment is configured.
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return whether it succeeded."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("PASSED")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
            return True

        print("FAILED")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("TIMEOUT: command took too long")
        return False
    except Exception as exc:
        print(f"ERROR: {exc}")
        return False


def main():
    print("\n" + "=" * 60)
    print("AI Document Chatbot - Setup Verification")
    print("=" * 60)

    tests = []

    tests.append(run_command(
        "python --version",
        "Python Installation"
    ))

    tests.append(run_command(
        "python -c \"from dotenv import load_dotenv; import os; "
        "load_dotenv('backend/.env'); "
        "raise SystemExit(0 if os.getenv('ANTHROPIC_API_KEY') else 1)\"",
        "Anthropic API Key Configuration"
    ))

    tests.append(run_command(
        "python -c \"from langchain_anthropic import ChatAnthropic; "
        "print('langchain-anthropic available')\"",
        "Anthropic LangChain Dependency"
    ))

    tests.append(run_command(
        "node --version",
        "Node.js Installation"
    ))

    tests.append(run_command(
        "ng version",
        "Angular CLI Installation"
    ))

    venv_path = os.path.join("backend", "venv")
    print(f"\n{'=' * 60}")
    print("Testing: Backend Virtual Environment")
    print(f"{'=' * 60}")
    if os.path.exists(venv_path):
        print("PASSED - Virtual environment exists")
        tests.append(True)
    else:
        print("FAILED - Virtual environment not found")
        print("Run: cd backend && python -m venv venv")
        tests.append(False)

    node_modules_path = os.path.join("frontend", "node_modules")
    print(f"\n{'=' * 60}")
    print("Testing: Frontend Dependencies")
    print(f"{'=' * 60}")
    if os.path.exists(node_modules_path):
        print("PASSED - node_modules exists")
        tests.append(True)
    else:
        print("FAILED - node_modules not found")
        print("Run: cd frontend && npm install")
        tests.append(False)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(tests)
    total = len(tests)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("\nAll tests passed. Your setup is complete.")
        print("\nNext steps:")
        print("1. Confirm backend/.env contains ANTHROPIC_API_KEY")
        print("2. Optional: set ANTHROPIC_MODEL=claude-haiku-4-5-20251001")
        print("3. Start the backend: .\\start.ps1 -SkipFrontend")
        print("4. Start the frontend: .\\start.ps1 -SkipBackend")
        print("5. Open http://localhost:4200")
        return 0

    print("\nSome tests failed. Please fix the issues above.")
    print("\nCommon fixes:")
    print("- Add ANTHROPIC_API_KEY to backend/.env")
    print("- Install backend dependencies: cd backend && pip install -r requirements.txt")
    print("- Setup backend: cd backend && python -m venv venv")
    print("- Setup frontend: cd frontend && npm install")
    return 1


if __name__ == "__main__":
    sys.exit(main())
