
from blockchain.web3_api import Blockchain
import decouple
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Request testnet tokens for specified chain"

    def handle(self, *args, **options):
        chain = input("Chain: ")
        network = input("Network: ")
        blockchain = Blockchain(chain, network)
        blockchain.request_testnet_tokens(decouple.config("WALLET_ADDRESS"))

