from orchestrator import Orchestrator
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


def main():

    print("[MAIN] templates", str(TEMPLATES_DIR))

    orchestrator = Orchestrator(str(TEMPLATES_DIR))
    orchestrator.register()
    orchestrator.run()


if __name__ == "__main__":
    main()
