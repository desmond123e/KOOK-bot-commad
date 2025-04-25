import os
import json
import random
import chardet
from khl import Message

# 全局游戏状态存储
game_pools = {}  # 结构：{channel_id: {'encounters':[], 'events':[], 'opportunities':[]}}

def _resolve_path(filename: str) -> str:
    """修正路径计算方法"""
    # 获取当前文件的绝对路径（game_handler.py所在目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 上溯到项目根目录
    project_root = os.path.dirname(current_dir)
    # 组合数据文件路径
    return os.path.join(project_root, 'data', filename)

def load_data(filename: str) -> list:
    """强化版数据加载"""
    file_path = _resolve_path(filename)
    
    # 增强错误检测
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件 {filename} 不存在于路径：{file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"⚠️ 文件 {filename} 为空")
    
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
            
            # 优先尝试UTF-8解码
            try:
                data = json.loads(raw.decode('utf-8-sig'))
            except UnicodeDecodeError:
                # UTF-8失败时使用自动检测
                result = chardet.detect(raw)
                encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
                data = json.loads(raw.decode(encoding))
            
            # 强制类型校验
            if not isinstance(data, list):
                raise TypeError(f"{filename} 必须为JSON数组格式")
            if len(data) < 3:
                raise ValueError(f"{filename} 至少需要3条数据")
            
            # 调试输出
            print(f"[DEBUG] 已加载 {filename} ({len(data)}条): {data[:3]}...")
            return data
            
    except Exception as e:
        raise RuntimeError(f"加载 {filename} 失败: {str(e)}")

async def game_rule(msg: Message):
    """游戏规则"""
    await msg.reply("瓦洛兰特奇遇挑战游戏规则：10名玩家分为两队进行一场瓦洛兰特自定义比赛，但是每一回合都会随机出现相应的公共奇遇，和攻防两边的特殊事件，来从某些方面限制选手的发挥，如武器的使用，进攻的模式，技能的选择等，每一名选手比赛开始前通过私聊机器人可以获得一张特殊的机会卡，机会卡可以从一定程度上限制对手的发挥，或加强自己的团队，机会卡每一回合攻防两端分别只能使用一张。")

async def start_game(msg: Message):
    """增强初始化逻辑"""
    channel_id = msg.ctx.channel.id
    
    try:
        # 加载数据并验证
        encounters = load_data('encounters.json')
        events = load_data('events.json')
        opportunities = load_data('opportunities.json')
        
        # 初始化游戏池
        game_pools[channel_id] = {
            'encounters': encounters.copy(),  # 使用副本避免污染源数据
            'events': events.copy(),
            'opportunities': opportunities.copy()
        }
        
        await msg.reply(
            f"✅ 游戏初始化完成\n"
            f"神秘奇遇：{len(encounters)}条\n"
            f"攻防事件：{len(events)}条\n"
            f"机会卡牌：{len(opportunities)}条"
        )
        
    except Exception as e:
        await msg.reply(f"❌ 初始化失败：{str(e)}")
        # 打印详细错误日志
        import traceback
        traceback.print_exc()

async def play_round(msg: Message):
    """强化回合逻辑"""
    channel_id = msg.ctx.channel.id
    if channel_id not in game_pools:
        await msg.reply("⚠️ 请先使用 /game 开始游戏")
        return
    
    pool = game_pools[channel_id]
    
    try:
        # 抽取奇遇
        if len(pool['encounters']) == 0:
            await msg.reply("⚠️ 奇遇池已空，使用 /newgame 重置")
            return
        encounter = pool['encounters'].pop(random.randrange(len(pool['encounters'])))
        
        # 抽取事件（允许重复）
        attack_event = random.choice(pool['events'])
        defense_event = random.choice(pool['events'])
        
        await msg.reply(
            f"✨【奇遇】{encounter}\n"
            f"⚔️ 攻方事件：{attack_event}\n"
            f"🛡️ 守方事件：{defense_event}\n"
            f"剩余奇遇：{len(pool['encounters'])}条"
        )
        
    except Exception as e:
        await msg.reply(f"‼️ 操作失败：{str(e)}")
        import traceback
        traceback.print_exc()

# get_opportunity 和 new_game 函数保持不变

async def trigger_encounter(msg: Message):
    """单独触发奇遇事件"""
    channel_id = msg.ctx.channel.id
    if channel_id not in game_pools:
        await msg.reply("⚠️ 请先使用 /game 初始化游戏")
        return
    
    pool = game_pools[channel_id]
    
    try:
        if not pool['encounters']:
            await msg.reply("⚠️ 奇遇池已枯竭，使用 /newgame 重置")
            return
        
        # 抽取并移除奇遇
        encounter = pool['encounters'].pop(random.randrange(len(pool['encounters'])))
        await msg.reply(
            f"🌌【奇遇】\n"
            f"{encounter}\n"
            f"剩余奇遇：{len(pool['encounters'])}条"
        )
        
    except Exception as e:
        await msg.reply(f"‼️ 奇遇触发失败：{str(e)}")

async def trigger_event(msg: Message):
    """单独触发攻防事件"""
    channel_id = msg.ctx.channel.id
    if channel_id not in game_pools:
        await msg.reply("⚠️ 请先使用 /game 初始化游戏")
        return
    
    pool = game_pools[channel_id]
    
    try:
        # 从完整事件池随机抽取（允许重复）
        attack_event = random.choice(pool['events'])
        defense_event = random.choice(pool['events'])
        
        await msg.reply(
            f"⚔️【事件】\n"
            f"⚔️ 攻方事件：{attack_event}\n"
            f"🛡️ 守方事件：{defense_event}"
        )
        
    except Exception as e:
        await msg.reply(f"‼️ 事件生成失败：{str(e)}")

# 移除原有的 play_round 函数

async def get_opportunity(msg: Message):
    """独立获取机会卡（不依赖游戏池）"""
    try:
        # 直接加载最新机会卡数据
        opportunities = load_data('opportunities.json')
        
        if not opportunities:
            await msg.reply("⚠️ 机会卡池为空，请联系管理员")
            return
        
        oppo = random.choice(opportunities)
        await msg.reply(f"🎴 机会卡：{oppo}")
        
    except Exception as e:
        await msg.reply(f"❌ 获取失败：{str(e)}")

async def new_game(msg: Message):
    """重置游戏进度"""
    channel_id = msg.ctx.channel.id
    if channel_id in game_pools:
        del game_pools[channel_id]
    await msg.reply("🔄 游戏已重置，可重新开始")