#!/usr/bin/env python3
"""
Final Verification Script

Verifies all project components are working correctly
"""

import sys
import os
import subprocess

sys.path.insert(0, '.')


def check_imports():
    """Check all modules can be imported."""
    print("Checking imports...")
    
    modules = [
        'webcms.admin.admin_api',
        'webcms.admin.logging_middleware',
        'webcms.admin.performance_monitor',
        'webcms.admin.rate_limiter',
        'webcms.admin.validators',
        'webcms.admin.data_import_export',
        'webcms.admin.webhooks',
        'webcms.admin.scheduler',
        'webcms.cache.manager',
        'webcms.cli',
        'webcms.client',
        'webcms.health',
        'webcms.i18n',
        'webcms.api_versioning',
        'webcms.migrations',
        'webcms.graphql_api',
        'webcms.content_versioning',
        'webcms.realtime',
        'webcms.advanced_search',
        'webcms.email_templates',
        'webcms.analytics',
        'webcms.dev_tools',
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0, failed


def check_features():
    """Check key features work."""
    print("\nChecking features...")
    
    from webcms.admin.admin_api import AdminAPI
    from webcms.health import health
    from webcms.i18n import i18n
    from webcms.graphql_api import execute_graphql
    from webcms.client import WebCMSAdminClient
    
    checks = []
    
    # Check AdminAPI
    try:
        api = AdminAPI(db=None, auth=None)
        checks.append(("AdminAPI creation", True))
    except Exception as e:
        checks.append(("AdminAPI creation", False, str(e)))
    
    # Check health
    try:
        response = health.get_status()
        checks.append(("Health check", hasattr(response, 'status') and response.status == 200))
    except Exception as e:
        checks.append(("Health check", False, str(e)))
    
    # Check i18n
    try:
        result = i18n.t('common.save')
        checks.append(("I18n", result == 'Save'))
    except Exception as e:
        checks.append(("I18n", False, str(e)))
    
    # Check GraphQL
    try:
        result = execute_graphql('{ users { id } }')
        checks.append(("GraphQL", 'data' in result))
    except Exception as e:
        checks.append(("GraphQL", False, str(e)))
    
    # Check SDK
    try:
        client = WebCMSAdminClient(base_url='http://localhost:5000', api_key='test')
        checks.append(("SDK Client", True))
    except Exception as e:
        checks.append(("SDK Client", False, str(e)))
    
    for check in checks:
        name = check[0]
        passed = check[1]
        error = check[2] if len(check) > 2 else None
        
        if passed:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}: {error}")
    
    return all(c[1] for c in checks)


def run_tests():
    """Run all tests."""
    print("\nRunning tests...")
    
    test_files = [
        'tests/test_simple.py',
    ]
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                result = subprocess.run(
                    [sys.executable, test_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"  ✓ {test_file}")
                    passed += 1
                else:
                    print(f"  ✗ {test_file}")
                    if result.stderr:
                        print(f"    Error: {result.stderr[:200]}")
                    failed += 1
            except Exception as e:
                print(f"  ✗ {test_file}: {e}")
                failed += 1
        else:
            print(f"  - {test_file} (not found)")
    
    return failed == 0


def main():
    """Run all verifications."""
    print("=" * 60)
    print("WebCMS Admin Panel - Final Verification")
    print("=" * 60)
    
    results = {}
    
    # Check imports
    imports_ok, failed_imports = check_imports()
    results['imports'] = imports_ok
    
    # Check features
    features_ok = check_features()
    results['features'] = features_ok
    
    # Run tests
    tests_ok = run_tests()
    results['tests'] = tests_ok
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name.capitalize():15} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("Project is ready for production!")
    else:
        print("✗ SOME CHECKS FAILED")
        print("Please review the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
