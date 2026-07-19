import sys
import logging
from webcms.app_factory import create_app

logging.basicConfig(level=logging.DEBUG, filename='server.log', filemode='w')
app = create_app()
app.run(host='127.0.0.1', port=8000, debug=True)
