import os
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import DeepEvalBaseLLM
import pytest
from app.llm import llm
from app.retrieval import search_codebase

# Custom Judge for DeepEval using existing Gemini client 
class GeminiJudge(DeepEvalBaseLLM):
    def __init__(self):
        # We reuse your existing Langchain Gemini client from app.llm
        self.model = llm.client

    def load_model(self):
        return self.model

    def _parse_content(self, content) -> str:
        if isinstance(content, list):
            return "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
        return str(content)

    def generate(self, prompt: str) -> str:
        # DeepEval passes a string prompt to the judge
        response = self.model.invoke(prompt)
        return self._parse_content(response.content)

    async def a_generate(self, prompt: str) -> str:
        # DeepEval also uses async generation to run tests faster
        response = await self.model.ainvoke(prompt)
        return self._parse_content(response.content)

    def get_model_name(self):
        return "Gemini (2.5-Flash)"




@pytest.mark.parametrize(
    "user_query, expected_output",
    [
        (
            "Where are the frontend pages implemented?",
            "The frontend pages are located directly within the app directory and its subdirectories like (tabs) and modals."
        ),
        (
            "How does authentication work?",
            "The repository does not have an authentication part implemented yet."
        ),
        (
            "What is the overall folder structure?",
            "The project contains an app directory at the root which holds pages, subdirectories for tabs and modals, and layout components."
        ),
        (
            "What database is used in this repository?",
            "The database used in this repository is SQLite."
        ),
        (
            "Are there any files related to querying GPA?",
            "Yes, there is a gpa.ts file in the queries folder."
        )
    ]
)
def test_rag_quality_evaluation(user_query, expected_output):
    # Setup test data
    repo_url = "https://github.com/Pabodha-Wann/Academia" # repo is ingested first!
    
    # We run a mock retrieval just to supply DeepEval with context.
    # The actual agent will do its own retrieval!
    chunks = search_codebase(user_query, repo_url)
    retrieved_context = [chunk["content"] for chunk in chunks]

    # Run the Agentic RAG
    from app.agent import run_agent
    chat_history = [{"role": "user", "content": user_query}]
    actual_answer = run_agent(chat_history, repo_url)


    # Create the DeepEval Test Case
    test_case = LLMTestCase(
        input=user_query,
        actual_output=actual_answer,
        retrieval_context=retrieved_context,
        expected_output=expected_output
    )

    # Setup the Metrics using our custom Gemini Judge
    gemini_judge = GeminiJudge()
    
    faithfulness_metric = FaithfulnessMetric(threshold=0.7, model=gemini_judge)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=gemini_judge)

    # Run the test and upload to Dashboard!
    assert_test(test_case, [faithfulness_metric, relevancy_metric])
