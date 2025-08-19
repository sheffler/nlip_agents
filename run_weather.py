import os
import subprocess
import sys

import nlip_agents.servers.basic_server
from nlip_agents.servers.basic_server import app

subprocess.run(
    [
        "uvicorn",
        "nlip_agents.servers.weather_server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8022",
        "--reload"
    ],
    check=True
)
