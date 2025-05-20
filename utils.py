import json, re

def extract_json_from_markdown(text: str) -> dict:
    """
    Extract JSON content from a markdown code block like ```json ... ```
    """
    # Match anything between triple backticks
    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        # Fallback: assume raw text is just JSON
        json_str = text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"answer": text, "suggested_questions": []}