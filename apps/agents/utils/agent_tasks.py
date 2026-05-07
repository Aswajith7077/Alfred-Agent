from multiprocessing import Queue as MPQueue
from .create_agent import create_agent
from agents.models import LLMQueueItem

def run_agent(llm_queue: MPQueue):

    orchestrator = create_agent()
    while True:
        query_dict = llm_queue.get()

        try:
            query = LLMQueueItem(**query_dict)
            if query.text.lower() in ["/exit", "/quit", "/bye"]:
                break
            for chunk in orchestrator.run(query.text):
                print(chunk, end="", flush=True)

            print()

        except Exception as e:
            print(f"Error: {e}")
            continue
