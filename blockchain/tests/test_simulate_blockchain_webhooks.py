
from blockchain.web3_api import Blockchain
from .build_blockchain_data import Build
import decouple
from django.test import TestCase


class BlockchainSimulationTests(TestCase):

    def setUp(self):
        self.test_token_contract = decouple.config("TEST_TOKEN_CONTRACT")
        self.sepolia = Blockchain("ethereum", "sepolia")
        self.base_address = self.sepolia.ACCOUNT
        self.user_wallet = "0xbA1f6d33bc01A90020fE41a50e52EDD26B018068"
        self.bytecode, self.abi = Build.get_test_source_code()

    def test_simulate_webhook(self):

        self.sepolia.transfer_tokens(self.test_token_contract, self.user_wallet, 100)

