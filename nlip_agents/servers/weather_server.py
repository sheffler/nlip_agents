import os

from nlip_sdk.nlip import NLIP_Factory
from nlip_server import server
from nlip_sdk import nlip

from nlip_agents.agents.weather_agent import WeatherAgent
from nlip_agents import logger


class ChatApplication(server.NLIP_Application):
    async def startup(self):
        logger.info("Starting app...")

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return ChatSession(WeatherAgent(
            "Weather"
        ))


class ChatSession(server.NLIP_Session):

    def __init__(self, agent: WeatherAgent):
        self.agent = agent

    async def start(self):
        logger.info("Starting the chat session")

    async def execute(
        self, msg: nlip.NLIP_Message
    ) -> nlip.NLIP_Message:
        logger = self.get_logger()
        text = msg.extract_text()

        try:
            response = await self.agent.process_query(text)
            logger.info(f"Response : {response}")
            return NLIP_Factory.create_text(response)
        except Exception as e:
            logger.error(f"Exception {e}")
            return None

    async def stop(self):
        logger.info(f"Stopping chat session")
        await self.agent.cleanup()
        self.server = None


app = server.setup_server(ChatApplication())
