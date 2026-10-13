from multiprocessing import Queue as MPQueue
from .create_agent import create_agent
from agents.models import LLMQueueItem
from config import Settings
from text_to_speech import PiperService, PiperConfig


def run_agent(llm_queue: MPQueue):

    orchestrator = create_agent()
    settings = Settings()
    piper = PiperService(voice=settings.VOICE, config=PiperConfig())

    while True:
        query_dict = llm_queue.get()

        try:
            query = LLMQueueItem(**query_dict)
            if query.text.lower() in ["/exit", "/quit", "/bye"]:
                break

            full_response = ""
            for chunk in orchestrator.run(query.text):
                print(chunk, end="", flush=True)
                full_response += chunk

            print()

            if full_response.strip():
                piper.synthesize(full_response)

        except Exception as e:
            print(f"Error: {e}")
            continue
