#
# A Weather Agent has tools for querying about weather conditions and alerts.
# An additional system instruction helps refine its behavior.

import logging

import asyncio
from .basic_agent import BasicAgent

from typing import Any
import httpx
import json

# Import NLIP
from nlip_client.nlip_client import NLIP_HTTPX_Client
from nlip_sdk.nlip import NLIP_Factory, NLIP_Message
from urllib.parse import urlparse

from pydantic import AnyHttpUrl

# map host->session
sessions = { }

logger = logging.getLogger("NLIP")

# MODEL = 'llama3.2:latest'
# MODEL = 'ollama_chat/llama3.2:latest'
MODEL = 'ollama_chat/llama3-groq-tool-use:latest'
# MODEL = "anthropic/claude-3-7-sonnet-20250219"


#
# Make a connection and return a status string
#
    
async def connect_to_server(url):
    """Connect to the server and return a message"""
    try:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port
    except Exception as e:
        instance.text = f"Exception: {e}"
        return

    # Establish the URL and return a connection message
    await asyncio.sleep(1.0)
    client = NLIP_HTTPX_Client.create_from_url(f"http://{host}:{port}/nlip/")   
    sessions[host] = client

    logger.info(f"Saved {host} with client {client}")
    return f"Connected to http://{host}:{port}/"

#
# Send a message to a named host and get a response
#

# async def send_to_server(url: AnyHttpUrl, msg: str) -> NLIP_Message:
async def send_to_server(url: AnyHttpUrl, msg: str) -> dict:
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port
    client = sessions[host]

    nlip_message = NLIP_Factory.create_text(msg)
    logger.info(f"Sending message: {msg}")
    nlip_resp = await client.async_send(nlip_message)
    logger.info(f"Received: {nlip_resp.model_dump()}")
    # return nlip_resp.model_dump() # did not work
    # return nlip_resp.extract_text() # worked
    return str(nlip_resp.model_dump())



class NlipAgent(BasicAgent):

    def __init__(self,
                 name: str,
                 model: str = MODEL,
                 instruction: str = None,
                 tools = [connect_to_server, send_to_server]
                 ):

        super().__init__(name, model=model, tools=tools)

        self.add_instruction("You are an agent with tools for querying other NLIP Agent Servers")

        if instruction:
            self.add_instruction(instruction)
    

# Test program for running with stdin
async def main():
    logger.info(f"WELCOME")
    if len(sys.argv) < 0:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    agent = NlipAgent(
        "Margaret"
    )
    
    try:
        await agent.chat_loop()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys
    import nlip_agents
    nlip_agents.log_to_console(logging.DEBUG)

    asyncio.run(main())
