from bot.bot_factory import create_bot
from bridge.context import Context
from bridge.reply import *
from common import const
from common.log import logger
from common.singleton import singleton
from config import conf
from translate.factory import create_translator
from voice.factory import create_voice


@singleton
class Bridge(object):
    def __init__(self):
        self.btype = {
            "chat": const.CHATGPT,
            "voice_to_text": conf().get("voice_to_text", "openai"),
            "text_to_voice": conf().get("text_to_voice", "google"),
            "translate": conf().get("translate", "baidu"),
        }
        # 这边取配置的模型
        bot_type = conf().get("bot_type")
        if bot_type:
            self.btype["chat"] = bot_type
        else:
            model_type = conf().get("model") or const.GPT35
            if model_type in ["text-davinci-003"]:
                self.btype["chat"] = const.OPEN_AI
            if conf().get("use_azure_chatgpt", False):
                self.btype["chat"] = const.CHATGPTONAZURE
            if model_type in ["wenxin", "wenxin-4"]:
                self.btype["chat"] = const.BAIDU
            if model_type in ["MyModel"]:
                self.btype["chat"] = const.MyModel
            if model_type in ["xunfei"]:
                self.btype["chat"] = const.XUNFEI
            if model_type in [const.QWEN]:
                self.btype["chat"] = const.QWEN
            if model_type in [const.QWEN_TURBO, const.QWEN_PLUS, const.QWEN_MAX]:
                self.btype["chat"] = const.QWEN_DASHSCOPE
            if model_type and model_type.startswith("gemini"):
                self.btype["chat"] = const.GEMINI
            if model_type and model_type.startswith("glm"):
                self.btype["chat"] = const.ZHIPU_AI
            if model_type and model_type.startswith("claude-3"):
                self.btype["chat"] = const.CLAUDEAPI

            if model_type in ["claude"]:
                self.btype["chat"] = const.CLAUDEAI

            if model_type in [const.MOONSHOT, "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]:
                self.btype["chat"] = const.MOONSHOT

            if model_type in ["abab6.5-chat"]:
                self.btype["chat"] = const.MiniMax

            if conf().get("use_linkai") and conf().get("linkai_api_key"):
                self.btype["chat"] = const.LINKAI
                if not conf().get("voice_to_text") or conf().get("voice_to_text") in ["openai"]:
                    self.btype["voice_to_text"] = const.LINKAI
                if not conf().get("text_to_voice") or conf().get("text_to_voice") in ["openai", const.TTS_1, const.TTS_1_HD]:
                    self.btype["text_to_voice"] = const.LINKAI

        self.bots = {}
        self.chat_bots = {}

    # 模型对应的接口
    def get_bot(self, typename):
        if self.bots.get(typename) is None:
            logger.info("create bot {} for {}".format(self.btype[typename], typename))
            if typename == "text_to_voice":
                self.bots[typename] = create_voice(self.btype[typename])
            elif typename == "voice_to_text":
                self.bots[typename] = create_voice(self.btype[typename])
            elif typename == "chat":
                self.bots[typename] = create_bot(self.btype[typename])
            elif typename == "translate":
                self.bots[typename] = create_translator(self.btype[typename])
        return self.bots[typename]

    def get_bot_type(self, typename):
        return self.btype[typename]

    def fetch_reply_content(self, query, context: Context) -> Reply:
        return self.get_bot("chat").reply(query, context)

    def fetch_voice_to_text(self, voiceFile) -> Reply:
        return self.get_bot("voice_to_text").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text) -> Reply:
        return self.get_bot("text_to_voice").textToVoice(text)

    def fetch_translate(self, text, from_lang="", to_lang="en") -> Reply:
        return self.get_bot("translate").translate(text, from_lang, to_lang)

    def find_chat_bot(self, bot_type: str):
        if self.chat_bots.get(bot_type) is None:
            self.chat_bots[bot_type] = create_bot(bot_type)
        return self.chat_bots.get(bot_type)
    
    def fetch_file_content(self, file_path: str, context: Context) -> Reply:
        bot = self.get_bot("chat")  # 获取用于文件处理的 bot 实例
        
        # 通过 `MyModelBot` 的 `handle_file_upload` 处理文件上传
        if hasattr(bot, "handle_file_upload"):
            reply = bot.handle_file_upload(context)
            return reply
        else:
            logger.error("Bot does not support file handling.")
            return Reply(content="当前模型不支持文件处理", type=ReplyType.ERROR)

    def reset_bot(self):
        self.__init__()
