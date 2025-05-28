import datetime
import time

import requests

# --- 配置 ---
API_KEY = "your base api key"  # 请确保这是您有效且针对Basescan的API密钥
TARGET_ADDRESS = "0x0BDcA19c9801bb484285362fD5dd0c94592c874C"
USDC_CONTRACT_ADDRESS_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" # Base 上的 USDC
BASESCAN_API_URL = "https://api.basescan.org/api"

def get_all_usdc_transactions(address, usdc_contract_address, api_key):
    all_transactions = []
    page = 1
    offset = 1000
    max_retries = 3

    while True:
        params = {
            "module": "account",
            "action": "tokentx", # 根据文档，这是正确的action
            "contractaddress": usdc_contract_address,
            "address": address,
            "page": page,
            "offset": offset,
            "apikey": api_key,
        }
        
        prepared_request = requests.Request('GET', BASESCAN_API_URL, params=params).prepare()
        print(f"\n正在获取第 {page} 页数据...")
        print(f"请求 URL: {prepared_request.url}") # 打印将要请求的URL
        
        current_retry = 0
        while current_retry < max_retries:
            try:
                response = requests.get(BASESCAN_API_URL, params=params, timeout=20) # 增加超时
                response.raise_for_status()
                data = response.json()
                
                status = data.get("status")
                message = data.get("message")
                result = data.get("result")

                if status == "1":
                    transactions = result
                    if not isinstance(transactions, list):
                        print(f"API 返回的 'result' 不是一个列表: {transactions}")
                        all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                        return all_transactions
                    
                    if not transactions:
                        print("未找到更多交易。")
                        all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                        return all_transactions
                    
                    all_transactions.extend(transactions)
                    
                    if len(transactions) < offset:
                        print("已到达交易列表的最后一页。")
                        all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                        return all_transactions
                    
                    page += 1
                    time.sleep(0.3) # 调整延迟以符合API限制 (例如 3-5 req/sec)
                    break # 成功，跳出重试循环

                elif status == "0" and message == "No transactions found":
                    print("此地址和代币未找到任何交易。")
                    all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                    return all_transactions
                elif status == "0" and message and "Max rate limit reached" in message:
                    print(f"已达到API速率限制，等待10秒后重试 (尝试 {current_retry + 1}/{max_retries})...")
                    time.sleep(10)
                    current_retry += 1
                else: # 包括用户报告的 "Error! Missing Or invalid Action name"
                    print(f"获取数据时出错: Message: {message}, Result: {result}, Status: {status}")
                    all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                    return all_transactions

            except requests.exceptions.Timeout:
                print(f"请求超时，等待5秒后重试 (尝试 {current_retry + 1}/{max_retries})...")
                time.sleep(5)
                current_retry += 1
            except requests.exceptions.RequestException as e:
                print(f"HTTP请求失败: {e} (尝试 {current_retry + 1}/{max_retries})")
                time.sleep(5)
                current_retry += 1
            except ValueError as e: # Includes JSONDecodeError
                print(f"解析JSON响应失败: {e}")
                if 'response' in locals() and response:
                    print(f"响应文本: {response.text}")
                all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
                return all_transactions
        
        if current_retry == max_retries:
            print("达到最大重试次数，停止获取数据。")
            all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
            return all_transactions
    
    # 以防万一，虽然理论上循环内部会返回
    all_transactions.sort(key=lambda x: int(x.get('timeStamp', '0')))
    return all_transactions

if __name__ == "__main__":
    print(f"开始获取地址 {TARGET_ADDRESS} 的USDC交易记录...")
    print(f"USDC 合约地址 (Base): {USDC_CONTRACT_ADDRESS_BASE}")
    
    usdc_transactions = get_all_usdc_transactions(TARGET_ADDRESS, USDC_CONTRACT_ADDRESS_BASE, API_KEY)
    
    if usdc_transactions:
        print(f"\n共找到 {len(usdc_transactions)} 条USDC交易记录，已按时间排序 (从旧到新):")
        
        # 准备将数据写入CSV文件
        # import csv
        # csv_file_name = "usdc_transactions_sorted.csv"
        # fieldnames = ['Timestamp (UTC)', 'Unix Timestamp', 'Transaction Hash', 'From', 'To', 'Value', 'Token Symbol', 'Block Number']

        # with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()

        for i, tx in enumerate(usdc_transactions):
            timestamp_str = tx.get('timeStamp', '0')
            try:
                timestamp = int(timestamp_str)
            except ValueError:
                print(f"警告: 交易 {tx.get('hash', 'N/A')} 的时间戳无效: {timestamp_str}")
                timestamp = 0 # 使用默认值或跳过

            dt_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            readable_time = dt_object.strftime("%Y-%m-%d %H:%M:%S %Z")
            
            token_decimal_str = tx.get('tokenDecimal', '6') # 默认为6 (USDC常见值)
            value_str = tx.get('value', '0')
            try:
                token_decimal = int(token_decimal_str)
                value_raw = int(value_str)
                value_adjusted = value_raw / (10**token_decimal)
            except ValueError:
                print(f"警告: 交易 {tx.get('hash', 'N/A')} 的代币精度或值无效: decimal='{token_decimal_str}', value='{value_str}'")
                value_adjusted = 0.0


            print(f"--- 交易 {i+1} ---")
            print(f"时间: {readable_time} (Unix: {timestamp})")
            print(f"哈希: {tx.get('hash', 'N/A')}")
            print(f"从: {tx.get('from', 'N/A')}")
            print(f"到: {tx.get('to', 'N/A')}")
            print(f"数量: {value_adjusted} {tx.get('tokenSymbol', 'N/A')}")
            print(f"区块号: {tx.get('blockNumber', 'N/A')}")
            
            # writer.writerow({
            #     'Timestamp (UTC)': readable_time,
            #     'Unix Timestamp': timestamp,
            #     'Transaction Hash': tx.get('hash', 'N/A'),
            #     'From': tx.get('from', 'N/A'),
            #     'To': tx.get('to', 'N/A'),
            #     'Value': value_adjusted,
            #     'Token Symbol': tx.get('tokenSymbol', 'N/A'),
            #     'Block Number': tx.get('blockNumber', 'N/A')
            # })
        # print(f"\n所有交易数据也已保存到 {csv_file_name}")

        import json
        json_file_name = "usdc_transactions_sorted.json"
        with open(json_file_name, "w", encoding='utf-8') as f:
            json.dump(usdc_transactions, f, indent=4, ensure_ascii=False)
        print(f"\n所有交易数据也已保存到 {json_file_name}")
            
    elif len(usdc_transactions) == 0 and not any(err in ["No transactions found", "获取数据时出错"] for err in ["<output from script should be checked here>"]): # 检查是否真的没有交易，而不是纯粹的错误
        print("未找到USDC交易记录 (可能是该地址确实没有相关交易)。")
    else:
        print("获取USDC交易记录过程中发生错误，或未找到交易。")