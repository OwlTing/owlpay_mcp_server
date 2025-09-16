def main():
    """Search Owlpay documentation MCP server"""
    from .server import main as web_main
    web_main()

# 導出 web 模組以便於導入
from . import server

if __name__ == "__main__":
    main()