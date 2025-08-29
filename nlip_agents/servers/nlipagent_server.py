#
# A Server that Launches a NlipAgent instance for each session
#

import os

from nlip_sdk.nlip import NLIP_Message
from nlip_sdk.nlip import NLIP_Factory

from nlip_agents.agents.nlip_agent import NlipAgent

import nlip_agents.http_server.nlip_session_server as server
from nlip_agents.http_server.nlip_session_server import SessionManager

from nlip_agents import logger
import uvicorn


#
# Define a session manager that launches a new BasicAgent for each session
#

class NlipManager(SessionManager):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.myAgent = NlipAgent(
            "Margaret"
        )

    async def process_nlip(self, msg: NLIP_Message) -> NLIP_Message:

        # concatenate all of the "text" parts
        text = msg.extract_text()

        try:
            results = await self.myAgent.process_query(text)
            logger.info(f"Results : {results}")
            msg = NLIP_Factory.create_text(results[0])
            for res in results[1:]:
               msg.add_text(res)
            return msg
        except Exception as e:
            logger.error(f"Exception {e}")
            return None
        
        
#
# Now configure the server
#

server.SESSION_MANAGER_CLASS = NlipManager
server.SESSION_COOKIE_NAME = "NlipCoordinatorCookie"

app = server.app

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8024, log_level="info")
    uvicorn.run("nlip_agents.servers.nlip_server:app", host="0.0.0.0", port=8024, log_level="info", reload=True)
