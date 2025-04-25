import json
from khl import Bot, Message, MessageTypes, Event, EventTypes, PublicMessage
from khl.card import Card, CardMessage, Module, Types, Element, Struct

# 商品配置（保持原样）
SHOP_ITEMS = [
    {"id": 1, "name": "奶茶", "price": 20, "desc": "一杯香甜的奶茶！"},
    {"id": 2, "name": "活动指挥", "price": 200, "desc": "专属活动主持服务"},
    {"id": 3, "name": "专属头衔", "price": 100, "desc": "定制个人头衔（有效期7天）"}
]

def setup_shop(bot: Bot):
    @bot.command(name='shop')
    async def shop_cmd(msg: Message):
        """显示兑换商店（代码保持原样）"""
        card = Card()
        card.append(Module.Header("🛒 活力值兑换商店"))
        card.append(Module.Divider())
        for item in SHOP_ITEMS:
            card.append(
                Module.Section(
                    Element.Text(f"​**​{item['name']}​**​\n{item['desc']} - 需 {item['price']} 点活力值"),
                    Element.Button("兑换", value=f"shop_{item['id']}", click=Types.Click.RETURN_VAL)
                )
            )
            card.append(Module.Divider())
        card.append(Module.Context("点击兑换后，兑换结果将通过私信发送"))
        card.theme = Types.Theme.INFO
        await msg.reply(CardMessage(card))

    @bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
    async def shop_btn(bot: Bot, event: Event):
    """处理商店按钮点击（已修复隐藏字符）"""
    value = event.body['value']
    if not value.startswith("shop_"):
        return
    
    try:
        # 正确代码（无隐藏字符）
        msg = PublicMessage(​**​event.body['msg'])
        user_id = str(msg.author.id)
        username = msg.author.nickname or msg.author.username
        
            
            data = json.load(open("sign_data.json"))  # 直接读取数据避免导入依赖
            user = data['users'].get(user_id)
            
            if not user:
                await _send_dm(bot, user_id, "❌ 兑换失败：您还没有签到记录！")
                return
                
            if user['energy_total'] < item['price']:
                await _send_dm(bot, user_id, 
                    f"❌ {item['name']} 需要 {item['price']} 点活力值，当前余额：{user['energy_total']}")
                return
                
            user['energy_total'] -= item['price']
            json.dump(data, open("sign_data.json", 'w'), ensure_ascii=False, indent=4)
            
            await _send_dm(bot, user_id,
                f"🎉 成功兑换 {item['name']}！\n"
                f"扣除 {item['price']} 点，剩余余额：{user['energy_total']}\n"
                f"物品说明：{item['desc']}"
            )
            
        except Exception as e:
            print(f"兑换错误: {e}")
            await _send_dm(bot, user_id, "⚠️ 兑换操作异常，请联系管理员")

async def _send_dm(bot: Bot, user_id: str, content: str):
    """优化后的私信方法"""
    try:
        # 使用正确的 Kook API 方法创建私信频道
        dm_channel = await bot.client.create_dm(user_id)
        await dm_channel.send(content)
    except Exception as e:
        print(f"私信发送失败（用户ID：{user_id}）: {e}")