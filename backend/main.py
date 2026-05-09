from apps.bootstrap import create_orchestrator


def main():
    orchestrator = create_orchestrator()

    while True:
        query = input(">> ")
        response = orchestrator.run(query)
        print(response)


if __name__ == "__main__":
    main()