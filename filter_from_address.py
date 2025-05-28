import json


def extract_unique_from_addresses(input_json_file, output_json_file):
    """
    从包含交易列表的JSON文件中提取所有唯一的 'from' 地址，
    并以指定的格式保存到新的JSON文件中。

    Args:
        input_json_file (str): 输入的JSON文件名 (包含交易列表)。
        output_json_file (str): 输出的JSON文件名。
    """
    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            transactions = json.load(f)
    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_json_file}' 未找到。请确保文件名和路径正确。")
        return
    except json.JSONDecodeError:
        print(f"错误: 解析JSON文件 '{input_json_file}' 失败。文件内容可能不是有效的JSON格式。")
        return
    except Exception as e:
        print(f"读取文件 '{input_json_file}' 时发生未知错误: {e}")
        return

    if not isinstance(transactions, list):
        print(f"错误: '{input_json_file}' 的内容不是一个交易列表。")
        return

    unique_from_addresses = set()
    for tx in transactions:
        if isinstance(tx, dict) and 'from' in tx:
            unique_from_addresses.add(tx['from'])
        else:
            print(f"警告: 发现一个格式不正确的交易记录，已跳过: {tx}")

    # 转换为目标JSON格式
    output_data = [{"from": address} for address in sorted(list(unique_from_addresses))] # 按字母顺序排序

    try:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"成功! 所有唯一的 'from' 地址已提取并保存到 '{output_json_file}'。")
        print(f"共找到 {len(output_data)} 个唯一的 'from' 地址。")
    except Exception as e:
        print(f"写入文件 '{output_json_file}' 时发生错误: {e}")

if __name__ == "__main__":
    # 假设您之前运行的脚本将数据保存为 'usdc_transactions_sorted.json'
    input_file = "usdc_transactions_sorted.json"
    output_file = "unique_from_addresses.json"
    
    extract_unique_from_addresses(input_file, output_file)