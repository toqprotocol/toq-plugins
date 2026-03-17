<p align="center">
  <strong>toq protocol framework plugins</strong>
</p>

<p align="center">
  LangChain and CrewAI integrations for <a href="https://github.com/toqprotocol/toq">toq protocol</a>. Give your agents the ability to communicate with other agents.
</p>

<p align="center">
  <a href="https://github.com/toqprotocol/toq-plugins/actions"><img src="https://github.com/toqprotocol/toq-plugins/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/toq-langchain/"><img src="https://img.shields.io/pypi/v/toq-langchain.svg?label=toq-langchain" alt="PyPI"></a>
  <a href="https://pypi.org/project/toq-crewai/"><img src="https://img.shields.io/pypi/v/toq-crewai.svg?label=toq-crewai" alt="PyPI"></a>
  <a href="https://github.com/toqprotocol/toq-plugins/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
</p>

---

## Packages

This monorepo contains three packages:

| Package | Description | Install |
|---------|-------------|---------|
| `toq-langchain` | 17 LangChain tools for toq | `pip install toq-langchain` |
| `toq-crewai` | 17 CrewAI tools for toq | `pip install toq-crewai` |
| `toq-plugins-common` | Shared binary management and daemon lifecycle | (installed automatically) |

All packages require Python 3.10+.

## Prerequisites

1. Install the [toq binary](https://github.com/toqprotocol/toq)
2. Run `toq setup`
3. Run `toq up`

## LangChain

```python
import toq
from toq_langchain import make_tools

client = toq.connect()
tools = make_tools(client)

# Use with any LangChain agent
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(llm, tools)
```

Or use the built-in `connect()` which handles binary extraction, setup, and daemon startup:

```python
from toq_langchain import connect

toq_client = connect(agent_name="alice", connection_mode="open")
tools = toq_client.tools()
sdk = toq_client.sdk  # direct access to toq.Client
```

### Listening for Messages

```python
from toq_langchain import listen

# Feeds incoming toq messages into your LangChain agent
await listen(async_client, agent)
```

## CrewAI

```python
import toq
from toq_crewai import make_tools

client = toq.connect()
tools = make_tools(client)

# Use with any CrewAI crew
from crewai import Agent, Task, Crew

agent = Agent(
    role="Communicator",
    goal="Send and receive messages via toq protocol",
    tools=tools,
)
```

Or use the built-in `connect()`:

```python
from toq_crewai import connect

toq_client = connect(agent_name="alice", connection_mode="open")
tools = toq_client.tools()
```

## Available Tools

Both plugins expose the same 17 tools:

| Tool | Description |
|------|-------------|
| `toq_send` | Send a message to a remote agent |
| `toq_send_stream` | Send a streaming message (word-by-word delivery) |
| `toq_peers` | List known peers with connection status |
| `toq_status` | Check daemon status |
| `toq_block` | Block a peer by key, address, or wildcard |
| `toq_unblock` | Unblock a peer |
| `toq_approvals` | List pending approval requests |
| `toq_approve` | Approve a request or pre-approve by pattern |
| `toq_deny` | Deny a pending request |
| `toq_revoke` | Revoke an approved rule |
| `toq_history` | Query received message history |
| `toq_permissions` | List all permission rules |
| `toq_ping` | Ping a remote agent |
| `toq_handlers` | List registered message handlers |
| `toq_add_handler` | Register a new handler |
| `toq_remove_handler` | Remove a handler |
| `toq_stop_handler` | Stop running handler processes |

## Repo Structure

```
_common/          toq-plugins-common: binary management, daemon lifecycle, setup
langchain/        toq-langchain: LangChain tools + SSE listener
crewai/           toq-crewai: CrewAI tools + SSE listener
```

## License

Apache 2.0
