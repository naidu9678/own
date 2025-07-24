from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.tools.tool_context import ToolContext

from agent import root_agent
from callback_logging import log_query_to_model, log_model_response

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_req: ChatRequest):
    user_message = chat_req.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Create ToolContext per request
        try:
            tool_context = ToolContext()
        except TypeError:
            tool_context = ToolContext(None)

        # Invoke agent asynchronously
        response = await root_agent.invoke(
            tool_context=tool_context,
            user_input=user_message
        )

        # Extract textual response from the response object
        if hasattr(response, "text") and response.text:
            response_text = response.text
        elif hasattr(response, "content") and response.content:
            response_text = response.content
        elif hasattr(response, "candidates") and response.candidates:
            # For a list of candidates, grab first candidate's message text
            candidate = response.candidates[0]
            response_text = getattr(candidate, "message", str(candidate))
        else:
            response_text = str(response)  # fallback to string representation

        # Optional logging
        log_query_to_model(user_message)
        log_model_response(response_text)

        return ChatResponse(response=response_text)

    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
