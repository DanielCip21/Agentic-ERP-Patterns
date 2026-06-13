"""Quickstart: Azure AI Agent — live API example.

Prerequisites
-------------
1. Deploy an Azure OpenAI resource and a chat model (e.g. gpt-4o):
   Azure portal > Azure OpenAI > Deployments > Deploy model

2. Optionally, deploy an Azure AI Search resource and create an index.

3. Copy .env.example to .env and fill in your credentials:
   AZURE_OPENAI_ENDPOINT=https://yourresource.openai.azure.com
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   AZURE_SEARCH_ENDPOINT=https://yoursearch.search.windows.net  # optional
   AZURE_SEARCH_API_KEY=your-search-key                         # optional
   ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_azure_ai.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.azure_ai import AzureAIConfig
from agentic_erp.ai.azure_ai_agent import AzureAIAgent

load_dotenv()


def main() -> None:
    config = AzureAIConfig(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
        search_api_key=os.getenv("AZURE_SEARCH_API_KEY", ""),
    )

    agent = AzureAIAgent(config=config)

    print("=== Azure AI Agent ===\n")

    # Example 1: pure chat — no document URL needed
    response = agent.run(
        "Summarise what Azure AI Document Intelligence can do for invoice processing "
        "in 3 bullet points."
    )
    print("Document Intelligence Overview:\n", response, "\n")

    # Example 2: analyze a real document
    response = agent.run(
        "Analyze this document and extract key fields: "
        "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples"
        "/master/curl/form-recognizer/rest-api/invoice.pdf"
    )
    print("Invoice Analysis:\n", response, "\n")

    # Example 3 (requires AZURE_SEARCH_ENDPOINT — uncomment to run):
    # response = agent.run(
    #     "Search the knowledge base index 'kb-index' for documents about "
    #     "'purchase order approval workflow'. Return the top 3 results."
    # )
    # print("Knowledge Base Search:\n", response)


if __name__ == "__main__":
    main()
