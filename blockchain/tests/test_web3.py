from django.test import TestCase
from unittest.mock import Mock, patch
from blockchain.web3_api import Blockchain


class BlockchainTests(TestCase):
    def setUp(self):
        """
        Set up the test case by initializing the Blockchain instance.
        """
        self.chain = "ethereum"
        self.network_type = "sepolia"
        self.blockchain = Blockchain(chain=self.chain, network_type=self.network_type)

    @patch("blockchain.web3_api.Blockchain._setup_web3")
    def test_connection(self, mock_setup_web3):
        """
        Test if the blockchain instance can successfully connect to the network.
        """
        mock_setup_web3.return_value.is_connected.return_value = True
        connected = self.blockchain.test_connection()
        self.assertTrue(connected, "The blockchain should be connected.")

    @patch("blockchain.web3_api.compile_source")
    @patch("blockchain.web3_api.install_solc")
    def test_compile_contract(self, mock_install_solc, mock_compile_source):
        """
        Test if the smart contract can be compiled successfully.
        """
        mock_install_solc.return_value = None
        mock_compile_source.return_value = {
            "<stdin>:MyToken": {
                "abi": [],
                "bin": "0x12345"
            }
        }
        bytecode, abi = self.blockchain.compile_contract(
            name="TestToken", symbol="TT", decimals=18, initial_supply=1000
        )
        self.assertEqual(bytecode, "0x12345", "The bytecode should match the mocked bytecode.")
        self.assertEqual(abi, [], "The ABI should match the mocked ABI.")

    @patch("blockchain.web3_api.Web3")  # Mock the Web3 class itself
    @patch("blockchain.web3_api.Account.from_key")
    @patch("blockchain.web3_api.Blockchain._setup_web3")
    def test_create_contract(self, mock_setup_web3, mock_from_key, mock_web3):
        """
        Test if the smart contract can be deployed successfully.
        """
        # Set up mock for account
        mock_from_key.return_value.address = "0x236349bAb48d2fDF23E5115b0899Bb58eFE4C742"

        # Connect the Mock setup to the web3 instance
        mock_web3 = mock_web3.return_value
        mock_setup_web3.return_value = mock_web3

        # Set up mock for web3.eth
        mock_web3.eth.get_transaction_count.return_value = 1
        mock_web3.eth.send_raw_transaction.return_value = "0xTransactionHash"

        # Set the return value for wait_for_transaction_receipt to a dictionary
        mock_web3.eth.wait_for_transaction_receipt.return_value = {
            "contractAddress": "0xMockedContractAddress"
        }

        # Mock the sign_transaction method return value
        signed_tx_mock = Mock()
        signed_tx_mock.rawTransaction = '0xSignedTransaction'
        signed_tx_mock.hash = '0xTransactionHash'
        signed_tx_mock.r = 1234567890123456789012345678901234567890  # Large integer simulating signature r
        signed_tx_mock.s = 9876543210987654321098765432109876543210  # Large integer simulating signature s
        signed_tx_mock.v = 27  # Chain ID or recovery ID, typically 27 or 28

        # Assign the mocked return value for sign_transaction
        mock_web3.eth.account.sign_transaction.return_value = signed_tx_mock

        # Set up Blockchain instance and mock valid bytecode
        blockchain = Blockchain(chain="ethereum", network_type="sepolia")
        bytecode = "0x600060005560236070527f"  # A mock valid-looking hexadecimal bytecode

        # Call the create_contract method
        contract_address = blockchain.create_contract(bytecode=bytecode)

        # Assertions
        self.assertEqual(contract_address, "0xMockedContractAddress",
                         "The contract address should match the mocked address.")

    @patch("blockchain.web3_api.requests.post")
    def test_request_testnet_tokens(self, mock_requests_post):
        """
        Test if testnet tokens can be requested successfully.
        """
        mock_requests_post.return_value.status_code = 200
        address = "0xYourEthereumAddressHere"
        self.blockchain.request_testnet_tokens(address=address)
        mock_requests_post.assert_called_once()
        self.assertEqual(mock_requests_post.call_args[1]["json"], {"address": address}, "The request payload should contain the correct address.")
