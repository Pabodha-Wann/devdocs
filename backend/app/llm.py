from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import logging

from config import GEMINI_API_KEY, GEMINI_MODEL
from exceptions import LLMError

logger = logging.getLogger(__name__)

# Gemini Wrapper
class LLMClient:

    def __init__(self):
        try:
            self.client = ChatGoogleGenerativeAI(
                temperature=0.3,
                model=GEMINI_MODEL,
                google_api_key=GEMINI_API_KEY
            )
            logger.info(f"LLM initialized: {GEMINI_MODEL}")
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
                You have access to codebase context to answer the user's questions.

                IMPORTANT RULES:
                1. If you use information from the provided context (including directory structures), do not mention that you read it from a "file", "chunk", "map", or "DIRECTORY_TREE". Speak naturally as an engineer who just knows the codebase.
                2. If the context does not contain enough information to answer the question, do not say "I cannot find the answer in the retrieved code files." Instead, say something natural like: "I don't have enough context about that part of the codebase to give a definitive answer." or "That doesn't seem to be covered in the parts of the codebase I can see right now."
                3. Do not guess or make up code.
                4. When you DO find the answer, explain it clearly and reference the relevant file names (e.g., "In `src/app/page.tsx`, we can see...").
                5. Structure your answer beautifully using Markdown formatting! Use bullet points, bold text for emphasis, and backticks for file paths, variable names, or code snippets. Keep paragraphs short and scannable so it is highly user-friendly and easy to read. DO NOT output massive walls of text.

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


    