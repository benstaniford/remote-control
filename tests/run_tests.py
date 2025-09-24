#!/usr/bin/env python3
"""
Test Runner Script

This script runs all test files in the tests directory and provides
a summary of results.
"""

import sys
import os
import subprocess
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_file: str) -> Tuple[str, bool, str]:
    """
    Run a single test file and return results.
    
    Args:
        test_file: Path to the test file
        
    Returns:
        Tuple of (test_name, success, output)
    """
    test_name = os.path.basename(test_file).replace('.py', '').replace('test_', '')
    
    try:
        print(f"\n{'='*60}")
        print(f"Running {test_name.upper()} tests...")
        print('='*60)
        
        result = subprocess.run(
            [sys.executable, test_file], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        
        print(output)
        
        success = result.returncode == 0
        return test_name, success, output
        
    except subprocess.TimeoutExpired:
        error_msg = f"Test {test_name} timed out after 60 seconds"
        print(error_msg)
        return test_name, False, error_msg
    except Exception as e:
        error_msg = f"Error running test {test_name}: {e}"
        print(error_msg)
        return test_name, False, error_msg

def main():
    """Main test runner."""
    print("Remote Control Test Suite")
    print("=" * 60)
    
    # Find all test files
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        os.path.join(test_dir, f) for f in os.listdir(test_dir)
        if f.startswith('test_') and f.endswith('.py') and f != 'run_tests.py'
    ]
    
    if not test_files:
        print("No test files found!")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {os.path.basename(test_file)}")
    
    # Run all tests
    results: List[Tuple[str, bool, str]] = []
    
    for test_file in sorted(test_files):
        test_name, success, output = run_test(test_file)
        results.append((test_name, success, output))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, _ in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:<8} {test_name}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error in test runner: {e}")
        sys.exit(1)