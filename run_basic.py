import os
import subprocess
import sys

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
