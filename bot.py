from web3 import Web3
from eth_account import Account
from eth_abi import encode
import time
import sys
import os
import random


# Data jembatan (bridge data)
from data_bridge import data_bridge
# from keys_and_addresses import private_keys, my_addresses, labels
from network_config import networks

# 从环境变量中获取私钥
private_keys = [
    os.getenv('MY_PRIVATE_KEY')  # 环境变量名应根据你的设置而定
]

# 从环境变量中获取地址
my_addresses = [
    # os.getenv('MY_ADDRESS')
]

labels = [
    'Wallet 1'
]

# Fungsi untuk memusatkan teks
def center_text(text):
    terminal_width = os.get_terminal_size().columns
    lines = text.splitlines()
    centered_lines = [line.center(terminal_width) for line in lines]
    return "\n".join(centered_lines)

# Fungsi untuk membersihkan terminal
def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

ascii_art = """
 _   _       _   _     
| | | |  _  | | | |  _ 
| |_| | / \ | |_| | / \ 
|  _  |/ _ \|  _  '/ _ \
| | | | (_) | | | | (_) |
|_| |_|_| |_|_| |_|_| |_|
"""

description = """
Bot Auto Bridge  https://bridge.t1rn.io/
"""

# Warna dan simbol untuk setiap chain
chain_symbols = {
    'Arbitrum Sepolia': '\033[34m',   
    'OP Sepolia': '\033[91m',         
    'Blast Sepolia': '\033[93m',     
    'Base Sepolia': '\033[96m'       
}

# Warna hijau
green_color = '\033[92m'
reset_color = '\033[0m'
menu_color = '\033[95m'  # Warna untuk teks menu

# URLs Explorer untuk setiap jaringan
explorer_urls = {
    'Arbitrum Sepolia': 'https://sepolia.arbiscan.io/tx/',
    'OP Sepolia': 'https://sepolia-optimism.etherscan.io/tx/',
    'Blast Sepolia': 'https://testnet.blastscan.io/tx/',
    'Base Sepolia': 'https://sepolia.basescan.org/tx/',
    'BRN': 'https://brn.explorer.caldera.xyz/tx/'
}

# Fungsi untuk mendapatkan saldo BRN
def get_brn_balance(web3, my_address):
    balance = web3.eth.get_balance(my_address)
    return web3.from_wei(balance, 'ether')

# Fungsi untuk membuat dan mengirim transaksi
def send_bridge_transaction(web3, account, my_address, network_name, choice_bridge):
    nonce = web3.eth.get_transaction_count(my_address, 'pending')
    # value_in_ether = 0.1
    value_in_ether = round(random.uniform(0.11, 0.15), 4)
    value_in_wei = web3.to_wei(value_in_ether, 'ether')
    value_min = web3.to_wei(value_in_ether*0.999999, 'ether')

    data = calculate_bridge_data(web3, account.address, value_min, network_name, choice_bridge)

    # 获取账户余额
    balance = web3.eth.get_balance(my_address)
    formatted_balance = web3.from_wei(balance, 'ether')

    if balance < (value_in_wei + web3.to_wei(0.01, 'ether')):  # 假设 0.01 ETH 作为 gas
        print(f"{reset_color} 余额不足: {formatted_balance} ETH，无法发送 {value_in_ether} ETH 交易。{reset_color}", flush=True)
        return None

    try:
        gas_estimate = web3.eth.estimate_gas({
            'to': networks[network_name]['contract_address'],
            'from': my_address,
            'data': data,
            'value': value_in_wei
        })
        gas_limit = gas_estimate + 50000  # Increase safety margin
    except Exception as e:
        print(f"Error estimating gas: {e}", flush=True)
        return None

    base_fee = web3.eth.get_block('latest')['baseFeePerGas']
    priority_fee = web3.to_wei(5, 'gwei')
    max_fee = base_fee + priority_fee

    data = calculate_bridge_data(web3, account.address, value_in_wei, max_fee+value_in_wei, network_name, choice_bridge)

    transaction = {
        'nonce': nonce,
        'to': networks[network_name]['contract_address'],
        'value': value_in_wei,
        'gas': gas_limit,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': priority_fee,
        'chainId': networks[network_name]['chain_id'],
        'data': data
    }

    try:
        signed_txn = web3.eth.account.sign_transaction(transaction, account.key)
    except Exception as e:
        print(f"Error signing transaction: {e}", flush=True)
        return None

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Mendapatkan saldo terkini
        balance = web3.eth.get_balance(my_address)
        formatted_balance = web3.from_wei(balance, 'ether')

        # Mendapatkan link explorer
        explorer_link = f"{explorer_urls[network_name]}{web3.to_hex(tx_hash)}"

        # Menampilkan informasi transaksi
        print(f"{green_color} Alamat Pengirim: {account.address}", flush=True)
        print(f" Gas digunakan: {tx_receipt['gasUsed']}", flush=True)
        print(f"  Nomor blok: {tx_receipt['blockNumber']}", flush=True)
        print(f" Saldo ETH: {formatted_balance} ETH", flush=True)
        brn_balance = get_brn_balance(Web3(Web3.HTTPProvider('https://brn.rpc.caldera.xyz/http')), my_address)
        print(f" Saldo BRN: {brn_balance} BRN", flush=True)
        print(f" Link Explorer: {explorer_link}\n{reset_color}", flush=True)

        return web3.to_hex(tx_hash), value_in_ether
    except Exception as e:
        print(f"Error sending transaction: {e}", flush=True)
        return None, None

