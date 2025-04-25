import random
from khl.card import Card, CardMessage, Module, Element, Types
from khl import Bot, Message, MessageTypes
from bot import config

# 命令和解释
normal_commands_info = {
    '[/help]': '帮助指令',
    '[/hello]': '打个招呼',
}

valorant_commands_info = {
    '[/kd KD值]': '添加或更新kd值',
    '[/kdrandom]': 'kd匹配，未登记kd值的需要先登记一遍',
    '[/captain]': '队长选马模式',
    '[/random]': '随机分组模式',
    '[/assign]': '随机英雄模式(需先分组)',
    '[/map]': '随机地图',
    '[/rekd]': '删除你的比赛信息',
    '[/check]': '查看当前参赛情况',
    '[/delete]': '清除当前所有参赛信息',
    '[/move]': '分配语音频道',
}

rich_commands_info = {
    '[/rule]': '游戏规则',
    '[/game]': '开始游戏',
    '[/newgame]' : '重新开始游戏',
    '[/round]' : '新的回合',
    '[/oppo]' : '获得机会卡',
}

funny_commands_info = {
    '[/roll]': '摇骰子1-100',
    '[/countdown 秒数]': '倒计时 默认60秒',
    '[/saveid 游戏名#1234]' : '保存游戏id',
    '[/myid]' : '查询我的id'
}

# 注册 /help 命令
async def show_help(msg: Message):
    # 创建卡片消息
    image_url = 'https://sodron.net/uploads/ma.jpg'  # 替换为实际图片的 URL
    card = Card(
        Module.Header('你可以使用下面这些指令来呼叫网管哦！'),
         *[Module.Section(Element.Text(f"{command}  {desc}", type=Types.Text.KMD)) for command, desc in normal_commands_info.items()],
        Module.Divider(),
        Module.Header('马德里大师赛！启动！'),
        # 添加图片模块
        Module.Container(Element.Image(src=image_url, size=Types.Size.SM)),
        *[Module.Section(Element.Text(f"{command}  {desc}", type=Types.Text.KMD)) for command, desc in valorant_commands_info.items()],
	Module.Divider(),
	Module.Header('瓦罗兰特奇遇挑战'),
	*[Module.Section(Element.Text(f"{command}   {desc}", type=Types.Text.KMD)) for command, desc in rich_commands_info.items()],
        Module.Divider(),
        Module.Header('其他功能'),
         *[Module.Section(Element.Text(f"{command}   {desc}", type=Types.Text.KMD)) for command, desc in funny_commands_info.items()],
	Module.Divider(),
        Module.Header('卧底风云（开发中）'),
    )
    
    cm = CardMessage(card)
    await msg.reply(cm, type=MessageTypes.CARD)


# 地图列表
maps = ['源工重镇', '隐士修所', '霓虹町', '亚海悬城', '森寒冬港', '微风岛屿', '裂变峡谷??', '深海明珠', '莲华古城', '日落之城', '幽邃地窟']

async def random_map(msg: Message):
    """随机选择一张地图"""
    selected_map = random.choice(maps)
    await msg.reply(f"随机选择的地图是: {selected_map}")