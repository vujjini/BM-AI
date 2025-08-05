from fastapi import APIRouter
from services.chat_service import chat_service
from models.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = chat_service.get_answer(request.question)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"]
    )

@router.get("/health")
async def health_check():
    return {"status": "healthy"}