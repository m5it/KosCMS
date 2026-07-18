#!/usr/bin/env python3
"""
WebCMS Admin Panel Test Runner

Runs all tests including:
- Unit tests (unittest)
- End-to-end tests
- Integration tests
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*70)
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} PASSED")
        return True
    else:
        print(f"❌ {description} FAILED")
        return False


def main():
    """Run all tests."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           WebCMS Admin Panel Test Suite                              ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    tests = [
        ("python3 tests/test_admin_unittest.py", 
         "Unit Tests (unittest)"),
        ("python3 test_admin_e2e.py", 
         "End-to-End Tests"),
        ("python3 -c \"from webcms.app_factory import create_app; app = create_app(); print('✅ App creates successfully')\"", 
         "Application Startup"),
        ("python3 -c \"from webcms.admin.admin_api import AdminAPI; api = AdminAPI(None, None); print('✅ Admin API imports successfully')\"", 
         "Admin API Import"),
        ("python3 -c \"from webcms.admin.logging_middleware import AdminLogger; logger = AdminLogger(); print('✅ Logging middleware works')\"", 
         "Logging Middleware"),
    ]
    
    results = []
    
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print('='*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {desc}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} test suites passed")
    print('='*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
