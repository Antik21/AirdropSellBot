import time
import os
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger

# Настройка логирования
logger.add("metamask_to_exchange.log", rotation="1 MB", level="INFO")

# Загрузка переменных из .env
load_dotenv()

# Подключение к сети BNB (Binance Smart Chain)
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"  # Публичный RPC-эндпоинт BNB
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))

# Проверка подключения
if not w3.is_connected():
    logger.error("Не удалось подключиться к BSC RPC")
    exit(1)
logger.info("Подключение к BSC успешно")

# Адреса и ключи из .env
METAMASK_PRIVATE_KEY = os.getenv("METAMASK_PRIVATE_KEY")
EXCHANGE_WALLET_ADDRESS = os.getenv("EXCHANGE_WALLET_ADDRESS")  # Зашитый адрес кошелька биржи
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")  # Адрес контракта токена

# Проверка корректности адресов
if not all([METAMASK_PRIVATE_KEY, EXCHANGE_WALLET_ADDRESS, TOKEN_CONTRACT_ADDRESS]):
    logger.error("Не все необходимые параметры найдены в .env")
    exit(1)
if not w3.is_address(EXCHANGE_WALLET_ADDRESS) or not w3.is_address(TOKEN_CONTRACT_ADDRESS):
    logger.error("Некорректный адрес кошелька биржи или контракта токена")
    exit(1)

# Преобразование адресов в checksum-формат
try:
    EXCHANGE_WALLET_ADDRESS = w3.to_checksum_address(EXCHANGE_WALLET_ADDRESS)
    TOKEN_CONTRACT_ADDRESS = w3.to_checksum_address(TOKEN_CONTRACT_ADDRESS)
except ValueError as e:
    logger.error(f"Некорректный формат адреса: {e}")
    exit(1)

# Получение адреса MetaMask из приватного ключа
account = w3.eth.account.from_key(METAMASK_PRIVATE_KEY)
METAMASK_ADDRESS = account.address
logger.info(f"Адрес MetaMask: {METAMASK_ADDRESS}")

# ABI для стандартного ERC-20 токена (balanceOf и transfer)
TOKEN_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    }
]

# Создание контракта
token_contract = w3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=TOKEN_ABI)


def get_token_balance(address: str) -> float:
    """Получение баланса токена в читаемом формате (с учётом decimals)."""
    try:
        balance_wei = token_contract.functions.balanceOf(address).call()
        # Предполагаем 18 decimals (стандарт для большинства токенов на BSC)
        balance = balance_wei / 10 ** 18
        return balance
    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {e}")
        return 0.0

def transfer_tokens(amount: float):
    """Перевод токенов на адрес биржи с высоким газом и приоритетом (EIP-1559)."""
    try:
        # Получаем базовую цену газа
        gas_price = w3.eth.gas_price
        # Устанавливаем параметры EIP-1559
        max_fee_per_gas = int(gas_price * 2.5)  # Максимальная плата за газ
        max_priority_fee_per_gas = int(gas_price * 1.5)  # Приоритетная плата для майнеров
        gas_limit = 100000  # Высокий gasLimit для надёжности

        # Конвертируем сумму в wei (с учётом decimals)
        amount_wei = int(amount * 10**18)

        # Создаём транзакцию с параметрами EIP-1559
        tx = token_contract.functions.transfer(
            EXCHANGE_WALLET_ADDRESS,
            amount_wei
        ).build_transaction({
            'from': METAMASK_ADDRESS,
            'gas': gas_limit,
            'maxFeePerGas': max_fee_per_gas,
            'maxPriorityFeePerGas': max_priority_fee_per_gas,
            'nonce': w3.eth.get_transaction_count(METAMASK_ADDRESS),
            'chainId': 56  # ID сети BSC
        })

        # Подписываем транзакцию
        signed_tx = w3.eth.account.sign_transaction(tx, METAMASK_PRIVATE_KEY)

        # Отправляем транзакцию
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"Транзакция отправлена: {tx_hash.hex()}")

        # Ожидаем подтверждения
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            logger.info(f"Перевод {amount} токенов на {EXCHANGE_WALLET_ADDRESS} успешно выполнен")
        else:
            logger.error("Транзакция не удалась")
    except Exception as e:
        logger.error(f"Ошибка при переводе токенов: {e}")


def main():
    logger.info("Запуск скрипта для мониторинга баланса MetaMask в сети BNB")
    while True:
        balance = get_token_balance(METAMASK_ADDRESS)
        logger.info(f"Текущий баланс токена: {balance}")

        if balance > 0.00001:
            logger.info(f"Баланс {balance} превысил минимум, начинаем перевод")
            transfer_tokens(balance)
            break  # Выходим после успешного перевода

        time

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")