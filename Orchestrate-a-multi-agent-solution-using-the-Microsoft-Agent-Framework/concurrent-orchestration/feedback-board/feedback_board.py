"""
Customer Feedback Insight Board — concurrent orchestration lab (STARTER).

Goal: broadcast ONE customer review to three specialist agents that run
IN PARALLEL, then aggregate their independent analyses into one report.

Fill in the TODOs. Each TODO maps to a step in
"Implement the concurrent orchestration pattern" from the module notes.
The full reference solution is in README.md if you get stuck.
"""
import os
import asyncio
from pathlib import Path

# Add references
from agent_framework import Message
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()


async def main():
    # Clear the console
    os.system("cls" if os.name == "nt" else "clear")

    # Load the sample feedback and let the user pick one review
    reviews = (
        (Path(__file__).parent / "data.txt")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    print("Sample customer feedback:\n")
    for i, review in enumerate(reviews, start=1):
        print(f"{i}. {review}")
    choice = int(input("\nPick a review number to analyze: ")) - 1
    feedback = reviews[choice]

    # Run the async orchestration
    await analyze_feedback(feedback)


async def analyze_feedback(feedback: str):
    # STEP 1 — Create your chat client
    # TODO: build an AzureOpenAIChatClient using AzureCliCredential and the
    #       PROJECT_ENDPOINT / MODEL_DEPLOYMENT_NAME environment variables.
    chat_client = AzureOpenAIChatClient(
        credential=AzureCliCredential(),
        endpoint=os.environ["PROJECT_ENDPOINT"],
        deployment_name=os.environ["MODEL_DEPLOYMENT_NAME"],
    )

    # STEP 2 — Define your agents (one specialist per perspective)
    sentiment_agent = chat_client.as_agent(
        name="SentimentAnalyst",
        instructions=(
            "You analyze customer feedback sentiment. Return: overall sentiment "
            "(Positive/Neutral/Negative), a 1-5 satisfaction score, and the key "
            "emotional drivers in 2 bullet points. Be concise."
        ),
    )
    feature_agent = chat_client.as_agent(
        name="FeatureRequestExtractor",
        instructions=(
            "You extract product feature requests from customer feedback. List each "
            "explicit or implied feature request as a short bullet. If there are "
            "none, say 'No feature requests detected.' Be concise."
        ),
    )
    churn_agent = chat_client.as_agent(
        name="ChurnRiskAssessor",
        instructions=(
            "You assess churn risk from customer feedback. Return a risk level "
            "(Low/Medium/High), the warning signals you found, and one recommended "
            "retention action. Be concise."
        ),
    )

    # STEP 3 — Build the concurrent workflow
    workflow = (
        ConcurrentBuilder(participants=[sentiment_agent, feature_agent, churn_agent]).build()
    )

    # STEP 4 — Run the workflow (parallel)
    events = await workflow.run(feedback)

    # STEP 5 — Process the results
    outputs = events.get_outputs()

    # STEP 6 — Handle the aggregated responses
    # TODO: iterate the aggregated messages and print author_name + text.
    print(f"\n=== Insight Board report for: {feedback!r} ===\n")
    for output in outputs:
        for message in output:          # each output is a list of messages
            print(f"--- {message.author_name} ---")
            print(message.text, "\n")


if __name__ == "__main__":
    asyncio.run(main())
