from bootstrap import create_orchestrator


def main():
    orchestrator = create_orchestrator()

    while True:
        query = input(">> ")

        if query in ["/exit", "/quit", "/bye"]:
            break
        for chunk in orchestrator.run(query):
            print(chunk, end="", flush=True)

        print()


if __name__ == "__main__":
    main()
