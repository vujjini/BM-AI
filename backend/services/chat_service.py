from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from services.vector_store import vector_store_service
from config import settings

class ChatService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        self.prompt_template = PromptTemplate(
            template="""
            You are a helpful assistant for building managers. Use the provided context 
            from shift logs to answer questions accurately and helpfully in a human like manner.
            
            If the context doesn't contain relevant information, say so clearly.
            Keep your answers concise but informative.
            
            Context from shift logs:
            {context}
            
            Question: {question}
            
            Answer:
            """,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = None
        self._setup_qa_chain()
    
    def _setup_qa_chain(self):
        """Setup the QA chain"""
        retriever = vector_store_service.get_retriever()
        if retriever:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
    
    def get_answer(self, question: str) -> dict:
        """Get answer for a question"""
        if not self.qa_chain:
            return {
                "answer": "Sorry, the system is not ready yet. Please upload some files first.",
                "sources": []
            }
        
        try:
            result = self.qa_chain.invoke({"query": question})
            return {
                "answer": result["result"],
                "sources": [doc.metadata.get("filename", "Unknown") for doc in result["source_documents"]]
            }
        except Exception as e:
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": []
            }

# Global instance
chat_service = ChatService()