import os
import subprocess
import sys

subprocess.run(
    [
        "uvicorn",
        "nlip_agents.servers.coordinator_server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8024",
        "--reload"
    ],
    check=True
)
