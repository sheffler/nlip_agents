import os
import subprocess
import sys

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
