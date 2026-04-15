"""
AQ Java Bridge Server - Flask application factory.
Reconstructed from AQJavaServer.exe (Python 3.13 PyInstaller bundle).

Provides REST API for automating Java Swing/AWT applications
via the Java Access Bridge (JAB) API.
"""
from flask import Flask
import logging

app = Flask(__name__)

# Logger setup
logger = logging.getLogger(__name__)
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler("aqjbridge.log")
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)
logger.addHandler(c_handler)
logger.addHandler(f_handler)

from core import routes  # noqa: E402, F401

logger.debug("STARTED JAVA BRIDGE")
