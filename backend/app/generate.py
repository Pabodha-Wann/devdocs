import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()

my_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    temperature=0,
    model="llama-3.3-70b-versatile",
    api_key=my_key
)

def generate_answer(query:str,retrieved_chunks:list) -> str:
    print("Formatting code for the AI...")

    if not retrieved_chunks:
        return "I couldn't find relevent code for your question"
    
    context_text = "\n\n---\n\n".join([
        f"File: {chunk['source']}\n{chunk['content']}"
        for chunk in retrieved_chunks
    ])

    prompt_template = """
        You are a senior software engineer analyzing a codebase.
        Use the following pieces of retrieved code to answer the user's question.
        If the answer is not in the code provided, just say "I cannot find the answer in the retrieved code files."
        Do not guess or make up code. 
        Explain your answer clearly and reference the file names when applicable.
        
        Context Code:
        {context}

        User Question:{question}

        Answer:
    """

    prompt = PromptTemplate(template=prompt_template,input_variables=["context","question"])

    

    chain = prompt | llm

    response = chain.invoke({"context":context_text,"question":query})

    return response.content


    