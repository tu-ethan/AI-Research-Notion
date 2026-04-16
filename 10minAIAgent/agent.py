from tools import wikipedia_search, duckduckgo_search
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
import os

tools = [duckduckgo_search]

load_dotenv()

# temperature controls how random/creative the output is. Higher = more creative, lower = more consistent
llm = ChatOpenAI(
    model="openrouter/elephant-alpha",   # or whatever exact name OpenRouter gives
    temperature=1,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
).bind_tools(tools)  # bind tools to the llm so it can use them when needed

class Section(BaseModel):
    heading: str
    content: str

class Source(BaseModel):
    title: str
    link: str

class FormatResponse(BaseModel):
    # you can include any fields you want your LLM to output
    topic: str
    sections: list[Section]
    sources: list[Source]
    tools_used: list[str]


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful research assistant explaining complex topics to a five year old in simple terms using analogies.
            """
        ),
        ("placeholder", "{messages}")
    ]
)

chain = prompt | llm 

def run_agent(user_input: str):
    messages = [HumanMessage(content=user_input)]
    print(messages)

    tools_used_list = {}
    sources = []

    numRuns = 0
    while True:
        numRuns += 1
        print(numRuns)
        response = chain.invoke({"messages": messages})

        if not getattr(response, "tool_calls", None):
            # response includes a lot of junk, response.content is the main answer, parser.parse ensures the format is correct
            #print(response.content)
            #data = parser.parse(response.content)
            print(response.content)
            return {
                "output": response.content, # key text to return
                "tools_used": tools_used_list,
                "sources": sources
            }
        
        tools_used = []

        for tool in response.tool_calls:
            tool_name = tool["name"]
            tool_args = tool["args"] # args is the input that the LLM generates
            # ex. the args could be what the LLM wants to search in google

            if tool_name == "duckduckgo_search":
                result = duckduckgo_search.invoke(tool_args["query"])
                if (tool_name in tools_used_list):
                    tools_used_list[tool_name] += 1
                else:
                    tools_used_list[tool_name] = 1
            else:
                print("TOOL CALLED:", tool_name)
                print("AVAILABLE TOOLS:", ["duckduckgo_search", "wikipedia_search"])
                result = {
                    "text": "Unknown tool",
                    "results": []
                }
            
            search_result = result["text"]
            for source in result["results"]:
                sources.append(f"{source['title']}: {source['url']}")


            tools_used.append(
                ToolMessage(
                    content=search_result,
                    tool_call_id = tool["id"]
                )
            )
        
        messages.append(response)
        messages.extend(tools_used)

llmFormat = ChatOpenAI(
    model="openrouter/elephant-alpha", 
    temperature=0, #since it is formatting information it needs to be consistent
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)

def formatResponse(raw_response):
    # prompt template
    parser = PydanticOutputParser(pydantic_object=FormatResponse)

    promptFormat = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a reliable, consistent helper that formats information into headings and text bullet points
                Return the top 3 most relevant sources
                Return ONLY valid JSON with structured fields.
                You MUST output in the following format \n{format_instructions}
                """
            ),
            ("human", "Raw Response: {input}"),
            ("human", "Tools used: {tools_used}"),
            ("human", "Sources: {sources}")    
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    formatChain = promptFormat | llmFormat | parser
    formatted = formatChain.invoke({
        "input": raw_response["output"],
        "tools_used": raw_response["tools_used"],
        "sources": raw_response["sources"]
    })
    return formatted

def get_agent_response(user_input):
    raw_response = run_agent(user_input)
    return formatResponse(raw_response)
