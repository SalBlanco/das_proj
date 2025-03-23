import os
from src.utils import search, write, paginate, check_history

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

import re
import json

def main():
    # Load API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Load current index from state file
    records_file = 'out/records.json'
    if os.path.exists(records_file):
        with open(records_file, 'r') as f:
            index = len(f.readlines())
    else:
        index = 0
    
    # Number of papers to retrieve per call
    papers_per_call = 10
    
    print(f"Starting search from index {index}")
    
    # Set up tools and LLM agent
    tools = [search, paginate, write, check_history]
    memory = MemorySaver()
    model = ChatOpenAI(model_name="gpt-4o", api_key=api_key)
    agent_executor = create_react_agent(model, tools, checkpointer=memory)
    
    config = {"configurable": {"thread_id": "das-papers"}}
    
    # Run the agent
    for step in agent_executor.stream(
        {"messages": [HumanMessage(content=f"""
    You are a research assistant helping me find Distributed Acoustic Sensing (DAS) papers on arXiv. 

    **Task Instructions:**  
    1. Use the `search` tool to retrieve the next {papers_per_call} papers, starting from index {index}.
    2. Return the following details for each paper:  
        - title  
        - id  
        - author
        - link
    3. If you are able to correctly search, use the return 'obj' from the 'search' tool as the input for the 'write' tool. 
    4. If you are able to correctly search and write to the corresponding file, update the next index using the `paginate` tool. 
    5. Return the next starting index for future searches with the format: 'The next starting index for future searches is [index].'

    **Notes:**  
    - Always start from the most recent index and paginate correctly to avoid duplicates.  
    - If no new papers are found, return an empty list along with the current index.  
    """)]},
        config,
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
        
        # Extract the new index from the agent's response
        match = re.search(r"The next starting index for future searches is (\d+)", str(step["messages"][-1]))
        if match:
            index = int(match.group(1))  # Extract and convert to integer
    
    print(f"Updated index to {index}")
    
if __name__ == "__main__":
    main()