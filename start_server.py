#!/usr/bin/env python3
"""Start WebCMS server for testing."""

import sys
import os
sys.path.insert(0, '/home/user/KosCMS')

# Set minimal config
os.environ['WEBCMS_CONFIG'] = '/home/user/KosCMS/config_minimal.json'

from webcms.app_factory import create_app

# Create app with minimal config
app = create_app('/home/user/KosCMS/config_minimal.json')

# Run server
if __name__ == '__main__':
    print("Starting WebCMS server on http://127.0.0.1:8000")
    app.run(host='127.0.0.1', port=8000, debug=True)
