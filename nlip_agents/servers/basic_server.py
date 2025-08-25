import os

from nlip_sdk.nlip import NLIP_Factory
from nlip_server import server
from nlip_sdk import nlip

from nlip_agents.agents.basic_agent import BasicAgent # TOM'S NEW AGENT
from nlip_agents import logger


class ChatApplication(server.NLIP_Application):
    async def startup(self):
        logger.info("Starting app...")
        self.myAgent = BasicAgent(
            "BasicAgent"
        )

    async def shutdown(self):
        return None

    async def create_session(self) -> server.NLIP_Session:
        return ChatSession(self.myAgent)


class ChatSession(server.NLIP_Session):

    def __init__(self, agent: BasicAgent):
        self.agent = agent

    async def start(self):
        logger.info("Starting the chat session")

    async def execute(
        self, msg: nlip.NLIP_Message
    ) -> nlip.NLIP_Message:
        logger = self.get_logger()
        text = msg.extract_text()

        try:
            results = await self.agent.process_query(text)
            logger.info(f"Results : {results}")
            msg = NLIP_Factory.create_text(results[0])
            for res in results[1:]:
               msg.add_text(res)
            return msg
        except Exception as e:
            logger.error(f"Exception {e}")
            return None

    async def stop(self):
        logger.info(f"Stopping chat session")
        await self.agent.cleanup()
        self.server = None


app = server.setup_server(ChatApplication())
