# OwlPay MCP Server

## Overview
The OwlPay MCP Server provides documentation search capabilities. This server enables large language models (LLMs) to directly retrieve documentation, accelerating system integration.

<img src="./docs/Demo.gif" width="650">
<br><br>

## Components

### Tools

#### Query Tools
- `search_owlpay_documentation`
   - Search Owlpay documentation. 
   - Input:
     - `query` (string): Search keywords in English.
   - Returns: Query results as array of objects

## Install

For quick installation, use one of the one-click install buttons above. The remote MCP Server is hosted by OwlTing and provides the easiest method for getting up and running. If your MCP host does not support remote MCP servers, you can easily set up the local version using Docker.


Docker Setup (For Local MCP Server Only):

```bash
docker build -f Dockerfile.local_docker -t mcp/owlpay . --no-cache
```

<details>
<summary><b>Install in Cursor</b></summary>

#### Click the button to install:

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install%20OwlPay%20-blue?logo=cursor&logoColor=white)](https://owlting.github.io/owlpay_mcp_server/install-cursor-mcp.html)

#### Or install manually:

Go to `Cursor Settings` -> `Tools & Integrations` -> `New MCP Server`. 

```json
{
  "mcpServers": {
    "owlpay": {
      "url": "https://owlpay-mcp.owlting.com/mcp/"
    }
  }
}
```

### Docker
```json
{
  "mcpServers": {
    "owlpay": {
      "command": "docker",
      "args": [
        "run", 
        "-i", 
        "--rm", 
        "mcp/owlpay"
      ]
    }
  }
}
```
</details>

<details><summary><b>Install in VS Code</b></summary>

#### Click the button to install:
[![Install in VS Code](https://img.shields.io/badge/VS%20Code-Install%20OwlPay%20-blue?logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode:mcp/install?%7B%22name%22%3A%22owlpay%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fowlpay-mcp.owlting.com%2Fmcp%2F%22%7D)

#### Or install manually:

You can also install the MCP server using the VS Code CLI:

```json
{
	"servers": {
		"owlpay": {
			"type": "http",
			"url": "https://owlpay-mcp.owlting.com/mcp/"
		}
	}
}
```

### Docker
```json
{
	"servers": {
		"owlpay": {
			"command": "docker",
			"args": [
				"run", 
				"-i", 
				"--rm", 
				"mcp/owlpay"
			]
		}
	}
}
```
</details>


<details>
<summary><b>Install in Claude Desktop</b></summary>

Follow the MCP install [guide](https://modelcontextprotocol.io/quickstart/user), use following configuration:

```json
# Add the server to your claude_desktop_config.json
{
  "mcpServers": {
    "owlpay": {
      "command": "docker",
      "args": [
        "run", 
        "-i", 
        "--rm", 
        "mcp/owlpay"
      ]
    }
  }
}
```
</details>