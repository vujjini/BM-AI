from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from services.vector_store import vector_store_service
from config import settings, logger
from typing import Dict, Any
import re

class ChatService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )

        # Template for enhancing the user's prompt
        self.enhancement_template = """
            You are an expert at refining and expanding user queries for better information retrieval.

            Your task:
            1. Correct any grammatical issues.
            2. Clarify vague or ambiguous wording while keeping the original intent.
            3. Expand the query by including:
            - Key terminology and relevant definitions.
            - Common synonyms or alternate phrases used for the same concept.
            - Related entities, domains, or contexts that could improve recall.
            4. Ensure the result is concise, natural-sounding, and optimized for semantic retrieval systems (e.g., vector search).

            Output only the enhanced query.

            Original question: {question}
            """


        
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
    
    async def enhance_question(self, question: str) -> Dict[str, str]:
        """Enhance the user's question for better retrieval and response"""
        try:
            # Create a prompt for enhancement
            prompt = self.enhancement_template.format(question=question)
            
            # Get enhanced query from LLM
            response = await self.llm.ainvoke(prompt)
            
            # Parse the response
            enhanced = response.content
            return enhanced
                
        except Exception as e:
            logger.error(f"Error enhancing question: {e}")
            return question
    
    # async def get_answer(self, question: str) -> Dict[str, Any]:
    #     """Get an answer for the given question using enhanced retrieval"""
    #     if not self.qa_chain:
    #         return {
    #             "answer": "The system is not ready. Please try again later.",
    #             "sources": []
    #         }
        
    #     try:
    #         # Step 1: Enhance the question
    #         enhanced = await self.enhance_question(question)
    #         logger.info(f"Enhanced query for retrieval: {enhanced}")
            
    #         # Step 2: Use enhanced query for retrieval
    #         result = self.qa_chain.invoke({
    #             "query": enhanced
    #         })
            
    #         # Extract and format sources
    #         sources = []
    #         if "source_documents" in result:
    #             seen_files = set()
    #             for doc in result["source_documents"]:
    #                 filename = doc.metadata.get("filename", "Unknown")
    #                 if filename not in seen_files:
    #                     sources.append({
    #                         "filename": filename,
    #                         "pdf_path": doc.metadata.get("pdf_path")
    #                     })
    #                     seen_files.add(filename)
            
    #         return {
    #             "answer": result.get("result", "I couldn't find a good answer."),
    #             "sources": sources,
    #             "enhanced_question": enhanced  # For debugging
    #         }
# In chat_service.py, update the get_answer method:
    async def get_answer(self, question: str) -> Dict[str, Any]:
        if not self.qa_chain:
            return {
                "answer": "The system is not ready. Please try again later.",
                "sources": []
            }
        
        try:
            # Step 1: Get the retriever
            retriever = vector_store_service.get_retriever(k=2, score_threshold=0.3)
            
            # Step 2: Use the correct method name for Qdrant
            docs = retriever.invoke(question)  # Changed from get_relevant_documents to invoke
            
            if not docs:
                # Try with enhanced query if first attempt fails
                enhanced = await self.enhance_question(question)
                docs = retriever.invoke(enhanced)  # Changed here too
            
            if not docs:
                return {
                    "answer": "I couldn't find any relevant information in the documents.",
                    "sources": []
                }

            # Log the retrieved documents for debugging
            logger.info(f"Retrieved {len(docs)} documents")
            for i, doc in enumerate(docs):
                logger.info(f"Doc {i+1}:")
                logger.info(f"  Source: {doc.metadata.get('filename', 'Unknown')}")
                logger.info(f"  Content: {doc.page_content[:200]}...")

            # Continue with answer generation...
            context = "\n\n".join([f"Source: {doc.metadata.get('filename', 'Unknown')}\n{doc.page_content}" 
                                for doc in docs])
            
            result = self.llm.invoke(
                self.prompt_template.format(
                    context=context,
                    question=question
                )
            )

        #     # Extract sources from the answer
        #     sources = []
        #     source_matches = re.findall(r'\[source:\s*([^\]]+)\]', result.content, re.IGNORECASE)
        #     for match in source_matches:
        #         src = match.strip().lower()
        #         # Find the matching document to get full metadata
        #         for doc in docs:
        #             if doc.metadata.get("filename", "").lower() == src:
        #                 sources.append({
        #                     "filename": doc.metadata.get("filename", "Unknown"),
        #                     "pdf_path": doc.metadata.get("pdf_path")
        #                 })
        #                 break

        #     # Clean up the answer
        #     clean_answer = re.sub(r'\s*\[source:[^\]]+\]', '', result.content).strip()

        #     return {
        #         "answer": clean_answer,
        #         "sources": sources,
        #         "enhanced_question": question
        #     }

        # except Exception as e:
        #     logger.error(f"Error getting answer: {e}", exc_info=True)
        #     return {
        #         "answer": "Sorry, I encountered an error while processing your request.",
        #         "sources": []
        #     }
        # Extract sources from the retrieved documents
            sources = []
            seen_files = set()
            for doc in docs:
                filename = doc.metadata.get("filename", "Unknown")
                if filename not in seen_files:
                    sources.append({
                        "filename": filename,
                        "pdf_path": doc.metadata.get("pdf_path")
                    })
                    seen_files.add(filename)

            return {
                "answer": result.content,
                "sources": sources,
                "enhanced_question": question
            }

        except Exception as e:
            logger.error(f"Error getting answer: {e}", exc_info=True)
            return {
                "answer": "Sorry, I encountered an error while processing your request.",
                "sources": []
            }

# Global instance
chat_service = ChatService()