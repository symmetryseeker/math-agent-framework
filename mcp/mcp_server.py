#!/usr/bin/env python3
"""
Math Agent Framework — MCP Server
===================================
通用数学推导 MCP 服务器，支持动态模型注册。

架构:
    Claude Code → MCP stdio → Math Agent Framework MCP Server
                                  ├── ToolRegistry (动态工具注册)
                                  ├── SymbolicEngine (符号推导)
                                  ├── NumericalEngine (数值计算)
                                  ├── VerificationEngine (验证)
                                  └── DocumentEngine (文档生成)

注册方式:
    claude mcp add-json math-agent-framework '{
      "command": "python",
      "args": ["D:/tools/math-agent-framework/mcp/mcp_server.py"],
      "env": {}
    }' -s local

特性:
    - 模型热加载: 修改模型代码后重启服务器即可生效
    - 自动工具生成: 每个 @derivation_step 产生一个 MCP 工具
    - 模型隔离: 不同模型的工具前缀不同 (math_{model}_...)
"""

import os, sys, json, logging, asyncio, io
from pathlib import Path
from typing import Optional

# Encoding setup for Windows
if sys.platform == "win32":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add framework root to path
FRAMEWORK_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(FRAMEWORK_DIR))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(FRAMEWORK_DIR / "math_agent_framework.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("math-agent-framework-mcp")

# MCP SDK
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Framework imports
from mcp.tool_registry import ToolRegistry
from models import discover_models

# ── Initialize ──
server = Server("math-agent-framework")
registry = ToolRegistry()

# Auto-discover and register all models
logger.info("Discovering models...")
all_models = discover_models()
logger.info(f"Found {len(all_models)} models: {list(all_models.keys())}")

for model_name, model_class in all_models.items():
    try:
        registry.register_model(model_class)
        logger.info(f"  Registered: {model_name}")
    except Exception as e:
        logger.error(f"  Failed to register {model_name}: {e}")

logger.info(f"Total tools registered: {len(registry.get_all_tools())}")


# ── MCP Handlers ──

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有动态注册的工具"""
    mcp_tools = []
    for tool_def in registry.get_all_tools():
        mcp_tools.append(Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def.get("inputSchema", {"type": "object", "properties": {}}),
        ))
    return mcp_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用动态注册的工具处理器"""
    logger.info(f"Tool called: {name} with args: {json.dumps(arguments, default=str)[:200]}")

    handler = registry.get_handler(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = await handler(arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        import traceback
        error_msg = f"Error in {name}: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({
            "error": str(e),
            "tool": name,
        }, ensure_ascii=False))]


# ── Main ──

async def main():
    logger.info("Math Agent Framework MCP Server starting...")
    logger.info(f"  Framework: {FRAMEWORK_DIR}")
    logger.info(f"  Models: {registry.get_registered_models()}")
    logger.info(f"  Tools: {len(registry.get_all_tools())}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
