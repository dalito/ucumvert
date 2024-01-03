from ucumvert.parser import lark_parser


def main():
    print("Enter UCUM units to parse, or 'q' to quit.")
    while True:
        s = input("> ")
        if s in "qQ":
            break
        try:
            print(lark_parser(s))
        except Exception as e:
            print(e)


def run_cli_app():
    main()


if __name__ == "__main__":
    main()
