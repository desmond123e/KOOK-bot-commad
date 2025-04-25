from datetime import datetime, timedelta
from bot import config
from bot import bot
from khl import Bot, Message, MessageTypes, Event, EventTypes
from khl.card import Card, CardMessage, Module, Types, Element, Struct
import pytz
from handlers.database import Database  # 导入数据库模块

# 初始化数据库
db = Database()
TIMEZONE = pytz.timezone('Asia/Shanghai')
BASE_ENERGY = 20
CONSECUTIVE_BONUS = 20

def get_daily_sign_list():
    """获取当日签到用户列表"""
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    return db.get_daily_sign(today)

def update_sign_data(user_id: str, username: str):
    """更新签到数据（数据库版本）"""
    today = datetime.now(TIMEZONE)
    today_str = today.strftime('%Y-%m-%d')
    
    # 获取或初始化用户数据
    user = db.get_user(user_id) or {
        'user_id': user_id,
        'username': username,
        'total_days': 0,
        'consecutive_days': 0,
        'last_sign': None,
        'energy_total': 0,
        'consecutive_bonus': 0
    }
    
    # 计算连续签到
    last_sign = datetime.fromisoformat(user['last_sign']) if user['last_sign'] else None
    if last_sign and (today.date() - last_sign.date()).days == 1:
        user['consecutive_days'] += 1
        user['consecutive_bonus'] = CONSECUTIVE_BONUS
    else:
        user['consecutive_days'] = 1
        user['consecutive_bonus'] = 0
    
    # 计算当日活力值
    daily_energy = BASE_ENERGY + user['consecutive_bonus']
    user['energy_total'] += daily_energy
    user['total_days'] += 1
    user['last_sign'] = today.isoformat()
    
    # 更新数据库
    db.update_user(user)
    db.update_daily_sign(today_str, user_id)
    
    # 返回扩展字段（用于生成卡片）
    user['daily_energy'] = daily_energy
    return user

async def generate_sign_card(user_data: dict):
    """生成签到卡片"""
    today_users = get_daily_sign_list()
    rank = today_users.index(user_data['user_id']) + 1
    
    return CardMessage(
        Card(
            Module.Header(f"🎉 {user_data['username']} 签到成功"),
            Module.Divider(),
            Module.Section(
                Element.Text(
                    f"📅 今日第 **{rank}** 位签到\n"
                    f"⚡ 获得活力 **{BASE_ENERGY}** 点 + 连签奖励 **{user_data['consecutive_bonus']}** 点\n"
                    f"💡 活力总值 **{user_data['energy_total']}** 点\n"
                    f"🔥 连续签到 **{user_data['consecutive_days']}** 天\n"
                    f"🏆 累计签到 **{user_data['total_days']}** 天"
                ),
                Element.Button('📌 我也要签到', value='sign', click=Types.Click.RETURN_VAL)
            ),
            theme=Types.Theme.SUCCESS
        )
    )

# ---------------------- 命令处理逻辑 ----------------------
async def sign_command(msg: Message):
    """处理 /sign 命令"""
    user_id = str(msg.author.id)
    username = msg.author.nickname or msg.author.username
    
    # 检查是否已签到
    if user_id in get_daily_sign_list():
        await msg.reply(CardMessage(
            Card(
                Module.Header('⚠️ 签到提醒'),
                Module.Section('您今天已经签到过了！'),
                theme=Types.Theme.WARNING
            )
        ))
        return
    
    # 更新数据并发送卡片
    user_data = update_sign_data(user_id, username)
    user_data['user_id'] = user_id  # 确保包含 user_id 字段
    cm = await generate_sign_card(user_data)
    await msg.reply(cm)

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def sign_button_click(bot: Bot, event: Event):
    """处理签到按钮点击事件"""
    if event.body['value'] != 'sign':
        return
    
    user_id = str(event.body['user_id'])
    username = event.body['user_info']['nickname'] or event.body['user_info']['username']
    channel_id = event.body['target_id']
    
    try:
        # 获取频道对象
        channel = await bot.client.fetch_public_channel(channel_id)
    except Exception as e:
        print(f"获取频道失败: {e}")
        return
    
    # 检查重复签到
    if user_id in get_daily_sign_list():
        await channel.send(CardMessage(
            Card(
                Module.Header('⚠️ 签到提醒'),
                Module.Section(f'{username} 今天已经签到过了！'),
                theme=Types.Theme.WARNING
            )
        ))
        return
    
    # 更新数据并发送卡片
    user_data = update_sign_data(user_id, username)
    user_data['user_id'] = user_id
    cm = await generate_sign_card(user_data)
    await channel.send(cm)

@bot.command(name='sign-status')
async def check_sign_status(msg: Message):
    """查看签到状态"""
    user_id = str(msg.author.id)
    user = db.get_user(user_id)
    
    if not user:
        await msg.reply('您还没有签到记录！')
        return
    
    cm = CardMessage(
        Card(
            Module.Header(f"📊 {user['username']} 的签到统计"),
            Module.Divider(),
            Module.Section(
                Element.Text(
                    f"🔥 连续签到: {user['consecutive_days']} 天\n"
                    f"🎯 累计签到: {user['total_days']} 天\n"
                    f"⚡ 总活力值: {user['energy_total']}\n"
                    f"⏰ 上次签到: {user['last_sign'][:10]}"
                )
            ),
            theme=Types.Theme.INFO
        )
    )
    await msg.reply(cm)

@bot.command(name='sign-reset', prefixes=['!'])
async def reset_sign_data(msg: Message):
    """重置数据（管理员命令）"""
    if not msg.author.is_admin:
        await msg.reply('权限不足！')
        return
    
    db.reset_data()
    await msg.reply('签到数据已重置！')

if __name__ == '__main__':
    bot.run()