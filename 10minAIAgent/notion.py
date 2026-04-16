import requests
from agent import FormatResponse

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
    
    data = FormatResponse.model_validate(AIresponse)
    sources = data.sources

    sources_property = {
        "rich_text": [
            {
                "text": {
                    "content": source.title + "\n",
                    "link": {
                        "url": source.link
                    }
                }
            }
            for source in sources
        ]
    }
    titleData = {
        "parent": { "database_id": "3395c6316e5980b59bc6f488030fe87a" },
        "properties": {
            "Name": {
                "title": [
                    {"text": {"content": data.topic}}
                ]
            },
            "Sources": sources_property
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

    if res.status_code != 200:
        print("ERROR:", res.json())
        raise Exception("Notion create page request failed")

    page_id = res.json()["id"]
    page_id = str(page_id).strip()
    print("Successfully Created Notion Page")

    blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    res = requests.patch(
        blocks_url,
        headers=headers,
        json={"children": blocks}
    )
    if res.status_code != 200:
        print("ERROR:", res.json())
        raise Exception("Notion edit page failed")
    print("Successfully posted information to notion")