from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.llm import llm
from app.retrieval import search_codebase, get_directory_tree, read_file_content
from pydantic import BaseModel, Field

# Define an exact explicit schema for the search query parameters
class SearchCodebaseSchema(BaseModel):
    query: str = Field(
        description="The specific code keyword, function name, or conceptual search string. Must be specific."
    )

def get_search_tool(repo_url: str):
    """Factory function for semantic search tool."""
    @tool("search_codebase_tool", args_schema=SearchCodebaseSchema)
    def search_codebase_tool(query: str) -> str:
        """Search the codebase for code snippets relevant to the query. 
        Use this tool to find information about concepts, functions, or features. 
        If the first search doesn't return what you need, try different keywords."""
        try:
            results = search_codebase(query, repo_url)
            if not results:
                return "No matching code found. Try a different search query."
            
            return "\n\n---\n\n".join([
                f"File: {chunk['source']}\n{chunk['content']}"
                for chunk in results
            ])
        except Exception as e:
            return f"Error searching codebase: {str(e)}"
            
    return search_codebase_tool


def get_directory_tree_tool(repo_url: str):
    """Factory function for directory tree tool."""
    @tool
    def directory_tree_tool() -> str:
        """Fetch the entire folder structure (directory tree) of the repository. 
        Use this tool when you need to understand the layout, find where certain components live, or look up exact file paths before reading them."""
        return get_directory_tree(repo_url)
    return directory_tree_tool


def get_read_file_tool(repo_url: str):
    """Factory function for file reading tool."""
    @tool
    def read_file_tool(file_path: str) -> str:
        """Read the exact, complete contents of a specific file. 
        You MUST provide the exact file path (e.g., 'src/app/page.tsx'). 
        Use this after finding a file in the directory tree or if you know the exact path and need its full context."""
        return read_file_content(file_path, repo_url)
    return read_file_tool


def run_agent(messages_dict: list, repo_url: str) -> str:
    """
    Executes the LangGraph Agent to answer a user's question using a suite of tools.
    messages_dict: List of dicts [{"role": "user", "content": "..."}]
    """
    # Instantiate the tools for this specific repository
    search_tool = get_search_tool(repo_url)
    dir_tool = get_directory_tree_tool(repo_url)
    file_tool = get_read_file_tool(repo_url)
    
    tools = [search_tool, dir_tool, file_tool]
    
    system_prompt = """You are an expert senior software engineer analyzing a codebase.
You have access to a suite of specialized tools. Use them to investigate the codebase thoroughly!

YOUR TOOLBOX:
1. search_codebase_tool: Use this to semantically search for concepts, keywords, or where certain functions are defined.
2. directory_tree_tool: Use this if you need to understand the project structure, locate files, or find exact file paths.
3. read_file_tool: Use this to read the complete contents of a specific file path.

RULES:
- When asked a question, determine if you need information from the tools. If you do, execute the tool IMMEDIATELY. Do not provide a partial conversational answer before calling a tool.
- DO NOT guess file paths or names! If you need to find where something is, check the directory tree tool first to get the exact path.
- Base your final answers STRICTLY on the real output returned by your tools.

FORMATTING RULES (CRITICAL):
- Format your final response using clean Markdown.
- Break your text into short, highly readable paragraphs (1-3 sentences maximum).
- Use structural headings (###) and bullet points to make information clear and scannable.
- Use `inline code` formatting for variables, file names, and directory paths.
- Use full ```language code blocks``` for code fragments.
- Do not mention your internal tool names (like 'search_codebase_tool') to the end user.
- DO NOT summarize or list out the directory structure of the repository in your answer unless the user explicitly asks for the folder structure. Just answer the specific question they asked.
"""
    
    # Initialize the LangGraph ReAct agent
    agent = create_react_agent(
        llm.client, 
        tools=tools, 
        prompt=system_prompt
    )
    
    # Convert dict messages to LangChain message objects
    formatted_messages = []
    for msg in messages_dict:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        else:
            formatted_messages.append(AIMessage(content=msg["content"]))
            
    # Run the agent
    response = agent.invoke({"messages": formatted_messages})
    
    # Extract the final AI message that doesn't have tool calls
    final_content = ""
    for msg in reversed(response["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            final_content = msg.content
            break
            
    if not final_content:
        final_content = response["messages"][-1].content
        
    # Google GenAI sometimes returns content as a list of dicts instead of a string
    if isinstance(final_content, list):
        final_content = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in final_content
        )
        
    return str(final_content)
