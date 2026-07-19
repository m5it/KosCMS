import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run tests
from tests.benchmark.test_settings_save import (
    TestSettingsSaveBenchmark,
    TestSettingsSaveIntegration
)

# Run with verbose output
loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromTestCase(TestSettingsSaveBenchmark))
suite.addTests(loader.loadTestsFromTestCase(TestSettingsSaveIntegration))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with proper code
sys.exit(0 if result.wasSuccessful() else 1)
