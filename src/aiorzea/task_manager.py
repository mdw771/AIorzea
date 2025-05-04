from textwrap import dedent
from typing import Callable
import autogen

import aiorzea.comms as comms
from aiorzea.tools.base import BaseTool
from aiorzea.tools.query import XIVAPIQueryTool


class TaskManager:

    class AgentGroup(dict):
        user_proxy: autogen.UserProxyAgent = None
        tool_executor: autogen.UserProxyAgent = None
        assistant: autogen.ConversableAgent = None
            
    def __init__(self, model_name: str = "gpt-4o", *args, **kwargs):
        self.model_name = model_name
        self.agents = self.AgentGroup()
        self.group_chat_manager = None
        self.build()

    def build(self, *args, **kwargs):
        self.build_agents()
        self.build_tools()

    def build_agents(self, *args, **kwargs):
        self.agents.assistant = autogen.ConversableAgent(
            name="assistant",
            system_message=dedent(
                """\
                You are answering game-related questions of a player of
                Final Fantasy XIV. These questiosn may be related to in-game
                actions and items, such as the attributes of a gear. 
                You have tools provided to you to query a game database.
                Use the tool to look for the information you need to answer
                the questions. When you finish answering a question or need
                human input, say "TERMINATE".\
                """
            ),
            llm_config={
                "model": self.model_name,
                "api_key": comms.get_llm_api_key(self.model_name),
            },
        )
        
        self.agents.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            llm_config=False,
            human_input_mode="ALWAYS",
            code_execution_config={
                "use_docker": False
            },
        )

        self.agents.tool_executor = autogen.ConversableAgent(
            name="tool_executor",
            system_message=dedent(
                """\
                Execute tools called by the assistant.\
                """
            ),
            code_execution_config={
                "use_docker": False
            },
        )

        group_chat =  autogen.GroupChat(
            agents=[self.agents.user_proxy, self.agents.tool_executor, self.agents.assistant],
            messages=[],
            max_round=10,
        )

        self.group_chat_manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config={
                "model": self.model_name,
                "api_key": comms.get_llm_api_key(self.model_name),
            },
        )

    def build_tools(self, *args, **kwargs):
        query_tool = XIVAPIQueryTool()
        self.register_tools(
            callables=query_tool.__call__,
            names=["general_query"],
            caller=self.agents.assistant,
            executor=self.agents.tool_executor
        )
        self.register_tools(
            query_tool.query_item,
            names=["item_query"],
            caller=self.agents.assistant,
            executor=self.agents.tool_executor
        )
    
    def register_tools(
        self, 
        callables: list[Callable] = None,
        names: list[str] = None,
        caller: autogen.ConversableAgent = None, 
        executor: autogen.ConversableAgent = None
    ) -> None:
        if callables is None:
            callables = []
        if not isinstance(callables, (list, tuple)):
            callables = [callables]
        if isinstance(names, str) and not isinstance(names, (list, tuple)):
            names = [names]
        for i, func in enumerate(callables):
            wrapped_tool = autogen.tools.Tool(
                name=names[i] if names else func.__name__,
                description=func.__doc__,
                func_or_tool=func,
            )
            autogen.register_function(
                wrapped_tool,
                caller=caller,
                executor=executor,
                name=names[i] if names else func.__name__,
                description=func.__doc__,
            )

    def run(self, *args, **kwargs):
        message = input("Enter a message: ")
        self.agents.user_proxy.initiate_chat(
            self.group_chat_manager,
            message=message,
        )
