from simplewot import ConsumedThing, WoT


def main():
    thing = WoT.consume("tests/test_file_001/td.json")

    assert isinstance(thing, ConsumedThing)


if __name__ == "__main__":
    main()