# Fungsi untuk memproses transaksi pada jaringan tertentu
def process_network_transactions(network_name, bridges, chain_data, successful_txs):
    web3 = Web3(Web3.HTTPProvider(chain_data['rpc_url']))
    if not web3.is_connected():
        print(f"无法连接到 {network_name}", flush=True)
        return

    choice_bridge = random.randint(0, 2)

    bridge = bridges[choice_bridge]
    for i, private_key in enumerate(private_keys):
        account = Account.from_key(private_key)
        # data = data_bridge[bridge]
        result = send_bridge_transaction(web3, account, account.address, network_name, choice_bridge)
        if result:
            tx_hash, value_sent = result
            successful_txs += 1

            # Check if value_sent is valid before formatting
            if value_sent is not None:
                print(f"{chain_symbols[network_name]} Total Tx Sukses: {successful_txs} | {labels[i]} | Bridge: {bridge} | Jumlah Bridge: {value_sent:.5f} ETH {reset_color}\n", flush=True)
            else:
                print(f"{chain_symbols[network_name]} Total Tx Sukses: {successful_txs} | {labels[i]} | Bridge: {bridge} {reset_color}\n", flush=True)

            print(f"{'='*150}", flush=True)
            print("\n", flush=True)
        delay = random.randint(1, 60)
        print(f"发送成功，休息{30+delay}秒\n", flush=True)
        time.sleep(30+delay)
        

    return successful_txs

# Fungsi untuk menampilkan menu pilihan chain
def display_menu():
    print(f"{menu_color}Pilih chain untuk menjalankan transaksi:{reset_color}")
    print("")
    print(f"{chain_symbols['Arbitrum Sepolia']}1. ARB -> OP, BLAST, BASE Sepolia{reset_color}")
    print(f"{chain_symbols['OP Sepolia']}2. OP -> ARB, BLAST, BASE Sepolia{reset_color}")
    print(f"{chain_symbols['Blast Sepolia']}3. BLAST -> ARB, OP, BASE Sepolia{reset_color}")
    print(f"{chain_symbols['Base Sepolia']}4. BASE -> ARB, OP, BLAST Sepolia{reset_color}")
    print(f"{menu_color}5. Jalankan Semua{reset_color}")
    print("")
    choice = input("Masukkan pilihan (1-5): ")
    return choice

