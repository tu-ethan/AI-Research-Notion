import json
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_agent
from tools import wikipedia_search, duckduckgo_search
from langchain_core.messages import HumanMessage, ToolMessage
from typing import List
import requests
import os

load_dotenv()

tools = [wikipedia_search, duckduckgo_search]
# my next task is to seperate the functions in main.py into other files to make it more organized

# temperature controls how random/creative the output is. Higher = more creative, lower = more consistent
llm = ChatOpenAI(
    model="qwen/qwen3.6-plus:free",   # or whatever exact name OpenRouter gives
    temperature=0.7,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
).bind_tools(tools)  # bind tools to the llm so it can use them when needed
# llm3 = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)
# llm2 = ChatAnthropic(model="claude-3-5-sonnet", temperature=0.9)

# prompt template
class Section(BaseModel):
    heading: str
    content: str

class ResearchResponse(BaseModel):
    # you can include any fields you want your LLM to output
    topic: str
    sections: list[Section]
    sources: list[str]
    tools_used: list[str]

parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful research assistant explaining complex topics to a five year old in simple terms using analogies.
            Answer the user query
            Return ONLY valid JSON with structured fields. No markdown, no backticks. Output in the following format \n{format_instructions}
            """
        ),
        ("placeholder", "{messages}")
    ]
).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm 

def run_agent(user_input: str):
    messages = [HumanMessage(content=user_input)]
    print(messages)

    numRuns = 0
    while True:
        numRuns += 1
        print(numRuns)
        response = chain.invoke({"messages": messages})

        if not getattr(response, "tool_calls", None):
            return response.content
        
        tools_used = []

        for tool in response.tool_calls:
            tool_name = tool["name"]
            tool_args = tool["args"] # args is the input that the LLM generates
            # ex. the args could be what the LLM wants to search in google

            if tool_name == "wikipedia_search": # wikisearch is not working
                result = wikipedia_search.invoke(tool_args["query"])
            elif tool_name == "duckduckgo_search":
                result = duckduckgo_search.invoke(tool_args["query"])
            else:
                result = "Unknown tool"
            
            tools_used.append(
                ToolMessage(
                    content=result,
                    tool_call_id = tool["id"]
                )
            )
        
        messages.append(response)
        messages.extend(tools_used)

#query = input("What would you like to research? ")                
raw_response = run_agent("why is sleep good for you")
print(raw_response)
data = ResearchResponse.model_validate_json(raw_response)
print(type(data))

# to notion

url = "https://api.notion.com/v1/pages"

headers = {
    "Authorization": "Bearer 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",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

titleData = {
    "parent": { "database_id": "3395c6316e5980b59bc6f488030fe87a" },
    "properties": {
        "Name": {
            "title": [
                {"text": {"content": data.topic}}
            ]
        }
    }
}

blocks = []

for section in data.sections:
    # Heading
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [
                { "text": { "content": section.heading } }
            ]
        }
    })

    # Paragraph
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                { "text": { "content": section.content } }
            ]
        }
    })

res = requests.post(url, headers=headers, json=titleData)
page_id = res.json()["id"]
page_id = str(page_id).strip()
print(page_id, type(page_id))

blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"

res_blocks = requests.patch(
    blocks_url,
    headers=headers,
    json={"children": blocks}
)

print(res_blocks.status_code, res_blocks.text)