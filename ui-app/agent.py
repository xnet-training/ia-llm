import uuid
import asyncio
from dataclasses import dataclass, field
import time, importlib, inspect, os, json
from typing import Any, Optional, Dict, TypedDict

from langchain.schema import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM
from langchain_core.embeddings import Embeddings

import python.helpers.log as Log
#from python.helpers.dirty_json import DirtyJson
from python.helpers.defer import DeferredTask
from typing import Callable

@dataclass
class AgentConfig:
    chat_model: BaseChatModel | BaseLLM
    utility_model: BaseChatModel | BaseLLM
    embeddings_model: Embeddings
    prompts_subdir: str = ""
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = field(default_factory=lambda: ["default", "custom"])
    auto_memory_count: int = 3,
    rate_limit_requests: int = 15,
    max_tool_response_length: int = 3000,
    code_exec_docker_enabled: bool = True,
    code_exec_ssh_enabled: bool = True

class AgentContext:
    _contexts: dict[str, "AgentContext"] = {}
    _counter: int = 0

    def __init__(self,
            config: AgentConfig,
            id: str | None = None,
            name: str | None = None,
            agent0: "Agent|None" = None,
            log: Log.Log | None = None,
            paused: bool = False,
            streaming_agent: "Agent|None" = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.config = config
        self.log = log or Log.Log()
        self.agent0 = agent0 or Agent(0, self.config, self)
        self.paused = paused
        self.streaming_agent = streaming_agent
        self.process: DeferredTask | None = None
        AgentContext._counter += 1
        self.no = AgentContext._counter

        self._contexts[self.id] = self

    @staticmethod
    def get(id: str):
        return AgentContext._contexts.get(id, None)

    @staticmethod
    def first():
        if not AgentContext._contexts:
            return None
        return list(AgentContext._contexts.values())[0]

    def communicate(self, msg: str, broadcast_level: int = 1):
        self.paused = False  # unpause if paused
        if self.streaming_agent:
            current_agent = self.streaming_agent
        else:
            current_agent = self.agent0
        #
        # TODO
        #
        if self.process and self.process.is_alive():
            intervention_agent = current_agent
            while intervention_agent and broadcast_level != 0:
                intervention_agent.intervention_message = msg
                broadcast_level -= 1
                intervention_agent = intervention_agent.data.get("superior", None)
        else:
            self.process = DeferredTask(self._process_chain, current_agent, msg)

        return self.process

    async def _process_chain(self, agent: 'Agent', msg: str, user=True):
        try:
            msg_template = (
                    agent.read_prompt("fw.user_message.md", message=msg)
                    if user
                    else agent.read_prompt(
                        "fw.tool_response.md",
                        tool_name="call_subordinate",
                        tool_response=msg,
                    )
            )
            response = await agent.monologue(msg_template)
            superior = agent.data.get("superior", None)
            if superior:
                response = await self._process_chain(superior, response, False)
            return response
        except Exception as e:
            agent.handle_critical_exception(e)


class Message:
    def __init__(self):
        self.segments: list[str]
        self.human: bool

class LoopData:
    def __init__(self):
        self.iteration = -1
        self.system = []
        self.message = ""
        self.history_from = 0
        self.history = []

class Agent:
    def __init__(self, number: int, config: AgentConfig, context: AgentContext | None = None):
        self.config = config
        self.context = context or AgentContext(config)
        self.number = number
        self.agent_name = f"Agent {self.number}"
        self.history = []
        self.last_message = ""
        self.intervention_message = ""
        self.data = {}

    async def monologue(self, msg: str):
        while True:
            try:
                loop_data = LoopData()
                loop_data.message = msg
                loop_data.history_from = len(self.history)


                await self.call_extensions("monologue_start", loop_data=loop_data)
                printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)
                user_message = loop_data.message
                await self.append_message(user_message, human=True)

                while True:
                    self.context.streaming_agent = self  # mark self as current streamer
                    agent_response = ""
                    loop_data.iteration += 1

                    try:
                        loop_data.system = []
                        loop_data.history = self.history

                        await self.call_extensions("message_loop_prompts", loop_data=loop_data)

                        prompt = ChatPromptTemplate.from_messages(
                                [
                                    SystemMessage(content="\n\n".join(loop_data.system)),
                                    MessagesPlaceholder(variable_name="messages"),
                                ]
                        )
                        chain = prompt | self.config.chat_model

                        formatted_inputs = prompt.format(messages=self.history)
                        tokens = int(len(formatted_inputs) / 4)
                        self.rate_limiter.limit_call_and_input(tokens)

                        PrintStyle(
                                 bold=True,
                                 font_color="green",
                                 padding=True,
                                 background_color="white",
                        ).print(f"{self.agent_name}: Generating")

                        log = self.context.log.log(
                                 type="agent", 
                                 heading=f"{self.agent_name}: Generating"
                        )

                        async for chunk in chain.astream(
                                {"messages": loop_data.history}
                        ):
                            await self.handle_intervention(agent_response)

                        if isinstance(chunk, str):
                            content = chunk
                        elif hasattr(chunk, "content"):
                            content = str(chunk.content)
                        else:
                            content = str(chunk)

                        if content:
                            printer.stream(content)
                            agent_response += (content)  # concatenate stream into the response
                            self.log_from_stream(agent_response, log)

                        #self.rate_limiter.set_output_tokens(int(len(agent_response) / 4))
                    # exceptions inside message loop:
                    except InterventionException as e:
                        pass
                    except (RepairableException) as e:
                        error_message = errors.format_error(e)
                        msg_response = self.read_prompt("fw.error.md", error=error_message)
                        await self.append_message(msg_response, human=True)
                        PrintStyle(font_color="red", padding=True).print(msg_response)
                        self.context.log.log(type="error", content=msg_response)
                    except Exception as e:
                        self.handle_critical_exception(e)
                    finally:
                        await self.call_extensions("message_loop_end", loop_data=loop_data)
            except InterventionException as e:
                pass  # just start over
            except Exception as e:
                self.handle_critical_exception(e)
            finally:
                self.context.streaming_agent = None  # unset current streamer
                await self.call_extensions("monologue_end", loop_data=loop_data)  # type: ignore

