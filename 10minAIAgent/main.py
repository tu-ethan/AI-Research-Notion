from dotenv import load_dotenv
from notion import sendToNotion
from agent import get_agent_response

load_dotenv()

query = input("What would you like to research? ")                
response = get_agent_response(query)
print(response)

sendToNotion(response)