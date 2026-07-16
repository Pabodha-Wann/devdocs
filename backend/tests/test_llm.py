from app.llm import llm
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from unittest.mock import patch

@patch("langchain_groq.ChatGroq._generate")
def test_generate_answer_formatting(mock_generate):
    # """Test that our LLM class correctly formats the code chunks and history into a prompt."""
    
    chat_history = [
        {"role": "user", "content": "How do I run this?"},
        {"role": "assistant", "content": "You run npm run dev."},
        {"role": "user", "content": "Where is the frontend code?"}
    ]
    
    retrieved_chunks = [
        {"source": "frontend/package.json", "content": '"scripts": {"dev": "next dev"}'}
    ]
    
    # Setup the exact response object that LangChain's internal _generate method expects to return
    mock_generate.return_value = ChatResult(
        generations=[ChatGeneration(message=AIMessage(content="The frontend code is in the frontend folder."))]
    )
    
    # Execution
    answer = llm.generate_answer(chat_history, retrieved_chunks)
    
    # Assertions
    assert answer == "The frontend code is in the frontend folder."
    
    # In Langchain, _generate receives a list of BaseMessage objects.
    messages_sent = mock_generate.call_args[0][0]
    formatted_prompt = messages_sent[0].content
    
    # Check that everything was formatted into the final string
    assert "frontend/package.json" in formatted_prompt
    assert '"scripts": {"dev": "next dev"}' in formatted_prompt
    assert "Human:How do I run this?" in formatted_prompt
    assert "Where is the frontend code?" in formatted_prompt

def test_generate_answer_no_chunks():
    # """Test how the LLM responds when the database finds 0 code chunks."""
    
    chat_history = [{"role": "user", "content": "What is the meaning of life?"}]
    retrieved_chunks = [] # Empty!
    
    answer = llm.generate_answer(chat_history, retrieved_chunks)
    
    assert answer == "I couldn't find relevent code for your question"
