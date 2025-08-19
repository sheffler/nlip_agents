import os
import subprocess
import sys

import nlip_agents.servers.basic_server
from nlip_agents.servers.basic_server import app

subprocess.run(
    [
        "uvicorn",
        "nlip_agents.servers.basic_server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8020",
        "--reload"
    ],
    check=True
)
