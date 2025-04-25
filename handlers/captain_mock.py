import random
import aiohttp
from bot import config
from bot import bot
from khl import Bot, Message, MessageTypes, Event, EventTypes
from khl.card import Card, CardMessage, Module, Types, Element

# 模拟的用户类，用于模拟语音频道中的用户
class SimulatedUser:
    def __init__(self, id, username, nickname=None):
        self.id = id
        self.username = username
        self.nickname = nickname or username

# 模拟的用户数据
simulated_users = [
    SimulatedUser(id="1", username="模拟用户1"),
    SimulatedUser(id="2", username="模拟用户2"),
    SimulatedUser(id="3", username="模拟用户3"),
    SimulatedUser(id="4", username="模拟用户4"),
    SimulatedUser(id="5", username="模拟用户5"),
    SimulatedUser(id="6", username="模拟用户6"),
    SimulatedUser(id="7", username="模拟用户7"),
    SimulatedUser(id="8", username="模拟用户8"),
    SimulatedUser(id="9", username="模拟用户9"),
    SimulatedUser(id="10", username="模拟用户10")
]

captains = {}
remaining_players = []
team1 = []
team2 = []

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


# 获取语音频道中的用户，如果人数不足，补充模拟用户
async def get_users_in_channel(voice_channel):
    """获取语音频道的用户，如果人数不足，则补充模拟用户"""
    users_in_channel = await voice_channel.fetch_user_list()

    if len(users_in_channel) < 10:
        # 如果人数不足，补充模拟用户
        needed_simulated_users = 10 - len(users_in_channel)
        users_in_channel.extend(simulated_users[:needed_simulated_users])
    
    return users_in_channel

# 选择队长的函数
async def select_captains_mock(msg: Message):
    """选马模式 - 从语音频道中随机选择两位队长，并开始选人过程"""

    guild_id = msg.ctx.guild.id
    user_id = msg.author.id

    # 获取 token
    token = config['token']

    # 使用 API 获取用户所在的语音频道ID
    voice_channel_id = await get_user_voice_channel(guild_id, user_id, token)
    
    if not voice_channel_id:
        await msg.reply("无法获取你的语音频道信息，请确认你已加入语音频道。")
        return
    
    # 通过 Bot 的 client 获取语音频道对象
    voice_channel = await bot.client.fetch_public_channel(voice_channel_id)

    # 获取语音频道内的用户列表，如果人数不足，补充模拟用户
    users_in_channel = await get_users_in_channel(voice_channel)

    # 随机选择两位队长
    selected_captains = random.sample(users_in_channel, 2)
    captains['captain1'] = selected_captains[0]
    captains['captain2'] = selected_captains[1]
    captains['current_turn'] = 'captain1'  # A 队长先选

    # 剩余的玩家
    global remaining_players
    remaining_players = [user for user in users_in_channel if user not in selected_captains]

    await msg.reply(f"随机选出的队长是：{captains['captain1'].username} 和 {captains['captain2'].username}")

    # 发送剩余玩家的卡片消息
    await send_player_selection_card(msg)

# 发送玩家选择的卡片消息
async def send_player_selection_card(msg: Message):
    """发送剩余玩家的卡片消息，队长点击按钮选择玩家"""
    global remaining_players

    # 构建卡片消息内容
    card = Card(
        Module.Header('选择队员'),
        Module.Divider(),
    )

    # 显示剩余玩家
    for player in remaining_players:
        card.append(
            Module.Section(
                Element.Text(f"{player.nickname or player.username}"),
                accessory=Element.Button(
                    text="选择",
                    value=player.id,  # 点击按钮返回玩家ID
                    click=Types.Click.RETURN_VAL,
                    theme=Types.Theme.PRIMARY
                )
            )
        )

    # 发送卡片消息
    cm = CardMessage(card)
    await msg.reply(cm, type=MessageTypes.CARD)

# 模拟队长选择玩家的按钮点击事件
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def player_selection_event(b: Bot, e: Event):
    """队长选择玩家时处理按钮点击事件"""
    global remaining_players, team1, team2

    # 检查是否有队长信息
    if 'captain1' not in captains or 'captain2' not in captains:
        await b.client.send(e.body['target_id'], "队长信息未找到，请重新开始选马模式。")
        return

    player_id = e.body['value']  # 获取被选择的玩家ID
    user_id = e.body['user_id']

    # 检查是否是队长点击按钮
    if user_id != captains['captain1'].id and user_id != captains['captain2'].id:
        await b.client.send(e.body['target_id'], "只有队长可以选择玩家！")
        return

    # 获取被选中的玩家
    selected_player = next((p for p in remaining_players if p.id == player_id), None)
    if not selected_player:
        await b.client.send(e.body['target_id'], "玩家不存在或已被选择。")
        return

    # 分配给队伍1或队伍2
    if captains['current_turn'] == 'captain1':
        team1.append(selected_player)
        captains['current_turn'] = 'captain2'
    else:
        team2.append(selected_player)
        captains['current_turn'] = 'captain1'

    # 从剩余玩家中移除已选玩家
    remaining_players = [p for p in remaining_players if p.id != player_id]

    # 判断是否已选完所有玩家
    if not remaining_players:
        # 发送最终队伍
        await send_final_teams(b, e.body['target_id'])
    else:
        # 继续选择玩家
        await send_player_selection_card(msg)

# 发送最终队伍
async def send_final_teams(bot: Bot, channel_id: str):
    """发送最终选择的队伍"""
    global team1, team2

    card = Card(
        Module.Header('最终队伍'),
        Module.Section(
            Element.Text("**队伍1**\n" + "\n".join([f"{player.nickname or player.username}" for player in team1]), type=Types.Text.KMD)
        ),
        Module.Divider(),
        Module.Section(
            Element.Text("**队伍2**\n" + "\n".join([f"{player.nickname or player.username}" for player in team2]), type=Types.Text.KMD)
        )
    )

    cm = CardMessage(card)
    await bot.client.send(channel_id, cm, type=MessageTypes.CARD)