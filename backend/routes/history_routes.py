import os
import time
import json
import re
from fastapi import APIRouter, HTTPException

router = APIRouter()

HISTORY_DIR = "history"

@router.post("/history/save")
@router.post("/history/save/")
async def save_history(data: dict):
    """Save a conversation to a JSON file."""
    messages = data.get("messages", [])
    filename = data.get("filename")
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to save.")
    
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    if filename and os.path.exists(os.path.join(HISTORY_DIR, filename)):
        filepath = os.path.join(HISTORY_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            title = old_data.get("title", "New Conversation")
            timestamp = old_data.get("timestamp", time.strftime("%Y%m%d_%H%M%S"))
        except Exception:
            title = "New Conversation"
            timestamp = time.strftime("%Y%m%d_%H%M%S")
    else:
        # Generate title from the first user message
        title = "New Conversation"
        for msg in messages:
            if msg.get("role") == "user":
                title = msg.get("content", "New Conversation")[:40].strip()
                title = re.sub(r'[^\\w\\s-]', '', title).replace(" ", "_")
                break
                
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{title}.json"
        filepath = os.path.join(HISTORY_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"title": title, "timestamp": timestamp, "messages": messages}, f, indent=2, ensure_ascii=False)
        
    return {"status": "success", "filename": filename}

@router.get("/history/list")
@router.get("/history/list/")
async def list_history():
    """List all saved conversations."""
    if not os.path.exists(HISTORY_DIR):
        return []
    
    history = []
    for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
        if filename.endswith(".json"):
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    history.append({
                        "filename": filename,
                        "title": data.get("title", "Untitled").replace("_", " "),
                        "timestamp": data.get("timestamp", "")
                    })
            except Exception:
                continue
    return history

@router.get("/history/load/{filename}")
async def load_history(filename: str):
    """Load a specific conversation."""
    filepath = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

@router.delete("/history/delete/{filename}")
async def delete_history(filename: str):
    """Delete a conversation."""
    filepath = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    os.remove(filepath)
    return {"status": "success"}
