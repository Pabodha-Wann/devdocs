from typing import List, Dict
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import logging

from config import GROQ_API_KEY,GROQ_MODEL
from exceptions import LLMError

logger = logging.getLogger(__name__)

# Groq Wraper
class LLMClient:

    def __init__(self):
        try:
            self.client = ChatGroq(
                temperature=0.3,
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY
            )
            logger.info(f"LLM initialized: {GROQ_MODEL}")
        except Exception as e:
            logger.error(f"LLM init error: {str(e)}")
            raise LLMError(f"LLM initialization failed: {str(e)}")

# Generate answers with code context
    def generate_answer(
            self,
            chat_history:List[Dict[str,str]],
            retrieved_chunks:List[Dict[str,str]]
            ) -> str:
        
        print("Formatting code for the AI...")

        try:
            if not retrieved_chunks:
                return "I couldn't find relevent code for your question"
            
            # format context
            context_text = "\n\n---\n\n".join([
                f"File: {chunk['source']}\n{chunk['content']}\n```"
                for chunk in retrieved_chunks
            ])

            # convert history ist into readable text
            history_text = ""
            for msg in chat_history[:-1]: #skip last message
                role = "Human" if msg["role"] == "user" else "AI"
                history_text += f"{role}:{msg['content']}\n"

            current_question = chat_history[-1]["content"]

            prompt_template ="""
                You are a senior software engineer analyzing a codebase.
                Use the following pieces of retrieved code to answer the user's question.

                You have been provided with the Chat History of this conversation. Use it to understand context (like if the user says "how do I run it?", use the history to figure out what "it" is).

                If the answer is not in the code provided, just say "I cannot find the answer in the retrieved code files."
                Do not guess or make up code. 
                Explain your answer clearly and reference the file names when applicable.

                Chat History:
                {history}
                
                Context Code:
                {context}

                User Question:{question}

                Answer:"""

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["history","context","question"]
            )

            
            chain = prompt | self.client

            response = chain.invoke({
                "history":history_text,
                "context":context_text,
                "question":current_question
            })

            return response.content

        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise LLMError(f"failed to generate answer: {str(e)}")


llm = LLMClient()


    