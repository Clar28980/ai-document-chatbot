#!/usr/bin/env python3
"""
Test script to verify the AI Document Chatbot setup.
Run this after installation to check if everything is configured correctly.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
            return True
        else:
            print("❌ FAILED")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏱️  TIMEOUT (command took too long)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("AI Document Chatbot - Setup Verification")
    print("="*60)
    
    tests = []
    
    # Test 1: Python version
    tests.append(run_command(
        "python --version",
        "Python Installation"
    ))
    
    # Test 2: Check Ollama
    tests.append(run_command(
        "ollama --version",
        "Ollama Installation"
    ))
    
    # Test 3: Check if LLaMA 3 is available
    tests.append(run_command(
        "ollama list | findstr llama3",
        "LLaMA 3 Model Available"
    ))
    
    # Test 4: Check Node.js
    tests.append(run_command(
        "node --version",
        "Node.js Installation"
    ))
    
    # Test 5: Check Angular CLI
    tests.append(run_command(
        "ng version",
        "Angular CLI Installation"
    ))
    
    # Test 6: Check backend virtual environment
    venv_path = os.path.join("backend", "venv")
    if os.path.exists(venv_path):
        print(f"\n{'='*60}")
        print("Testing: Backend Virtual Environment")
        print(f"{'='*60}")
        print("✅ PASSED - Virtual environment exists")
        tests.append(True)
    else:
        print(f"\n{'='*60}")
        print("Testing: Backend Virtual Environment")
        print(f"{'='*60}")
        print("❌ FAILED - Virtual environment not found")
        print("   Run: cd backend && python -m venv venv")
        tests.append(False)
    
    # Test 7: Check frontend dependencies
    node_modules_path = os.path.join("frontend", "node_modules")
    if os.path.exists(node_modules_path):
        print(f"\n{'='*60}")
        print("Testing: Frontend Dependencies")
        print(f"{'='*60}")
        print("✅ PASSED - node_modules exists")
        tests.append(True)
    else:
        print(f"\n{'='*60}")
        print("Testing: Frontend Dependencies")
        print(f"{'='*60}")
        print("❌ FAILED - node_modules not found")
        print("   Run: cd frontend && npm install")
        tests.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is complete.")
        print("\nNext steps:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Start the backend: .\\start.ps1 -SkipFrontend")
        print("3. Start the frontend: .\\start.ps1 -SkipBackend")
        print("4. Open http://localhost:4200")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install Ollama: https://ollama.com")
        print("- Pull LLaMA 3: ollama pull llama3")
        print("- Setup backend: cd backend && python -m venv venv")
        print("- Setup frontend: cd frontend && npm install")
        return 1

if __name__ == "__main__":
    sys.exit(main())
