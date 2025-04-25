from datetime import datetime
from khl import Bot, Message, MessageTypes, Event, EventTypes
from khl.card import Card, CardMessage, Module, Types, Element, Struct
from handlers.database import Database
from handlers.quotes import get_random_quote
from typing import Optional, List, Dict

class OfflineHandler:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self._register_handlers()

    def _register_handlers(self):
        """内部注册按钮点击事件"""
        @self.bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
        async def _on_button_click(bot: Bot, event: Event):
            await self.handle_button_click(event)

    async def handle_button_click(self, event: Event):
        """处理按钮点击"""
        if event.body.get('value') != 'off':
            return

        user_id = str(event.body['user_id'])
        username = event.body['user_info'].get('nickname', '未知用户')
        channel = await self.bot.client.fetch_public_channel(event.body['target_id'])

        # 验证逻辑
        if error_card := await self._validate_request(user_id, username):
            return await channel.send(error_card)
        
        # 执行打卡
        quote = get_random_quote()
        self.db.record_offline(user_id, quote)
        await channel.send(self._create_success_card(username, quote))

    def create_off_command(self):
        """生成/off命令处理函数"""
        async def _off_command(msg: Message):
            user_id = str(msg.author.id)
            username = msg.author.nickname or msg.author.username
            channel = await self.bot.client.fetch_public_channel(msg.ctx.channel.id)

            if error_card := await self._validate_request(user_id, username):
                return await channel.send(error_card)
            
            quote = get_random_quote()
            self.db.record_offline(user_id, quote)
            await channel.send(self._create_success_card(username, quote))

        return _off_command

    async def _validate_request(self, user_id: str, username: str) -> Optional[CardMessage]:
        """统一验证逻辑"""
        today = datetime.now().strftime('%Y-%m-%d')
        signed_users = self.db.get_daily_sign(today)
        if user_id not in signed_users:
            return self._create_error_card(f"{username} 请先完成签到再打卡下班！还没上班就想下班")
        if self.db.get_today_off_status(user_id):
            return self._create_error_card(f"{username} 今日已打过下班卡啦！下班了就去好生睡觉")
        return None

    def _create_success_card(self, username: str, quote: str) -> CardMessage:
        """成功卡片模板"""
        return CardMessage(
            Card(
                Module.Header(f'🎉 {username} 下班打卡'),
                Module.Divider(),
                Module.Section(
                    Element.Text(f"「{quote}」\n⏰ {datetime.now().strftime('%H:%M')}"),
                    Element.Button('📌 我也要打卡', value='off', click=Types.Click.RETURN_VAL)
                ),
                theme=Types.Theme.SECONDARY
            )
        )

    def _create_error_card(self, reason: str) -> CardMessage:
        """错误卡片模板"""
        return CardMessage(
            Card(
                Module.Header('⚠️ 打卡失败'),
                Module.Section(reason),
                theme=Types.Theme.DANGER
            )
        )