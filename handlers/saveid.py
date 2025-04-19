import json
import os
from khl import Bot, Message

data_file = "user_game_ids.json"

if not os.path.exists(data_file):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({}, f)
else:
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            json.load(f)  # 尝试读取以验证文件有效性
    except (UnicodeDecodeError, json.JSONDecodeError):  # 同时捕获两种错误
        print("文件损坏或编码错误，正在重建...")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def load_data():
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
        save_data(data)
        return data

def save_data(data):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def save_game_id(msg: Message, game_id: str):
    data = load_data()
    user_id = str(msg.author.id)
    data[user_id] = game_id
    save_data(data)
    await msg.reply(f"你的游戏ID {game_id} 已保存！")

async def get_game_id(msg: Message):
    data = load_data()
    user_id = str(msg.author.id)
    
    if user_id in data:
        await msg.reply(f"你的游戏ID 是 {data[user_id]}")
    else:
        await msg.reply("你还没有保存过游戏ID，请使用 /saveid <游戏ID> 来保存。")