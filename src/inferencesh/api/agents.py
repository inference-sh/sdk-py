"""Agents API - namespaced agent operations."""

from __future__ import annotations

from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Inference, AsyncInference
    from ..types import AgentConfig
    from ..agent import Agent, AsyncAgent


class AgentsAPI:
    """Synchronous Agents API.

    Example:
        ```python
        client = inference(api_key="...")

        # Create agent from template
        agent = client.agents.create('okaris/assistant@abc123')

        # Create ad-hoc agent
        agent = client.agents.create({
            'core_app': { 'ref': 'infsh/claude-sonnet-4@xyz789' },
            'system_prompt': 'You are a helpful assistant',
        })

        # Send messages
        response = agent.send_message('Hello!')
        ```
    """

    def __init__(self, client: "Inference") -> None:
        self._client = client

    def create(self, config: Union[str, "AgentConfig"]) -> "Agent":
        """Create an agent for chat interactions.

        Args:
            config: Either a template reference string (namespace/name@version) or ad-hoc config

        Returns:
            An Agent instance for chat operations
        """
        return self._client.agent(config)


class AsyncAgentsAPI:
    """Asynchronous Agents API.

    Example:
        ```python
        client = async_inference(api_key="...")

        # Create agent from template
        agent = client.agents.create('okaris/assistant@abc123')

        # Send messages
        response = await agent.send_message('Hello!')
        ```
    """

    def __init__(self, client: "AsyncInference") -> None:
        self._client = client

    def create(self, config: Union[str, "AgentConfig"]) -> "AsyncAgent":
        """Create an async agent for chat interactions.

        Args:
            config: Either a template reference string (namespace/name@version) or ad-hoc config

        Returns:
            An AsyncAgent instance for chat operations
        """
        return self._client.agent(config)
