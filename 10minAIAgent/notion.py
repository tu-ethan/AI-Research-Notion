import requests
from agent import ResearchResponse

url = "https://api.notion.com/v1/pages"

headers = {
    "Authorization": "Bearer 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",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json"
}

def sendToNotion(raw_response):
    titleData, blocks = processContent(raw_response) 
    postToNotion(titleData, blocks)

def processContent(AIresponse):
    
    data = ResearchResponse.model_validate(AIresponse)

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
    
    return titleData, blocks


def postToNotion(title, blocks):
    res = requests.post(url, headers=headers, json=title) # creates a notion page with title

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