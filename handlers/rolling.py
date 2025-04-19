import random
import asyncio
from khl import Bot, Message

# 摇骰子功能
async def roll_dice(msg: Message, *args):
    # 判断是否提供了自定义范围
    if args and args[0].isdigit():
        max_value = int(args[0])
    else:
        max_value = 100  # 默认范围 1-100
    
    # 生成随机数
    result = random.randint(1, max_value)

    username = msg.author.username

    await msg.reply(f"🎲 {username}摇出了: {result} (范围: 1-{max_value})")

# 倒计时功能
async def countdown(msg: Message, *args):
    # 默认倒计时为60秒
    if args and args[0].isdigit():
        countdown_time = int(args[0])
    else:
        countdown_time = 60

    await msg.reply(f"⏳ 倒计时开始: {countdown_time}秒")

    # 倒计时逻辑
    for remaining in range(countdown_time, 0, -1):
        if remaining % 10 == 0 or remaining <= 5:
            await msg.reply(f"⏳ 还剩 {remaining} 秒")
        await asyncio.sleep(1)  # 等待 1 秒

    await msg.reply("⏰ 时间到！")