def calculate_bridge_data(web3, sender, amountin, totalbridge, network_name, choice_bridge):
    # 初始化 Web3
    # web3 = Web3(Web3.HTTPProvider('YOUR_INFURA_OR_ALCHEMY_URL'))

    gasPrice = web3.eth.gas_price
    nonce = web3.eth.get_transaction_count(sender)
    
    # 合约地址和函数选择器
    bridgeaddr = web3.to_checksum_address(sender)  # for arb
    
    if network_name is 'Arbitrum Sepolia':
        funcbridge = bytes.fromhex('56591d59')  # 函数选择器
        if choice_bridge == 0:
            codebridge = bytes.fromhex('62737370')  # ARB -> BASE
        elif choice_bridge == 1:
            codebridge = bytes.fromhex('6f707370')  # ARB -> OP
        elif choice_bridge == 2:
            codebridge = bytes.fromhex('626c7373')  # ARB -> BLAST
    elif network_name is 'OP Sepolia':
        funcbridge = bytes.fromhex('56591d59')  # 函数选择器
        if choice_bridge == 0:
            codebridge = bytes.fromhex('626c7373')  # OP -> BLAST
        elif choice_bridge == 1:
            codebridge = bytes.fromhex('61726274')  # OP -> ARB
        elif choice_bridge == 2:
            codebridge = bytes.fromhex('62737370')  # OP -> BASE
    elif network_name is 'Blast Sepolia':
        funcbridge = bytes.fromhex('56591d59')  # 函数选择器
        if choice_bridge == 0:
            codebridge = bytes.fromhex('6f707370')  # BLAST -> OP
        elif choice_bridge == 1:
            codebridge = bytes.fromhex('61726274')  # BLAST -> ARB
        elif choice_bridge == 2:
            codebridge = bytes.fromhex('62737370')  # BLAST -> BASE
    elif network_name is 'Base Sepolia':
        funcbridge = bytes.fromhex('56591d59')  # 函数选择器
        if choice_bridge == 0:
            codebridge = bytes.fromhex('6f707370')  # BASE -> OP
        elif choice_bridge == 1:
            codebridge = bytes.fromhex('61726274')  # BASE -> ARB
        elif choice_bridge == 2:
            codebridge = bytes.fromhex('626c7373')  # BASE -> BLAST


    amountzero = 0
    # totalbridge = amountin
    bridgedmin = web3.from_wei(amountin, 'ether')  # 根据需要转换单位
    
    # 编码参数
    enc_bridge = encode([
        'bytes4', 'uint256', 'address', 'uint256', 'uint256', 'uint256', 'uint256'
    ], [
        codebridge, 
        amountzero, 
        sender, 
        amountin, 
        amountzero, 
        amountzero, 
        totalbridge
    ])
    
    # 生成最终的 data
    data = web3.to_hex(funcbridge + enc_bridge)
    # print(data)
    return data



def main():
    # print("\033[92m" + center_text(ascii_art) + "\033[0m")
    # print(center_text(description))
    # print("\n\n")

    successful_txs = 0

    while True:
        start_time = time.time()

        # 进行跨链操作，持续两个小时
        while time.time() - start_time < 3 * 3600:  # 2小时
            # choice = display_menu()
            # 生成一个随机选择，范围在 1 到 4 之间
            choice = random.randint(1, 4)

            # clear_terminal()  # Membersihkan terminal sebelum menampilkan transaksi baru
            # print("\033[92m" + center_text(ascii_art) + "\033[0m")
            # print(center_text(description))
            # print("\n\n")

            try:
                if choice == 1:
                    successful_txs = process_network_transactions('Arbitrum Sepolia', ["ARB - BASE", "ARB - OP SEPOLIA", "ARB - BLAST"], networks['Arbitrum Sepolia'], successful_txs)
                elif choice == 2:
                    successful_txs = process_network_transactions('OP Sepolia', ["OP - BLAST", "OP - ARB", "OP - BASE"], networks['OP Sepolia'], successful_txs)
                elif choice == 3:
                    successful_txs = process_network_transactions('Blast Sepolia', ["BLAST - OP", "BLAST - ARB", "BLAST - BASE"], networks['Blast Sepolia'], successful_txs)
                elif choice == 4:
                    successful_txs = process_network_transactions('Base Sepolia', ["BASE - OP", "BASE - ARB", "BASE - BLAST"], networks['Base Sepolia'], successful_txs)
                else:
                    print("Pilihan tidak valid. Silakan coba lagi.", flush=True)

            except KeyboardInterrupt:
                print("\nScript dihentikan oleh pengguna. ", flush=True)
                print(f"Total transaksi sukses: {successful_txs} ", flush=True)
                sys.exit(0)
            except Exception as e:
                print(f"Error occurred: {e}", flush=True)
                sys.exit(1)
        
        # 休息12个小时
        print("休息 9 小时...", flush=True)
        time.sleep(9 * 3600)

if __name__ == "__main__":
    main()
