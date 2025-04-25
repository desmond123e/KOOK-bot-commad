import json
from khl import Bot

def open_file(path: str):
    """打开 path 对应的 json 文件"""
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp

# 打开 config.json
config = open_file('./config/config.json')

# 使用 WebSocket 初始化机器人
bot = Bot(token=config['token'])
