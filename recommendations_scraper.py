import requests
import datetime
import openpyxl
import os

def scrape_steam_reviews_to_excel(appid):
    """
    根据给定的 Steam 游戏 AppID，
    从 store.steampowered.com/appreviewhistogram/ 获取评论统计数据，
    并将 [id, 日期, 好评数, 差评数] 写入 Excel 文件，
    其对应表格列标签为 ["id", "date", "recommendations_up", "recommendations_down"]。

    :param appid: 游戏的 AppID (int)
    """
    
    # 1. 拼接目标接口 URL
    url = f"https://store.steampowered.com/appreviewhistogram/{appid}?l=schinese&review_score_preference=0"
    
    # 仅作为保留作用，测试下来不需要设置 headers 也能正常请求
    headers = {
        # "Cookie": "sessionid=xxxx; ...",
        # "User-Agent": "Mozilla/5.0 ..."
    }
    
    # 2. 请求并解析 JSON
    resp = requests.get(url, headers=headers)
    data = resp.json()
    
    # 3. 提取 rollups 数组 (注意到层级上有特殊关系)
    # 结构: { "results": { "rollups": [ ... ] } }
    rollups = data.get("results", {}).get("rollups", [])
    
    # 4. 创建 Excel 工作簿和工作表
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"AppID_{appid}"
    
    # 写表头
    ws.append(["id", "date", "recommendations_up", "recommendations_down"])
    
    # 5. 遍历 rollups，把数据写入 Excel
    for item in rollups:
        ts = item["date"]  # UNIX时间戳(秒)
        positive = item["recommendations_up"]    # 好评
        negative = item["recommendations_down"]  # 差评
        
        # 转换时间戳为(UTC+0)的 datetime
        dt_utc = datetime.datetime.utcfromtimestamp(ts)
        # 北京时间, UTC+8
        dt_local = dt_utc + datetime.timedelta(hours=8)
        
        date_str = dt_local.strftime("%Y-%m-%d")
        
        ws.append([appid, date_str, positive, negative])

    # 6. 创建子文件夹
    folder_name = "steam_recommendations_data"
    if not os.path.exists(folder_name):# 如果文件夹不存在则创建
        os.makedirs(folder_name)
    
    # 7. 保存 Excel
    # 以 AppID 拼接出文件名
    filename = os.path.join(folder_name, f"steam_recommendations_{appid}.xlsx")
    wb.save(filename)
    print(f"爬取完成，已写入 {filename} ")

# 从文件读取 AppID 并调用 scrape_steam_reviews_to_excel(appid) 函数
def run_from_file(file_name='steam_appids.txt'):
    """
    读取与脚本同目录下的 steam_appids.txt 文件，
    按行解析 AppID 并调用 scrape_steam_reviews_to_excel(appid) 函数。
    """
    # 获取当前脚本的绝对路径，再获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接成 steam_appids.txt 的完整绝对路径
    file_path = os.path.join(script_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在，请检查文件名和路径。")
        return
    
    # 2. 按行读取 AppID
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            appid_str = line.strip()
            if not appid_str:
                continue  # 跳过空行
            try:
                appid = int(appid_str)
                scrape_steam_reviews_to_excel(appid)
            except ValueError:
                print(f"[警告] 无效的 AppID: {appid_str}")

# 运行
if __name__ == "__main__":
    run_from_file("steam_appids.txt")