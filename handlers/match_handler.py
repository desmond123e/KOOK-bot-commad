import random
import os
import json
import aiohttp
from khl import Message
from bot import config
from bot import bot
from khl import Bot, Message, MessageTypes, Event, EventTypes
from khl.card import Card, CardMessage, Module, Types, Element, Struct
from itertools import count

# 定义存储文件路径
kd_data_file = "kd_data.json"

# 如果文件不存在，创建一个空的文件
if not os.path.exists(kd_data_file):
    with open(kd_data_file, 'w') as f:
        json.dump({}, f)

# 从文件中加载 KD 数据
def load_kd_data():
    try:
        with open(kd_data_file, 'r') as f:
            data = f.read()
            if data.strip():  # 如果文件不为空
                return json.loads(data)
            else:
                return {}  # 如果文件为空，返回空字典
    except json.JSONDecodeError:
        return {}  # 如果文件格式错误，返回空字典

# 将 KD 数据保存到文件中
def save_kd_data(data):
    with open(kd_data_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 用于存储报名的用户信息（使用用户的ID作为键），每个用户的信息包括用户名和KD值
participants = {}
team1 = []
team2 = []
kd_data = {}
MAX_PARTICIPANTS = 10
captains = {}
remaining_players = []

# 存储用户 KD 的命令
async def store_kd(msg: Message, kd_value: str):
    user_id = str(msg.author.id)
    kd_data = load_kd_data()  # 加载现有 KD 数据

    try:
        kd_value = float(kd_value)  # 尝试将 KD 转换为浮点数
        kd_data[user_id] = kd_value  # 保存或更新 KD 值
        save_kd_data(kd_data)  # 保存数据到文件
        await msg.reply(f"你的 KD 值已保存或更新为 {kd_value}")
    except ValueError:
        await msg.reply("请提供有效的 KD 值，格式为：/kd <值>")

# 创建卡片消息，带有报名按钮
async def start_kd_random_match(msg: Message):
    card = Card(
        Module.Header('5v5 KD 随机匹配'),
        Module.Divider(),
        Module.Section(Element.Text("点击下方报名按钮进行报名，参赛人数达到 10 人后将自动分组。")),
        Module.ActionGroup(
            Element.Button(
                "报名",
                value="sign_up_kd",  # 点击后返回的值
                click=Types.Click.RETURN_VAL,
                theme=Types.Theme.PRIMARY
            )
        )
    )
    # 发送卡片消息
    cm = CardMessage(card)
    await msg.reply(cm, type=MessageTypes.CARD)

# 处理用户报名的函数
async def sign_up_with_kd(user_id: str, username: str, channel):
    # 检查是否已满
    if len(participants) >= MAX_PARTICIPANTS:
        await channel.send("报名已满，无法再报名。")
        return
    
    # 检查是否已经报名
    if user_id in participants:
        await channel.send(f"{username}, 你已经报名过了！")
    else:
        kd_data = load_kd_data()  # 加载 KD 数据
        # 检查用户是否有已存储的 KD 值
        if user_id not in kd_data:
            await channel.send(f"{username}, 请先通过 /kd 命令保存你的 KD 值。")
            return
        
        # 将用户加入报名列表，并使用已存储的 KD 值
        participants[user_id] = {"username": username, "kd": kd_data[user_id]}
        await channel.send(f"{username}, 你已成功报名！当前报名人数: {len(participants)}/{MAX_PARTICIPANTS}")
        
        if len(participants) == MAX_PARTICIPANTS:
            await channel.send("报名已满，自动分组中...")
            await allocate_teams_with_kd(channel)

# 分配队伍的函数（根据 KD 值）
async def allocate_teams_with_kd(channel):
    sorted_participants = sorted(participants.values(), key=lambda x: x['kd'], reverse=True)
    
    global team1, team2  # 使用全局队伍
    team1 = []
    team2 = []
    team1_kd = 0
    team2_kd = 0

    # 分配队伍，确保 KD 平衡
    for participant in sorted_participants:
        if team1_kd <= team2_kd:
            team1.append(participant)
            team1_kd += participant['kd']
        else:
            team2.append(participant)
            team2_kd += participant['kd']

    # 给每个用户标记所属队伍
    for player in team1:
        player['team'] = 1
    for player in team2:
        player['team'] = 2

    # 创建分组结果的卡片消息
    result_card = Card(
        Module.Section(
            Element.Text(f"**队伍1** (总 KD: {team1_kd:.2f})\n" + "\n".join([f"**{player['username']}** (KD: {player['kd']})" for player in team1]), type=Types.Text.KMD)
        ),
        Module.Divider(),
        Module.Section(
            Element.Text(f"**队伍2** (总 KD: {team2_kd:.2f})\n" + "\n".join([f"**{player['username']}** (KD: {player['kd']})" for player in team2]), type=Types.Text.KMD)
        )
    )
    cm = CardMessage(result_card)
    # 发送分组结果
    await channel.send(cm, type=MessageTypes.CARD)

    # # 清空报名信息
    # participants.clear()

# 监听按钮点击事件
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_click_event(b: Bot, e: Event):
    """处理按钮点击事件"""
    if e.body['value'] == 'sign_up_kd':  # 判断按钮是否是 KD 随机匹配报名按钮
        user_id = str(e.body['user_id'])
        username = e.body['user_info']['nickname'] or e.body['user_info']['username']
        
        # 获取频道对象并处理报名
        channel = await bot.client.fetch_public_channel(e.body['target_id'])
        
        # 处理 KD 报名
        await sign_up_with_kd(user_id, username, channel)


async def start_kd_random_command(msg: Message):
    await start_kd_random_match(msg)


async def reset_participants(msg: Message):
    """清空所有报名信息"""
    participants.clear()
    team1.clear()
    team2.clear()
    await msg.reply("所有报名信息已清空。")

async def view_participants(msg: Message):
    """查看当前报名的参赛选手"""
    if not participants:
        await msg.reply("目前没有参赛选手。")
        return
    
    participants_list = "当前参赛选手:\n"
    for info in participants.values():
        # 检查是否有 'kd' 字段
        if 'kd' in info:
            participants_list += f"{info['username']} (KD: {info['kd']})\n"
        else:
            participants_list += f"{info['username']}\n"
    
    await msg.reply(participants_list)



# --------------------------删除KD-----------------------------

@bot.command(name="rekd")
async def remove_kd(msg: Message):
    user_id = str(msg.author.id)  # 确保 user_id 是字符串类型
    
    # 检查当前用户是否已注册
    if user_id in participants:
        if len(participants) >= MAX_PARTICIPANTS:
            await msg.reply('报名已结束，无法删除')
            return
        # 从 participants 字典中删除该用户的条目
        del participants[user_id]
        await msg.reply(f"你的信息已被清除，请重新注册并输入 /kd kd值。")
    else:
        await msg.reply("你还没有注册，请先使用 /kd kd值 进行参赛。")

# ----------------------------------------------------

BASE_URL = "https://www.kookapp.cn/api"

async def get_user_voice_channel(guild_id: str, user_id: str, token: str):
    """使用 KOOK API 获取用户所在的语音频道"""
    url = f"{BASE_URL}/v3/channel-user/get-joined-channel"
    headers = {
        "Authorization": f"Bot {token}"
    }
    params = {
        "guild_id": guild_id,
        "user_id": user_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['code'] == 0 and data['data']['items']:
                    return data['data']['items'][0]['id']  # 返回频道ID
                else:
                    return None
            else:
                return None
async def select_captains(msg: Message):
    """选马模式 - 使用 API 获取用户所在的语音频道，并随机选择两位队长"""

    guild_id = msg.ctx.guild.id
    user_id = msg.author.id

    # 从配置文件中获取 token
    token = config['token']

    # 使用 API 获取用户所在的语音频道ID
    voice_channel_id = await get_user_voice_channel(guild_id, user_id, token)
    
    if not voice_channel_id:
        await msg.reply("无法获取你的语音频道信息，请确认你已加入语音频道。")
        return
    
    # 通过 Bot 的 client 获取语音频道对象
    voice_channel = await bot.client.fetch_public_channel(voice_channel_id)
    # # 让机器人加入语音频道
    # await voice_channel.join()
    # await msg.reply(f"已加入语音频道 {voice_channel.name}！")

    # 获取语音频道内的用户列表
    users_in_channel = await voice_channel.fetch_user_list()

    # 检查语音频道中是否有足够的人
    if len(users_in_channel) < 2:
        await msg.reply("当前语音频道人数不足，至少需要2人才能选队长。")
        return

    # 从语音频道中随机选择两位用户作为队长
    selected_captains = random.sample(users_in_channel, 2)
    captain1 = selected_captains[0].nickname or selected_captains[0].username
    captain2 = selected_captains[1].nickname or selected_captains[1].username

    await msg.reply(f"随机选出的队长是：{captain1} 和 {captain2}")
    
    # 机器人可以继续留在频道或根据需要离开
    # await voice_channel.leave()

# 随机匹配

# 创建卡片消息，带有报名按钮
async def start_random_match(msg: Message):
    card = Card(
        Module.Header('5v5 随机匹配'),
        Module.Divider(),
        Module.Section(Element.Text("点击下方报名按钮进行报名，参赛人数达到 10 人后将自动分组。")),
        Module.ActionGroup(
            Element.Button(
                "报名",
                value="sign_up",  # 点击后返回的值
                click=Types.Click.RETURN_VAL,
                theme=Types.Theme.PRIMARY
            )
        )
    )
    # 发送卡片消息
    cm = CardMessage(card)
    await msg.reply(cm, type=MessageTypes.CARD)

# 处理用户报名的函数
async def sign_up(user_id: str, username: str, channel):
    # 手动添加模拟用户以测试
    if len(participants) >= MAX_PARTICIPANTS:
        await channel.send("报名已满，无法再报名。")
        return
    
    if user_id in participants:
        await channel.send(f"{username}, 你已经报名过了！")
    else:
        participants[user_id] = {"username":username}
        await channel.send(f"{username}, 你已成功报名！当前报名人数: {len(participants)}/{MAX_PARTICIPANTS}")
        
        if len(participants) == MAX_PARTICIPANTS:
            await channel.send("报名已满，自动分组中...")
            await allocate_teams(channel)

# ===============================测试用================================================
# async def sign_up(user_id: str, username: str, channel):
#     if len(participants) >= MAX_PARTICIPANTS:
#         await channel.send("报名已满，无法再报名。")
#         return
    
#     # 允许单个用户多次报名
#     participants[user_id + f"_{len(participants)}"] = {"username":username}  # 用 user_id 加上报名次数作为唯一标识
#     await channel.send(f"{username}, 你已成功报名！当前报名人数: {len(participants)}/{MAX_PARTICIPANTS}")
    
#     if len(participants) == MAX_PARTICIPANTS:
#         await channel.send("报名已满，自动分组中...")
#         await allocate_teams(channel)
# =========================================================================================


# 分配队伍的函数
async def allocate_teams(channel):
    participant_list = list(participants.values())
    random.shuffle(participant_list)  # 随机打乱报名选手

    global team1, team2  # 声明使用全局变量
    team1 = participant_list[:5]
    team2 = participant_list[5:]

    # 给每个用户标记所属队伍
    for player in team1:
        player['team'] = 1
    for player in team2:
        player['team'] = 2

    # 创建分组结果的卡片消息
    result_card = Card(
        Module.Section(
            Element.Text("**队伍1**\n" + "\n".join([f"**{player['username']}**" for player in team1]), type=Types.Text.KMD)
        ),
        Module.Divider(),
        Module.Section(
            Element.Text("**队伍2**\n" + "\n".join([f"**{player['username']}**" for player in team2]), type=Types.Text.KMD)
        )
    )
    cm = CardMessage(result_card)
    # 发送分组结果
    await channel.send(cm, type=MessageTypes.CARD)

    # 清空报名信息
    # participants.clear()

# 监听按钮点击事件
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_click_event(b: Bot, e: Event):
    """处理按钮点击事件"""
    if e.body['value'] == 'sign_up':  # 判断按钮是否是报名按钮
        user_id = e.body['user_id']
        username = e.body['user_info']['nickname'] or e.body['user_info']['username']
        
        # 获取频道对象并处理报名
        channel = await bot.client.fetch_public_channel(e.body['target_id'])
        
        if user_id not in participants:
            await sign_up(user_id, username, channel)
        else:
            await channel.send(f"{username}, 你已经报名过了！")


# 语音移动
TEAM1_VOICE_CHANNEL_ID = '4196882795317224'
TEAM2_VOICE_CHANNEL_ID = '8005610226977221'
# 移动用户到指定语音频道的函数
async def move_user_to_channel(user_ids: list, target_channel_id: str, token: str):
    url = 'https://www.kookapp.cn/api/v3/channel/move-user'  # KOOK API 移动用户的地址
    headers = {
        "Authorization": f"Bot {token}",  # 你的机器人 token
        'Content-Type': 'application/json',
    }
    payload = {
        'user_ids': user_ids,  # 这里需要是一个用户 ID 数组
        'target_id': target_channel_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                print(f"用户 {user_ids} 已成功移动到频道 {target_channel_id}")
            else:
                error_message = await response.text()
                print(f"移动用户失败: {error_message}")

async def move_to_voice_channels(msg: Message):
    # 从配置文件中获取 token
    token = config['token']
    
    # 检查是否有分组信息
    if not participants or not any('team' in info for info in participants.values()):
        await msg.reply("目前没有分组信息，请先进行分组。")
        return
    
    # 分别收集队伍1和队伍2的用户ID
    team1_users = []
    team2_users = []
    
    for user_id, info in participants.items():
        if 'team' not in info:
            continue
        # 根据队伍收集用户ID
        if info['team'] == 1:
            team1_users.append(user_id)
        elif info['team'] == 2:
            team2_users.append(user_id)
    
    # 一次性将队伍1的用户移动到队伍1的语音频道
    if team1_users:
        await move_user_to_channel(team1_users, TEAM1_VOICE_CHANNEL_ID, token)
        await msg.reply(f"已将队伍1的用户移动到语音频道")
    
    # 一次性将队伍2的用户移动到队伍2的语音频道
    if team2_users:
        await move_user_to_channel(team2_users, TEAM2_VOICE_CHANNEL_ID, token)
        await msg.reply(f"已将队伍2的用户移动到语音频道")

# -------------------------------随机英雄---------------------------------------

# 英雄字典
heroes = {
    '控场英雄': ['海神', '蝰蛇', '星邃', '幽影', '暮蝶', '炼狱'],
    '信息英雄': ['KO', '盖克', '猎枭', '黑梦', '斯凯', '铁臂'],
    '突进英雄': ['jett', '霓虹', '火男', '雷兹', '蕾娜', '夜露', '壹绝'],
    '哨位英雄': ['保安', '奶妈', '钱包', '奇乐', '维斯', '钢索']
}

# 重置英雄字典
def reset_heroes():
    return {
        '控场英雄': ['海神', '蝰蛇', '星邃', '幽影', '暮蝶', '炼狱'],
        '信息英雄': ['KO', '盖克', '猎枭', '黑梦', '斯凯', '铁臂'],
        '突进英雄': ['jett', '霓虹', '火男', '雷兹', '蕾娜', '夜露', '壹绝'],
        '哨位英雄': ['保安', '奶妈', '钱包', '奇乐', '维斯', '钢索']
    }

# 为一个队伍分配英雄，确保队伍内英雄不重复
def assign_heroes_to_team(team):
    assigned_heroes = {}
    available_heroes = reset_heroes()  # 重置英雄列表以确保每个队伍有完整的选择
    
    # 为四个角色分配英雄（控场、哨位、突进、信息）
    role_order = ['控场英雄', '哨位英雄', '突进英雄', '信息英雄']
    
    for i, role in enumerate(role_order):
        player = team[i]['username']  # 从队伍中按顺序选择玩家，使用 `username`
        hero = random.choice(available_heroes[role])
        assigned_heroes[player] = hero
        available_heroes[role].remove(hero)  # 移除该英雄，确保队伍内不重复

    # 为第五个玩家分配一个任意职业的英雄
    remaining_heroes = [hero for role in available_heroes.values() for hero in role]
    player = team[4]['username']  # 最后一个玩家
    assigned_heroes[player] = random.choice(remaining_heroes)

    return assigned_heroes

# 生成卡片消息展示分配结果
async def show_heroes_card(msg, team1, team2, assigned_heroes_1, assigned_heroes_2):
    card = Card(
        Module.Header('英雄分配结果'),
        Module.Divider(),
        Module.Header('队伍1:')
    )
    
    # 显示队伍1的英雄分配
    for player, hero in assigned_heroes_1.items():
        card.append(Module.Section(Element.Text(f"{player}: {hero}", type=Types.Text.KMD)))
    
    card.append(Module.Divider())
    card.append(Module.Header('队伍2:'))
    
    # 显示队伍2的英雄分配
    for player, hero in assigned_heroes_2.items():
        card.append(Module.Section(Element.Text(f"{player}: {hero}", type=Types.Text.KMD)))
    
    # 发送卡片消息
    cm = CardMessage(card)
    await msg.reply(cm, type=MessageTypes.CARD)

@bot.command(name="assign")
async def assign_heroes_command(msg: Message):
    if len(team1) < 5 or len(team2) < 5:
        await msg.reply('队伍尚未分配完整,无法随机')
        return
    # 示例队伍数据，包含字典格式
    # team1 = [{'username': '迪倫老師', 'kd': 2.3, 'team': 1}, 
    #           {'username': '模拟用户3', 'kd': 1.8, 'team': 1}, 
    #           {'username': '模拟用户4', 'kd': 1.5, 'team': 1}, 
    #           {'username': '模拟用户7', 'kd': 1.3, 'team': 1}, 
    #           {'username': '1', 'kd': 1.2, 'team': 1}]
    
    # team2 = [{'username': '模拟用户6', 'kd': 1.7, 'team': 2}, 
    #           {'username': '模拟用户8', 'kd': 1.9, 'team': 2}, 
    #           {'username': '模拟用户9', 'kd': 1.9, 'team': 2}, 
    #           {'username': '模拟用户10', 'kd': 1.9, 'team': 2}, 
    #           {'username': '2', 'kd': 1.4, 'team': 2}]

    # 为每个队伍分配英雄
    assigned_heroes_1 = assign_heroes_to_team(team1)
    assigned_heroes_2 = assign_heroes_to_team(team2)

    # 显示英雄分配结果
    await show_heroes_card(msg, team1, team2, assigned_heroes_1, assigned_heroes_2)

# ----------------------------------------------------------------------------------------

@bot.command(name="add")
async def add_mock_users(msg: Message):
    """手动添加模拟用户"""
    participants.update({
        'user_1': {'username': '1', 'kd': 1.2},
        'user_2': {'username': '2', 'kd': 1.4},
        'user_3': {'username': '模拟用户3', 'kd': 1.8},
        'user_4': {'username': '模拟用户4', 'kd': 1.5},
        'user_5': {'username': '模拟用户5', 'kd': 1.1},
        'user_6': {'username': '模拟用户6', 'kd': 1.7},
        'user_7': {'username': '模拟用户7', 'kd': 1.3},
        'user_8': {'username': '模拟用户8', 'kd': 1.9},
        'user_9': {'username': '模拟用户9', 'kd': 1.9},
    })

    await msg.reply("已添加模拟用户，现在可以进行分组。")

@bot.command(name="addmock")
async def add_mock_users(msg: Message):
    """手动添加模拟用户"""
    participants.update({
        'user_1': {'username': '1', 'kd': 1.2},
        'user_2': {'username': '2', 'kd': 1.4},
        'user_3': {'username': '模拟用户3', 'kd': 1.8},
        'user_4': {'username': '模拟用户4', 'kd': 1.5},
        'user_5': {'username': '模拟用户5', 'kd': 1.1},
        'user_6': {'username': '模拟用户6', 'kd': 1.7},
        'user_7': {'username': '模拟用户7', 'kd': 1.3},
        'user_8': {'username': '模拟用户8', 'kd': 1.9},
        'user_9': {'username': '模拟用户9', 'kd': 1.9},
    })

    await msg.reply("已添加模拟用户，现在可以进行分组。")