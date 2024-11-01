
import json

from blockchain.web3_api import Blockchain
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deploys a token contract"

    def handle(self, *args, **options):
        chain = input("Chain > ")
        network = input("Network > ")
        blockchain = Blockchain(chain, network)

        # print("Now let's create a token. Please input the token attributes >")
        #
        # name = input("Name > ")
        # symbol = input("Symbol > ")
        # decimals = int(input("Decimals > "))
        # supply = int(input("Initial Supply > "))
        # print("Token contract will now be compiled and deployed to blockchain. It may take up to 120 seconds to receive"
        #       " transaction receipt...")
        #
        # contract = blockchain.deploy_contract(name, symbol, decimals, supply)

        with open("resources/test_contract_source_code.json") as f:
            source_code = json.load(f)
            bytecode = source_code["bytecode"]
            abi = source_code["abi"]
            contract = blockchain.create_contract(bytecode)
            deployer = blockchain.ACCOUNT

            balance = blockchain.check_balance(contract, deployer, abi)
            print(f"An initial supply of {balance} for token {contract} has been added to deployer wallet {deployer}")




