from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, chat, files

app = FastAPI(title="Building Manager RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(files.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Building Manager RAG Chatbot API"}