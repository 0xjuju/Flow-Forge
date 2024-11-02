import json


class Build:

    @staticmethod
    def get_test_source_code():
        with open("resources/test_contract_source_code.json") as f:
            source_code = json.load(f)
            return source_code["bytecode"], source_code["abi"]

