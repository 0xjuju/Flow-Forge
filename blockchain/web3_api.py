from decimal import Decimal

from web3 import Web3
from decouple import config
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from solcx import compile_source, install_solc, compile_solc
import solcx.exceptions
import requests


class Blockchain:
    def __init__(self, chain: str, network_type: str):
        """
        Initialize the blockchain interactor with specified chain and network type.

        :param chain: The blockchain to interact with (currently supports only "ethereum").
        :param network_type: Specify "mainnet" or "testnet" (currently supports only "mainnet" and "sepolia" for Ethereum).
        """
        self.chain = chain.lower()
        self.network_type = network_type.lower()
        self.API_KEY = config("ALCHEMY_API_KEY")
        self.PRIVATE_KEY = config("PRIVATE_KEY")
        self.ACCOUNT = Account.from_key(self.PRIVATE_KEY).address

        if self.chain != "ethereum":
            raise ValueError("Currently, only the Ethereum chain is supported.")

        self.NETWORK_URLS = {
            "mainnet": f"https://eth-mainnet.alchemyapi.io/v2/{self.API_KEY}",
            "sepolia": f"https://eth-sepolia.g.alchemy.com/v2/{self.API_KEY}"
        }

        supported_networks = ["mainnet", "sepolia"]
        if self.network_type not in supported_networks:
            raise ValueError(f"Unsupported network type. Supported networks are: {', '.join(supported_networks)}.")

        self.web3 = self._setup_web3()
        self.TOKEN_ABI = None  # Placeholder for the ERC-20 token ABI

    def _setup_web3(self) -> Web3:
        """
        Set up the Web3 instance based on the specified chain and network type.

        :return: Web3 instance connected to the specified network.
        """

        rpc_url = self.NETWORK_URLS[self.network_type]

        web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not web3.is_connected():
            raise ConnectionError(f"Unable to connect to the {self.network_type} network.")
        return web3

    def build_transaction(self, from_address: str, gas: int = None, gas_price: int = None, nonce: int = None,
                          **kwargs) -> dict[str, any]:
        """

        :param from_address: Address creating the transaction
        :param gas: Amount of gas required for transaction
        :param gas_price: How much ether to use for gas
        :param nonce: transaction index for account. defaults to latest
        :param kwargs: Optional arguments for transaction
        :return: Unsigned blockchain transaction
        """

        acceptable_attributes = {"from", "to", "gas", "gasPrice", "nonce", "data", "value", "maxFeePerGas",
                                 "maxPriorityFeePerGas"}

        if nonce is None:
            nonce = self.get_nonce()

        transaction = {
            "from": from_address,
            "nonce": nonce,
        }

        if kwargs.get("data"):
            transaction["data"] = kwargs.get("data")

        if gas is None:
            gas = self.web3.eth.estimate_gas(transaction)

        if gas_price is None:
            gas_price = self.web3.eth.gas_price

        if not all(i in acceptable_attributes for i in kwargs):
            raise ValueError(f"1 of more keyword arguments are invalid. Options are: {kwargs}")

        transaction["gas"] = gas
        transaction["gasPrice"] = gas_price

        transaction.update(kwargs)

        return transaction

    def check_balance(self, token_contract_address: str, address: str, abi: list) -> Decimal:
        """
        Check the balance of a given token contract for a specific address.

        :param token_contract_address: The address of the ERC-20 token contract.
        :param address: The address whose token balance is to be checked.
        :param abi: The ABI of the token contract.
        :return: Balance of the given address for the specified token contract, formatted as a human-readable number.
        """
        contract = self.web3.eth.contract(address=token_contract_address, abi=abi)

        balance = contract.functions.balanceOf(address).call()
        decimals = contract.functions.decimals().call()

        # Convert to a human-readable number
        human_readable_balance = Decimal(balance) / Decimal(10 ** decimals)
        return human_readable_balance

    def deploy_contract(self, name: str, symbol: str, decimals: int, initial_supply: int) -> str:
        """
        Compile and deploy contract to blockchain

        :param name: Token name
        :param symbol: Token Symbol
        :param decimals: Number of decimals for token
        :param initial_supply: Supply of token
        :return: Contract address of the deployed token
        """

        bytecode, abi = self.compile_contract(
            name=name,
            symbol=symbol,
            decimals=decimals,
            initial_supply=initial_supply
        )

        contract = self.create_contract(bytecode)
        return contract

    def get_nonce(self) -> int:
        """
        :return: Transaction count of address
        """
        return self.web3.eth.get_transaction_count(self.ACCOUNT)

    def broadcast_transaction(self, raw_transaction: bytes) -> bytes:
        """
        Broadcast the signed transaction to the blockchain
        :param raw_transaction: raw signed transaction
        :return: Hash of transaction after it's included in the block
        """
        return self.web3.eth.send_raw_transaction(raw_transaction)

    def sign_transaction(self, transaction: dict[str, any]) -> SignedTransaction:
        """
        Sign a transaction using private keys
        :param transaction: transaction parameters
        :return: SignedTransaction containing rawSignature and other metadata after tx is successfully signed
        """
        return self.web3.eth.account.sign_transaction(transaction, private_key=self.PRIVATE_KEY)

    def test_connection(self) -> bool:
        """
        Test if the connection to the blockchain network is successful.

        :return: True if connected, False otherwise.
        """
        is_connected = self.web3.is_connected()

        if is_connected:
            print(f"Successfully connected to the {self.network_type} network on the {self.chain} chain.")
        else:
            print(f"Failed to connect to the {self.network_type} network on the {self.chain} chain.")
        return is_connected

    def wait_for_transaction_receipt(self, transaction_hash: bytes, timeout=120):
        """

        :param transaction_hash: Transaction hash of signed transaction
        :param timeout: Number of seconds to wait for transaction to be included in the block
        :return: Transaction receipt containing blockHash, blockNumber, Logs etc.
        """
        return self.web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=timeout)

    def compile_contract(self, name: str, symbol: str, decimals: int, initial_supply: int):
        """
        Compile the ERC-20 smart contract with the specified parameters.

        :param name: The name of the token.
        :param symbol: The symbol of the token.
        :param decimals: The number of decimals the token will use.
        :param initial_supply: The initial supply of tokens.
        :return: The compiled bytecode and ABI of the contract.
        """

        try:
            # Install Solidity compiler version
            install_solc("0.8.20")
        except solcx.exceptions.SolcInstallationError as e:
            print(e)
            print("Now attempt to compile solidity compiler from its source code")
            compile_solc("0.8.20")

        # Solidity source code for ERC-20 token
        erc20_source_code = f"""
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.20;

        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

        contract MyToken is ERC20 {{
            constructor() ERC20("{name}", "{symbol}") {{
                _mint(msg.sender, {initial_supply} * (10 ** uint256({decimals})));}}}}
        """

        # Compile the contract
        compiled_sol = compile_source(
            erc20_source_code,
            output_values=["abi", "bin"],
            allow_paths=["./node_modules"]
        )

        contract_interface = compiled_sol["<stdin>:MyToken"]
        # Set the ABI
        self.TOKEN_ABI = contract_interface["abi"]
        bytecode = contract_interface["bin"]

        return bytecode, self.TOKEN_ABI

    def create_contract(self, bytecode: str, **kwargs) -> str:
        """
        Deploy a new ERC-20 smart contract to the blockchain.

        :param bytecode: The compiled bytecode of the ERC-20 contract.
        :return: The address of the deployed contract.
        """

        # Get transaction count for wallet
        nonce = self.get_nonce()

        # Create the contract deployment transaction
        transaction = self.build_transaction(self.ACCOUNT, nonce=nonce, data=bytecode, **kwargs)

        # Sign and send the transaction
        signed_tx = self.sign_transaction(transaction)
        tx_hash = self.broadcast_transaction(signed_tx.raw_transaction)

        # Wait for the transaction receipt
        tx_receipt = self.wait_for_transaction_receipt(tx_hash)

        contract_address = tx_receipt["contractAddress"]

        print(f"Contract deployed at address: {contract_address}")
        return contract_address

    def request_testnet_tokens(self, address: str):
        """
        Request testnet tokens using Alchemy's faucet API for the specified address.

        :param address: The Ethereum address to receive testnet tokens.
        """

        faucet_url = f"https://faucets.chain.link/{self.network_type}"
        data = {
            "address": address,
            "network": self.network_type
        }

        response = requests.post(faucet_url, json=data)

        if response.status_code == 200:
            print(f"Successfully requested {self.network_type} testnet tokens for address: {address}")
        else:
            print(
                f"Failed to request {self.network_type} testnet tokens. Status code: {response.status_code}, Response: {response.text}")

    def transfer_tokens(self, token_contract_address: str, to_address: str, amount: Decimal, abi: list) -> str:
        """
        Transfer tokens from the connected account to another address.

        :param token_contract_address: The address of the ERC-20 token contract.
        :param to_address: The recipient address.
        :param amount: The amount of tokens to transfer.
        :param abi: The ABI of the token contract.
        :return: Transaction hash of the transfer.
        """
        contract = self.web3.eth.contract(address=token_contract_address, abi=abi)
        decimals = contract.functions.decimals().call()
        value = int(amount * (10 ** decimals))

        # Build the transaction
        tx = {
            'chainId': self.web3.eth.chain_id,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.get_nonce(),
            'from': self.ACCOUNT,
        }
        # estimate gas, then add value to transaction
        tx["gas"] = self.web3.eth.estimate_gas(tx)

        transaction = contract.functions.transfer(to_address, value).build_transaction(tx)

        signed_tx = self.sign_transaction(transaction)
        tx_hash = self.broadcast_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()


# Example usage
if __name__ == "__main__":
    pass
    # # Load environment variables
    # chain = "ethereum"
    # network_type = "sepolia"
    #
    # # Instantiate the BlockchainInteractor
    # blockchain_interactor = Blockchain(chain=chain, network_type=network_type)
    #
    # # Test connection
    # blockchain_interactor.test_connection()
    #
    # # Compile contract
    # token_name = "MyToken"
    # token_symbol = "MTK"
    # token_decimals = 18
    # initial_supply = 1000000
    # bytecode, abi = blockchain_interactor.compile_contract(
    #     name=token_name,
    #     symbol=token_symbol,
    #     decimals=token_decimals,
    #     initial_supply=initial_supply
    # )
    #
    # # Deploy contract instance
    # try:
    #     contract_address = blockchain_interactor.create_contract(bytecode=bytecode)
    # except ValueError as e:
    #     print(f"Error: {e}")
    #
    # # Request Sepolia testnet tokens
    # recipient_address = "0xYourEthereumAddressHere"  # Replace with your Ethereum address
    # blockchain_interactor.request_testnet_tokens(address=recipient_address, testnet_name="sepolia")
