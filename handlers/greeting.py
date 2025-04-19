import random
from khl import Bot, Message
from bot import config

bot = Bot(token=config['token'])

# 准备多种打招呼的回复
greetings = [
    "放学一起走么？小男朋友😊",
    "拒绝女色，从你做起，我做不到🤗",
    "我们现在是宝宝关系，可以叫宝宝但是没关系🤩",
    "像我这种屌丝跟你提出交往的话，你会报警吗？😄",
    "睡不着觉，因为睡不着你👋",
    "我这一生行善积德，怎么就等不来你的消息呢？",
    "哥哥你真好，守男德，不联系前任也不联系现任",
    "你怎么只和她聊天，我家也有只会后空翻的猫",
    "不珍惜我算了，我去舔别人了",
    "我和你刚聊的那个女的掉水里你救谁",
    "如果想我，但你害羞，你可以跟我说晚安",
    "不好意思，忘记回你消息了，刚刚在玩手机",
    "发现一个岛，叫我爱你知布知岛",
    "只是想想吗？不想见我吗？"
]

async def greet(msg: Message):
    # 随机选择一个打招呼的回复
    response = random.choice(greetings)
    # 获取发送打招呼的用户名
    username = msg.author.username
    # 个性化打招呼，并发送消息
    await msg.reply(f"{username}, {response}")

