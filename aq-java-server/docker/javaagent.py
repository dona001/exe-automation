"""
AQ Java Bridge Server - Entry point.
Reconstructed from AQJavaServer.exe (Python 3.13 PyInstaller bundle).

REST API server for automating Java Swing/AWT applications
via the Java Access Bridge (JAB) API.
"""
import os
import warnings
from configparser import ConfigParser

os.environ["FLASK_ENV"] = "production"
warnings.filterwarnings("ignore", category=DeprecationWarning)

from core import app, logger  # noqa: E402
import sys
import traceback


def get_port():
    """Read server port from config.ini."""
    try:
        config = ConfigParser()
        config.read("config.ini")
        return int(config.get("default", "port"))
    except Exception:
        traceback.print_exc(file=sys.stdout)
        print("Failed to get port from config.ini")
        return 9996


if __name__ == "__main__":
    try:
        port = get_port()
        if len(sys.argv) > 1:
            port = int(sys.argv[1])
    except Exception:
        logger.error(f"ERROR: INVALID PORT NUMBER {sys.argv[1]} PROVIDED.")
        sys.exit(1)

    logger.debug("Started the server")
    app.run(debug=False, host="localhost", port=port)
