import json
import os
from khl import Bot, Message

# 定义存储文件路径
data_file = "user_game_ids.json"

# 如果文件不存在，创建一个空的文件
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({}, f)

# 从文件中加载数据
def load_data():
    with open(data_file, 'r') as f:
        return json.load(f)

# 将数据保存到文件中
def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def save_game_id(msg: Message, game_id: str):
    # 加载现有数据
    data = load_data()
    
    user_id = str(msg.author.id)
    # 存储用户的游戏ID
    data[user_id] = game_id
    
    # 保存数据到文件
    save_data(data)
    
    await msg.reply(f"你的游戏ID {game_id} 已保存！")

# 查询用户的游戏ID
async def get_game_id(msg: Message):
    # 加载现有数据
    data = load_data()
    
    user_id = str(msg.author.id)
    
    if user_id in data:
        await msg.reply(f"你的游戏ID 是 {data[user_id]}")
    else:
        await msg.reply("你还没有保存过游戏ID，请使用 /saveid <游戏ID> 来保存。")

