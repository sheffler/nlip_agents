import logging
import asyncio
from typing import Optional, List, Dict, Any
from typing import Callable

# Use the NLIP logger in this package
logger = logging.getLogger("NLIP")

# from pydantic import schema_of, schema_json_of
from pydantic import TypeAdapter
import json

# Pydantic v2 is deprecating schema_of.  This is how to do it in Pydantic v3.
def schema_of(thing):
    adapter = TypeAdapter(thing)
    return adapter.json_schema()

from litellm import completion
from dotenv import load_dotenv

# Configure Logging for LiteLLM
import litellm
litellm._turn_on_debug()

# Load .env for vars like ANTHROPIC_API_KEY, etc
load_dotenv()

# MODEL = 'llama3.2:latest'
# MODEL = 'ollama_chat/llama3.2:latest'
MODEL = 'ollama_chat/llama3-groq-tool-use:latest'
# MODEL = "anthropic/claude-3-7-sonnet-20250219"

################################################################
# from nlip_sdk import nlip
# # from function_schema import function_schema
# from pydantic import schema_json_of, schema_of

# def process_nlip(target: str, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
#     print(f"NLIPMSG: {msg}")
#     return nlip.NLIP_Factory.create_text("This is the result")

# print(schema_json_of(process_nlip, title="Foo", indent=2))


################################################################

INSTRUCTION = """
You are an agent with tools.  When calling a tool, make sure to match the type signature of the tool.
"""

