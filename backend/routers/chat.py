from fastapi import APIRouter
from services.chat_service import chat_service
from models.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await chat_service.get_answer(request.question)  # Added await here
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        enhanced_question=result.get("enhanced_question", "")  # Added enhanced_question
    )

@router.get("/health")
async def health_check():
    return {"status": "healthy"}