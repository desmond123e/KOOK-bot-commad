from bot import bot
from handlers.command_handler import show_help, random_map
from handlers.match_handler import store_kd,start_kd_random_command, reset_participants, view_participants, select_captains, start_random_match, move_to_voice_channels
from handlers.greeting import greet
from handlers.rolling import roll_dice, countdown
from handlers.saveid import get_game_id, save_game_id
from handlers.captain_mock import select_captains_mock

# 注册 /帮助 命令
bot.command(name="help")(show_help)

# # 注册 /参加比赛 命令
# bot.command(name="kd")(join_match)

# 注册 /重新录入 命令
bot.command(name="delete")(reset_participants)

# 注册 /查看参赛选手 命令
bot.command(name="check")(view_participants)

# 注册 /随机地图 命令
bot.command(name="map")(random_map)

# 注册 /选马模式 命令
bot.command(name="captain")(select_captains)

# 注册 /随机匹配 、命令
bot.command(name="random")(start_random_match)

# 注册 /移动频道 命令
bot.command(name="move")(move_to_voice_channels)

# 注册 /打招呼 命令
bot.command(name="hello")(greet)

# 注册 /roll 命令
bot.command(name="roll")(roll_dice)

# 注册 倒计时 命令
bot.command(name="countdown")(countdown)

# 查询用户的游戏ID
bot.command(name="myid")(get_game_id)

# 注册命令保存用户游戏ID
bot.command(name="saveid")(save_game_id)

# 存储用户 KD 的命令
bot.command(name="kd")(store_kd)

# 注册命令 /kdrandom 开始kd匹配
bot.command(name="kdrandom")(start_kd_random_command)


bot.command(name='mockcap')(select_captains_mock)
# 启动机器人
if __name__ == "__main__":
    bot.run()