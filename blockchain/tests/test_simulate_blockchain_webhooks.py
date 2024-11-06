from decimal import Decimal
import time

from blockchain.web3_api import Blockchain
from .build_blockchain_data import Build
from celery.signals import task_postrun
import decouple
from django.test import override_settings, TestCase


@override_settings(CELERY_TASK_ALWAYS_EAGER=False)
class BlockchainSimulationTests(TestCase):
    task_results = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        @task_postrun.connect(dispatch_uid="task_post_run_simulation")
        def task_monitor_handler(sender=None, **kwargs):
            cls.task_results.append(kwargs)

    def setUp(self):
        self.test_token_contract = decouple.config("TEST_TOKEN_CONTRACT")
        self.sepolia = Blockchain("ethereum", "sepolia")
        self.base_address = self.sepolia.ACCOUNT
        self.user_wallet = "0xbA1f6d33bc01A90020fE41a50e52EDD26B018068"
        self.bytecode, self.abi = Build.get_test_source_code()

    def test_simulate_webhook(self):

        transaction_hash = self.sepolia.transfer_tokens(self.test_token_contract, self.user_wallet, Decimal("100"),
                                                        self.abi)
        print("waiting for transaction to be included in block... ")

        receipt = self.sepolia.wait_for_transaction_receipt(transaction_hash)

        print(f"Receipt: {receipt}")

        task_found = False

        print("10 second delay for webhook latency")
        time.sleep(10)

        for task in self.task_results:
            print(task)


