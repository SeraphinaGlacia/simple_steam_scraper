import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import random
import os

class SteamScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # ====== CHANGED: 在 base_url 上面增加了 &l=english&cc=us，用以确保搜索页面也以英文+美元显示
        self.base_url = 'https://store.steampowered.com/search/?l=english&cc=us'
        self.games_data = []

    def get_total_pages(self):
        # ====== CHANGED: 此处也依旧保持 category1=998
        params = {
            'category1': '998', 
            'page': '1'
        }
        response = requests.get(self.base_url, params=params, headers=self.headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取搜索结果总数
        try:
            search_results = soup.find('div', {'class': 'search_pagination_left'})
            total_results = int(search_results.text.strip().split(' ')[-2])
            return (total_results // 25) + 1  # Steam每页显示25个游戏
        except:
            return 5000  # 如果无法获取总页数，默认爬取5000页

    def get_game_details(self, app_id):
        # ====== CHANGED: 这里在API请求末尾增加了 &l=english&cc=us，强制返回英文与美元
        url = f'https://store.steampowered.com/api/appdetails?appids={app_id}&l=english&cc=us'
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            data = response.json()
            
            if data[str(app_id)]['success']:
                game_data = data[str(app_id)]['data']
                return {
                    # ====== 保持原有字段不变
                    'name': game_data.get('name', ''),
                    'release_date': game_data.get('release_date', {}).get('date', ''),
                    'price': game_data.get('price_overview', {}).get('final_formatted', 'Free'),
                    'developers': ', '.join(game_data.get('developers', [])),
                    'publishers': ', '.join(game_data.get('publishers', [])),
                    'genres': ', '.join([genre['description'] for genre in game_data.get('genres', [])]),
                    'description': game_data.get('short_description', ''),
                }
        except Exception as e:
            print(f"Error fetching details for app {app_id}: {str(e)}")
        return None

    def scrape_page(self, page):
        # ====== CHANGED: 确保翻页时也带上 category1=998，以获取对应分类
        params = {
            'category1': '998',
            'sort_by': '_ASC',
            'page': str(page)
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            games = soup.find_all('a', {'class': 'search_result_row'})
            
            for game in games:
                app_id = game['data-ds-appid']
                details = self.get_game_details(app_id)
                
                if details:
                    # ====== CHANGED: 在这里把 app_id 存进 details 中，以便输出到excel里
                    details["id"] = app_id  # 这一行就是让第一列可以是 id
                    self.games_data.append(details)
                    print(f"Scraped: {details['name']}")
                
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            print(f"Error scraping page {page}: {str(e)}")

    def save_to_excel(self, filename=None):
        if not filename:
            filename = f'steam_games_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        df = pd.DataFrame(self.games_data)
        
        # ====== CHANGED: 如果你想把"id"作为第一列，需要显式指定列顺序
        # 当然前提是 self.games_data 中每个元素都有 "id" 这个键
        desired_columns = ["id", "name", "release_date", "price", 
                           "developers", "publishers", "genres", "description"]
        
        # 以防万一，先判断一下哪些列真的存在（如果有时获取不到字段，可能报错）
        existing_columns = [col for col in desired_columns if col in df.columns]
        df = df[existing_columns]
        
        df.to_excel(filename, index=False)
        print(f"Data saved to {filename}")

    # ====== ADDED: 新增一个方法，用来将所有的 app_id 保存到一个独立的文件中
    def save_appids_to_file(self, filename='app_ids.txt'):
    # 获取当前文件所在目录
        directory = os.path.dirname(__file__)
        # 生成完整文件路径
        file_path = os.path.join(directory, filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            for game in self.games_data:
                # 这里的 "id" 就是上面加的 details["id"]
                f.write(str(game['id']) + '\n')
    
        print(f"App IDs saved to {file_path}")

    def run(self, max_pages=None):
        total_pages = self.get_total_pages()
        if max_pages:
            total_pages = min(total_pages, max_pages)
            
        print(f"Starting to scrape {total_pages} pages...")
        
        for page in range(1, total_pages + 1):
            print(f"Scraping page {page}/{total_pages}")
            self.scrape_page(page)
            time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    scraper = SteamScraper()
    # 如果想要爬取全部页面，就不传入 max_pages，或者设置很大
    scraper.run(1)  
    scraper.save_to_excel()

    # ====== ADDED: 使用新函数，把所有app_id也单独存进一个txt文件
    scraper.save_appids_to_file('steam_appids.txt')