class BasicAgent:
    """
    LLM-based Agent capable of invoking tools.

    Args:
        name (str): REQUIRED - the agent's name
        model (str): the LLM model to use
        instruction (str): the system instruction
        tools (list): the initial set of tools
    """
        

    def __init__(self,
                 name: str,
                 model: str = 'ollama_chat/llama3.2:latest',
                 instruction: str = None,
                 tools: list[Callable] = [ ]
                 ):

        # self.name: str = name
        self.model: str = model
        self.instruction: str = instruction

        # the conversation history
        self.messages: list[Any] = [
            {
                "role": "system",
                "content": INSTRUCTION
            }
        ]

        # Every agent knows its name
        self.add_instruction(f"Your name is {name}.")

        # Add other instructions
        if instruction:
            self.add_instruction(instruction)

        # tools is a list of dict
        self.tools: list[Dict] = [ ]

        # map from tool name to Callable
        self.fnmap: Dict(str, Callable) = { }

        # final_text is what is returned to the user after a turn
        self.final_text: list[str] = [ ]

        # build the initial tools from a list of python callables
        for fn in tools:
            self.add_tool(fn)
    
    #
    # Tools MUST be Async Callable (for now).  Do use doc strings for the function and
    # the arguments as this helps the LLM understand the tool and its arguments.
    #
    
    def add_tool(self, fn: Callable):
        """Add a tool to the agent.  Its name and schema are generated using introspection."""
        name = fn.__name__

        # this is the tool description passed to the LLM
        self.tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": fn.__doc__,
                "parameters": schema_of(fn)
            }
        })

        # when the LLM requests a tool invocation this is where we find the Py function to call
        self.fnmap[name] = fn

    def list_tools(self):
        return self.tools

    #
    # Add a system instruction to refine the Agent's behavior
    #

    def add_instruction(self, instruction: str):
        self.messages.append(
            {
                "role": "system",
                "content": instruction
            }
        )
            

    #
    # Helper for main loop
    #

    async def _call_tool(self, name: str, args: Dict, tool_call_id: str) -> bool:
        """Call tool by name return True if it is found.
            ToDo: consider error handling ...
        """
        isFound = False

        fn = self.fnmap[name]
        if fn:
            isFound = True
            logger.info(f"Invoking tool:{name} with args:{args}")
            result = await fn(**args)
            logger.info(f"Got tool result:{result}")

            self.final_text.append(f"[Calling tool:{name} with args:{args}]")

            # NOTE: this solves a strange problem with ollama only
            # if type(result) == int:
            #    result = str(result)

            # serialize to json unless it is already a string
            if type(result) != str:
                result = json.dumps(result)

            self.messages.append(
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": name,
                    "content": result   # TOM: may be an NLIP Message
                }
            )

        return isFound


    #
    # Record the response message appropriately in both self.messages and self.final_response
    #
    
    def _handle_response(self, response_message):

        # to be shown to the user at the end of this turn
        self.final_text.append(response_message.content)

        tool_calls = response_message.tool_calls

        # NOTE: model_dump() is not mentioned in the documentation, but without
        # it pydantic complains about serializing messages on the following calls to completion().
        # The response is a Message with tool_calls[] containing a
        # ChatCompletionMessageToolCall object.  Pydantic does not know how to serialize properly.
        # Explicit serialization takes care of it.
        
        # to record in the conversation history
        if tool_calls:
            self.messages.append(response_message.model_dump())
        else:
            self.messages.append(response_message)


    #
    # Process a user query.  Return a message.
    #
            
    async def process_query(self, query: str) -> str:
        print(f"Processing query")

        # reset the result text
        self.final_text = [ ]

        # add to the conversation history
        self.messages.append({"role": "user", "content": query})

        # call the LLM witht he conversation
        response = completion(
            model=self.model, messages=self.messages, tools=self.tools
        )

        response_message = response.choices[0].message

        # Save the response
        self._handle_response(response_message)

        # Are there tool calls?
        tool_calls = response_message.tool_calls

        while tool_calls:

            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id # a uniqe id

                if await self._call_tool(tool_name, tool_args, tool_call_id) == False:
                    self.messages.append({"role": "user", "content": "Tool '{tool_name}' not found"})
                    
            # Now call the LLM again with the tool result
            response = completion(
                model=self.model, messages=self.messages, tools=self.tools
            )

            # Get the final response.
            response_message = response.choices[0].message

            # Save the response in the converation and add it to the text result
            self._handle_response(response_message)

            # Are there more tool calls?
            tool_calls = response_message.tool_calls

        return "\n".join(self.final_text)

    #
    # Provide a simple console based command loop for testing
    #
    
    async def chat_loop(self):
        logger.info("Agent Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        pass
    
################################################################
#
# Some simple tools for testing in the main() program below
#

async def echo(input: str) -> str:
    """This tool returns its argument as an echo"""
    logger.info(f"Echoing {input}")
    return f"Echoed Output is {input}"

# print(schema_json_of(echo, title="Echo", indent=2))

async def add2(val: int) -> int:
    """Add 2 to the argument and return the result."""
    return int(val) + 2

async def secret1(input: str) -> str:
    """Compute a secret given an input string"""
    import random
    letters = "abcdefghijklmnopqrstuvwxyz"
    c0 = random.choice(letters)
    c1 = random.choice(letters)
    secret = f"{input}{c0}{c1}"
    logger.info(f"The secret of {input} is {secret}")
    return secret

async def secret2(input: str) -> str:
    """Compute a secret given an input string"""
    import random
    letters = "abcdefghijklmnopqrstuvwxyz"
    c0 = random.choice(letters)
    c1 = random.choice(letters)
    c2 = random.choice(letters)
    secret = f"{input}{c0}{c1}{c2}"
    logger.info(f"The secret of {input} is {secret}")
    return secret


#
# Test program for trying out a simple agent with the console
#

async def main():
    logger.info(f"WELCOME")
    if len(sys.argv) < 0:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    agent = BasicAgent(
        name="Pronda",
        model=MODEL,
        instruction="You are a simple agent.  Answer each query as best as possible."
    )
    
    agent.add_tool(echo)
    agent.add_tool(add2)
    agent.add_tool(secret1)
    agent.add_tool(secret2)

    try:
        await agent.chat_loop()
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    import sys
    import nlip_agents
    nlip_agents.log_to_console(logging.DEBUG)

    asyncio.run(main())
