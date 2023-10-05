from nicegui import ui
import sys, os, json, subprocess, importlib, re, threading, signal
import logging, traceback
import time
import asyncio
# from functools import partial

from utils.config import Config
from utils.common import Common
from utils.logger import Configure_logger
from utils.audio import Audio

"""
全局变量
"""
# 创建一个全局变量，用于表示程序是否正在运行
running_flag = False

# 创建一个子进程对象，用于存储正在运行的外部程序
running_process = None

common = None
config = None
audio = None
my_handle = None
config_path = None


web_server_port = 12345

def init():
    global config_path, config, common

    common = Common()

    if getattr(sys, 'frozen', False):
        # 当前是打包后的可执行文件
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
        file_relative_path = os.path.dirname(os.path.abspath(bundle_dir))
    else:
        # 当前是源代码
        file_relative_path = os.path.dirname(os.path.abspath(__file__))

    # logging.info(file_relative_path)

    # 初始化文件夹
    def init_dir():
        # 创建日志文件夹
        log_dir = os.path.join(file_relative_path, 'log')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建音频输出文件夹
        audio_out_dir = os.path.join(file_relative_path, 'out')
        if not os.path.exists(audio_out_dir):
            os.makedirs(audio_out_dir)
            
        # # 创建配置文件夹
        # config_dir = os.path.join(file_relative_path, 'config')
        # if not os.path.exists(config_dir):
        #     os.makedirs(config_dir)

    init_dir()

    # 配置文件路径
    config_path = os.path.join(file_relative_path, 'config.json')

    audio = Audio(config_path, 2)

    # 日志文件路径
    file_path = "./log/log-" + common.get_bj_time(1) + ".txt"
    Configure_logger(file_path)

    # 获取 httpx 库的日志记录器
    httpx_logger = logging.getLogger("httpx")
    # 设置 httpx 日志记录器的级别为 WARNING
    httpx_logger.setLevel(logging.WARNING)

    logging.debug("配置文件路径=" + str(config_path))

    # 实例化配置类
    config = Config(config_path)

init()



# 创建一个函数，用于运行外部程序
def run_external_program():
    global running_flag, running_process

    if running_flag:
        ui.notify("运行中，请勿重复运行")
        return

    try:
        running_flag = True

        # 在这里指定要运行的程序和参数
        # 例如，运行一个名为 "bilibili.py" 的 Python 脚本
        running_process = subprocess.Popen(["python", "bilibili.py"])

        ui.notify("程序开始运行")

    except Exception as e:
        ui.notify(f"错误：{e}")
        running_flag = False


# 定义一个函数，用于停止正在运行的程序
def stop_external_program():
    global running_flag, running_process

    if running_flag:
        try:
            running_process.terminate()  # 终止子进程
            running_flag = False
            ui.notify("程序已停止")
        except Exception as e:
            ui.notify(f"停止错误：{e}")


def save_config():
    global config, config_path
    try:
        with open(config_path, 'r', encoding="utf-8") as config_file:
            config_data = json.load(config_file)
    except Exception as e:
        logging.error(f"无法写入配置文件！\n{e}")
        ui.notify(f"无法写入配置文件！{e}")
        return False

    def common_textarea_handle(content):
        """通用的textEdit 多行文本内容处理

        Args:
            content (str): 原始多行文本内容

        Returns:
            _type_: 处理好的多行文本内容
        """
        # 通用多行分隔符
        separators = [" ", "\n"]

        ret = [token.strip() for separator in separators for part in content.split(separator) if (token := part.strip())]
        if 0 != len(ret):
            ret = ret[1:]

        return ret


    try:
        config_data["platform"] = select_platform.value
        config_data["room_display_id"] = input_room_display_id.value
        config_data["chat_type"] = select_chat_type.value
        config_data["need_lang"] = select_need_lang.value
        config_data["before_prompt"] = input_before_prompt.value
        config_data["after_prompt"] = input_after_prompt.value

        """
        LLM
        """
        config_data["openai"]["api"] = input_openai_api.value
        config_data["openai"]["api_key"] = common_textarea_handle(textarea_openai_api_key.value)
        config_data["chatgpt"]["model"] = select_chatgpt_model.value
        config_data["chatgpt"]["temperature"] = round(float(input_chatgpt_temperature.value), 1)
        config_data["chatgpt"]["max_tokens"] = int(input_chatgpt_max_tokens.value)
        config_data["chatgpt"]["top_p"] = round(float(input_chatgpt_top_p.value), 1)
        config_data["chatgpt"]["presence_penalty"] = round(float(input_chatgpt_presence_penalty.value), 1)
        config_data["chatgpt"]["frequency_penalty"] = round(float(input_chatgpt_frequency_penalty.value), 1)
        config_data["chatgpt"]["preset"] = input_chatgpt_preset.value

        """
        TTS
        """
        config_data["edge-tts"]["voice"] = select_edge_tts_voice.value
        config_data["edge-tts"]["rate"] = input_edge_tts_rate.value
        config_data["edge-tts"]["volume"] = input_edge_tts_volume.value

        config_data["vits"]["config_path"] = input_vits_config_path.value
        config_data["vits"]["api_ip_port"] = input_vits_api_ip_port.value
        config_data["vits"]["id"] = input_vits_id.value
        config_data["vits"]["lang"] = select_vits_lang.value
        config_data["vits"]["length"] = input_vits_length.value
        config_data["vits"]["noise"] = input_vits_noise.value
        config_data["vits"]["noisew"] = input_vits_noisew.value
        config_data["vits"]["max"] = input_vits_max.value
        config_data["vits"]["format"] = input_vits_format.value
        config_data["vits"]["sdp_radio"] = input_vits_sdp_radio.value

        config_data["vits_fast"]["config_path"] = input_vits_fast_config_path.value
        config_data["vits_fast"]["api_ip_port"] = input_vits_fast_api_ip_port.value
        config_data["vits_fast"]["character"] = input_vits_fast_character.value
        config_data["vits_fast"]["language"] = select_vits_fast_language.value
        config_data["vits_fast"]["speed"] = input_vits_fast_speed.value
        
        config_data["elevenlabs"]["api_key"] = input_elevenlabs_api_key.value
        config_data["elevenlabs"]["voice"] = input_elevenlabs_voice.value
        config_data["elevenlabs"]["model"] = input_elevenlabs_model.value

        config_data["genshinvoice_top"]["speaker"] = select_genshinvoice_top_speaker.value
        config_data["genshinvoice_top"]["noise"] = input_genshinvoice_top_noise.value
        config_data["genshinvoice_top"]["noisew"] = input_genshinvoice_top_noisew.value
        config_data["genshinvoice_top"]["length"] = input_genshinvoice_top_length.value
        config_data["genshinvoice_top"]["format"] = input_genshinvoice_top_format.value

        config_data["bark_gui"]["api_ip_port"] = input_bark_gui_api_ip_port.value
        config_data["bark_gui"]["spk"] = input_bark_gui_spk.value
        config_data["bark_gui"]["generation_temperature"] = input_bark_gui_generation_temperature.value
        config_data["bark_gui"]["waveform_temperature"] = input_bark_gui_waveform_temperature.value
        config_data["bark_gui"]["end_of_sentence_probability"] = input_bark_gui_end_of_sentence_probability.value
        config_data["bark_gui"]["quick_generation"] = switch_bark_gui_quick_generation.value
        config_data["bark_gui"]["seed"] = input_bark_gui_seed.value
        config_data["bark_gui"]["batch_count"] = input_bark_gui_batch_count.value

        config_data["vall_e_x"]["api_ip_port"] = input_vall_e_x_api_ip_port.value
        config_data["vall_e_x"]["language"] = select_vall_e_x_language.value
        config_data["vall_e_x"]["accent"] = select_vall_e_x_accent.value
        config_data["vall_e_x"]["voice_preset"] = input_vall_e_x_voice_preset.value
        config_data["vall_e_x"]["voice_preset_file_path"] = input_vall_e_x_voice_preset_file_path.value
    except Exception as e:
        logging.error(f"无法写入配置文件！\n{e}")

    # return True

    try:
        with open(config_path, 'w', encoding="utf-8") as config_file:
            json.dump(config_data, config_file, indent=2, ensure_ascii=False)
            config_file.flush()  # 刷新缓冲区，确保写入立即生效

        logging.info("配置数据已成功写入文件！")
        ui.notify("配置数据已成功写入文件！")

        return True
    except Exception as e:
        logging.error(f"无法写入配置文件！\n{e}")
        ui.notify(f"无法写入配置文件！\n{e}")
        return False


"""
webui
"""
with ui.tabs().classes('w-full') as tabs:
    common_config_page = ui.tab('通用配置')
    llm_page = ui.tab('大语言模型')
    tts_page = ui.tab('文本转语音')
    svc_page = ui.tab('变声')
    copywriting_page = ui.tab('文案')
    docs_page = ui.tab('文档')
    about_page = ui.tab('关于')

with ui.tab_panels(tabs, value=common_config_page).classes('w-full'):
    with ui.tab_panel(common_config_page):
        with ui.grid(columns=2):
            select_platform = ui.select(label='平台', options={'talk': '聊天模式', 'bilibli': '哔哩哔哩', 'dy': '抖音', 'ks': '快手', 'douyu': '斗鱼'}, value=config.get("platform"))
        with ui.grid(columns=2):
            input_room_display_id = ui.input(label='直播间号', placeholder='一般为直播间URL最后/后面的字母或数字', value=config.get("room_display_id"))
        with ui.grid(columns=2):
            select_chat_type = ui.select(
                label='聊天类型', 
                options={
                    'none': '不启用', 
                    'reread': '复读机', 
                    'chatgpt': 'ChatGPT/闻达', 
                    'claude': 'Claude', 
                    'claude2': 'Claude2',
                    'chatglm': 'ChatGLM',
                    'chat_with_file': 'chat_with_file',
                    'chatterbot': 'Chatterbot',
                    'text_generation_webui': 'text_generation_webui',
                    'sparkdesk': '讯飞星火',
                    'langchain_chatglm': 'langchain_chatglm',
                    'zhipu': '智谱AI',
                    'bard': 'Bard',
                    'yiyan': '文心一言',
                    'tongyi': '通义千问',
                }, 
                value=config.get("chat_type")
            )
        with ui.grid(columns=2):
            select_audio_synthesis_type = ui.select(
                label='语音合成', 
                options={
                    'edge-tts': 'Edge-TTS', 
                    'vits': 'VITS', 
                    'vits_fast': 'VITS-Fast', 
                    'elevenlabs': 'elevenlabs',
                    'genshinvoice_top': 'genshinvoice_top',
                    'bark_gui': 'bark_gui',
                    'vall_e_x': 'VALL-E-X',
                }, 
                value=config.get("audio_synthesis_type")
            )
        with ui.grid(columns=2):
            select_need_lang = ui.select(
                label='回复语言', 
                options={'none': '所有', 'zh': '中文', 'en': '英文', 'jp': '日文'}, 
                value=config.get("need_lang")
            )
        with ui.grid(columns=2):
            input_before_prompt = ui.input(label='提示词前缀', placeholder='此配置会追加在弹幕前，再发送给LLM处理', value=config.get("before_prompt"))
        with ui.grid(columns=2):
            input_after_prompt = ui.input(label='提示词后缀', placeholder='此配置会追加在弹幕后，再发送给LLM处理', value=config.get("after_prompt"))
        
    
    with ui.tab_panel(llm_page):
        with ui.card():
            ui.label("ChatGPT/闻达")
            with ui.grid(columns=2):
                input_openai_api = ui.input(label='API地址', placeholder='API请求地址，支持代理', value=config.get("openai", "api"))
            with ui.grid(columns=2):
                textarea_openai_api_key = ui.textarea(label='API密钥', placeholder='API KEY，支持代理', value=config.get("openai", "api_key"))
            with ui.grid(columns=2):
                chatgpt_models = ["gpt-3.5-turbo",
                    "gpt-3.5-turbo-0301",
                    "gpt-3.5-turbo-0613",
                    "gpt-3.5-turbo-16k",
                    "gpt-3.5-turbo-16k-0613",
                    "gpt-4",
                    "gpt-4-0314",
                    "gpt-4-0613",
                    "gpt-4-32k",
                    "gpt-4-32k-0314",
                    "gpt-4-32k-0613",
                    "text-embedding-ada-002",
                    "text-davinci-003",
                    "text-davinci-002",
                    "text-curie-001",
                    "text-babbage-001",
                    "text-ada-001",
                    "text-moderation-latest",
                    "text-moderation-stable",
                    "rwkv"]
                data_json = {}
                for line in chatgpt_models:
                    data_json[line] = line
                select_chatgpt_model = ui.select(
                    label='模型', 
                    options=data_json, 
                    value=config.get("chatgpt", "model")
                )
            with ui.grid(columns=2):
                input_chatgpt_temperature = ui.input(label='温度', placeholder='控制生成文本的随机性。较高的温度值会使生成的文本更随机和多样化，而较低的温度值会使生成的文本更加确定和一致。', value=config.get("chatgpt", "temperature"))
            with ui.grid(columns=2):
                input_chatgpt_max_tokens = ui.input(label='最大令牌数', placeholder='限制生成回答的最大长度。', value=config.get("chatgpt", "max_tokens"))
            with ui.grid(columns=2):
                input_chatgpt_top_p = ui.input(label='前p个选择', placeholder='Nucleus采样。这个参数控制模型从累积概率大于一定阈值的令牌中进行采样。较高的值会产生更多的多样性，较低的值会产生更少但更确定的回答。', value=config.get("chatgpt", "top_p"))
            with ui.grid(columns=2):
                input_chatgpt_presence_penalty = ui.input(label='存在惩罚', placeholder='控制模型生成回答时对给定问题提示的关注程度。较高的存在惩罚值会减少模型对给定提示的重复程度，鼓励模型更自主地生成回答。', value=config.get("chatgpt", "presence_penalty"))
            with ui.grid(columns=2):
                input_chatgpt_frequency_penalty = ui.input(label='存在惩罚', placeholder='控制生成回答时对已经出现过的令牌的惩罚程度。较高的频率惩罚值会减少模型生成已经频繁出现的令牌，以避免重复和过度使用特定词语。', value=config.get("chatgpt", "frequency_penalty"))
            with ui.grid(columns=2):
                input_chatgpt_preset = ui.input(label='预设', placeholder='用于指定一组预定义的设置，以便模型更好地适应特定的对话场景。', value=config.get("chatgpt", "preset"))
            
    with ui.tab_panel(tts_page):
        with ui.card():
            ui.label("Edge-TTS")
            with ui.grid(columns=2):
                with open('data\edge-tts-voice-list.txt', 'r') as file:
                    file_content = file.read()
                # 按行分割内容，并去除每行末尾的换行符
                lines = file_content.strip().split('\n')
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_edge_tts_voice = ui.select(
                    label='说话人', 
                    options=data_json, 
                    value=config.get("edge-tts", "voice")
                )
            with ui.grid(columns=2):
                input_edge_tts_rate = ui.input(label='语速增益', placeholder='语速增益 默认是 +0%，可以增减，注意 + - %符合别搞没了，不然会影响语音合成', value=config.get("edge-tts", "rate"))
            with ui.grid(columns=2):
                input_edge_tts_volume = ui.input(label='音量增益', placeholder='音量增益 默认是 +0%，可以增减，注意 + - %符合别搞没了，不然会影响语音合成', value=config.get("edge-tts", "volume"))
        with ui.card():
            ui.label("VITS")
            with ui.grid(columns=2):
                select_vits_type = ui.select(
                    label='类型', 
                    options={'vits': 'vits', 'bert_vits2': 'bert_vits2'}, 
                    value=config.get("vits", "type")
                )
            with ui.grid(columns=2):
                input_vits_config_path = ui.input(label='配置文件路径', placeholder='模型配置文件存储路径', value=config.get("vits", "config_path"))
            with ui.grid(columns=2):
                input_vits_api_ip_port = ui.input(label='API地址', placeholder='vits-simple-api启动后监听的ip端口地址', value=config.get("vits", "api_ip_port"))
            with ui.grid(columns=2):
                input_vits_id = ui.input(label='说话人ID', placeholder='API启动时会给配置文件重新划分id，一般为拼音顺序排列，从0开始', value=config.get("vits", "id"))
            with ui.grid(columns=2):
                select_vits_lang = ui.select(
                    label='语言', 
                    options={'自动': '自动', '中文': '中文', '英文': '英文', '日文': '日文'}, 
                    value=config.get("vits", "lang")
                )
            with ui.grid(columns=2):
                input_vits_length = ui.input(label='语音长度', placeholder='调节语音长度，相当于调节语速，该数值越大语速越慢', value=config.get("vits", "length"))
            with ui.grid(columns=2):
                input_vits_noise = ui.input(label='噪声', placeholder='控制感情变化程度', value=config.get("vits", "noise"))
            with ui.grid(columns=2):
                input_vits_noisew = ui.input(label='噪声偏差', placeholder='控制音素发音长度', value=config.get("vits", "noisew"))
            with ui.grid(columns=2):
                input_vits_max = ui.input(label='分段阈值', placeholder='按标点符号分段，加起来大于max时为一段文本。max<=0表示不分段。', value=config.get("vits", "max"))
            with ui.grid(columns=2):
                input_vits_format = ui.input(label='音频格式', placeholder='支持wav,ogg,silk,mp3,flac', value=config.get("vits", "format"))
            with ui.grid(columns=2):
                input_vits_sdp_radio = ui.input(label='SDP/DP混合比', placeholder='SDP/DP混合比：SDP在合成时的占比，理论上此比率越高，合成的语音语调方差越大。', value=config.get("vits", "sdp_radio"))
        with ui.card():
            ui.label("VITS-Fast")
            with ui.grid(columns=2):
                input_vits_fast_config_path = ui.input(label='配置文件路径', placeholder='配置文件的路径，例如：E:\\inference\\finetune_speaker.json', value=config.get("vits_fast", "config_path"))
            with ui.grid(columns=2):
                input_vits_fast_api_ip_port = ui.input(label='API地址', placeholder='推理服务运行的链接（需要完整的URL）', value=config.get("vits_fast", "api_ip_port"))
            with ui.grid(columns=2):
                input_vits_fast_character = ui.input(label='说话人', placeholder='选择的说话人，配置文件中的speaker中的其中一个', value=config.get("vits_fast", "character"))
            with ui.grid(columns=2):
                select_vits_fast_language = ui.select(
                    label='语言', 
                    options={'自动识别': '自动识别', '日本語': '日本語', '简体中文': '简体中文', 'English': 'English', 'Mix': 'Mix'}, 
                    value=config.get("vits_fast", "language")
                )
            with ui.grid(columns=2):
                input_vits_fast_speed = ui.input(label='语速', placeholder='语速，默认为1', value=config.get("vits_fast", "speed"))
        with ui.card():
            ui.label("elevenlabs")
            with ui.grid(columns=2):
                input_elevenlabs_api_key = ui.input(label='api密钥', placeholder='elevenlabs密钥，可以不填，默认也有一定额度的免费使用权限，具体多少不知道', value=config.get("elevenlabs", "api_key"))
            with ui.grid(columns=2):
                input_elevenlabs_voice = ui.input(label='说话人', placeholder='选择的说话人名', value=config.get("elevenlabs", "voice"))
            with ui.grid(columns=2):
                input_elevenlabs_model = ui.input(label='模型', placeholder='选择的模型', value=config.get("elevenlabs", "model"))
        with ui.card():
            ui.label("genshinvoice.top")
            with ui.grid(columns=2):
                with open('data\genshinvoice_top_speak_list.txt', 'r', encoding='utf-8') as file:
                    file_content = file.read()
                # 按行分割内容，并去除每行末尾的换行符
                lines = file_content.strip().split('\n')
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_genshinvoice_top_speaker = ui.select(
                    label='角色', 
                    options=data_json, 
                    value=config.get("genshinvoice_top", "speaker")
                )
            with ui.grid(columns=2):
                input_genshinvoice_top_noise = ui.input(label='感情', placeholder='控制感情变化程度，默认为0.2', value=config.get("genshinvoice_top", "noise"))
            with ui.grid(columns=2):
                input_genshinvoice_top_noisew = ui.input(label='音素长度', placeholder='控制音节发音长度变化程度，默认为0.9', value=config.get("genshinvoice_top", "noisew"))
            with ui.grid(columns=2):
                input_genshinvoice_top_length = ui.input(label='语速', placeholder='可用于控制整体语速。默认为1.2', value=config.get("genshinvoice_top", "length"))
            with ui.grid(columns=2):
                input_genshinvoice_top_format = ui.input(label='格式', placeholder='原有接口以WAV格式合成语音，在MP3格式合成语音的情况下，涉及到音频格式转换合成速度会变慢，建议选择WAV格式', value=config.get("genshinvoice_top", "format"))
        with ui.card():
            ui.label("bark_gui")
            with ui.grid(columns=2):
                input_bark_gui_api_ip_port = ui.input(label='API地址', placeholder='bark-gui开启webui后监听的IP和端口地址', value=config.get("bark_gui", "api_ip_port"))
            with ui.grid(columns=2):
                input_bark_gui_spk = ui.input(label='说话人', placeholder='选择的说话人，webui的voice中对应的说话人', value=config.get("bark_gui", "spk"))
            with ui.grid(columns=2):
                input_bark_gui_generation_temperature = ui.input(label='生成温度', placeholder='控制合成过程中生成语音的随机性。较高的值（接近1.0）会使输出更加随机，而较低的值（接近0.0）则使其更加确定性和集中。', value=config.get("bark_gui", "generation_temperature"))
            with ui.grid(columns=2):
                input_bark_gui_waveform_temperature = ui.input(label='波形温度', placeholder='类似于generation_temperature，但该参数专门控制从语音模型生成的波形的随机性', value=config.get("bark_gui", "waveform_temperature"))
            with ui.grid(columns=2):
                input_bark_gui_end_of_sentence_probability = ui.input(label='句末概率', placeholder='该参数确定在句子结尾添加停顿或间隔的可能性。较高的值会增加停顿的几率，而较低的值则会减少。', value=config.get("bark_gui", "end_of_sentence_probability"))
            with ui.grid(columns=2):
                switch_bark_gui_quick_generation = ui.switch('快速生成', value=config.get("bark_gui", "quick_generation"))
            with ui.grid(columns=2):
                input_bark_gui_seed = ui.input(label='随机种子', placeholder='用于随机数生成器的种子值。使用特定的种子确保相同的输入文本每次生成的语音输出都是相同的。值为-1表示将使用随机种子。', value=config.get("bark_gui", "seed"))
            with ui.grid(columns=2):
                input_bark_gui_batch_count = ui.input(label='批量数', placeholder='指定一次批量合成的句子或话语数量。将其设置为1意味着逐句合成一次。', value=config.get("bark_gui", "batch_count"))
        with ui.card():
            ui.label("vall_e_x")
            with ui.grid(columns=2):
                input_vall_e_x_api_ip_port = ui.input(label='API地址', placeholder='VALL-E-X启动后监听的ip端口地址', value=config.get("vall_e_x", "api_ip_port"))
            with ui.grid(columns=2):
                select_vall_e_x_language = ui.select(
                    label='language', 
                    options={'auto-detect':'auto-detect', 'English':'English', '中文':'中文', '日本語':'日本語', 'Mix':'Mix'}, 
                    value=config.get("vall_e_x", "language")
                )
            with ui.grid(columns=2):
                select_vall_e_x_accent = ui.select(
                    label='accent', 
                    options={'no-accent':'no-accent', 'English':'English', '中文':'中文', '日本語':'日本語'}, 
                    value=config.get("vall_e_x", "accent")
                )
            with ui.grid(columns=2):
                input_vall_e_x_voice_preset = ui.input(label='voice preset', placeholder='VALL-E-X说话人预设名（Prompt name）', value=config.get("vall_e_x", "voice_preset"))
            with ui.grid(columns=2):
                input_vall_e_x_voice_preset_file_path = ui.input(label='voice_preset_file_path', placeholder='VALL-E-X说话人预设文件路径（npz）', value=config.get("vall_e_x", "voice_preset_file_path"))
    with ui.tab_panel(svc_page):
        ui.label('待完善')
    with ui.tab_panel(copywriting_page):
        ui.label('待完善')
    with ui.tab_panel(docs_page):
        ui.label('待完善')
    with ui.tab_panel(about_page):
        ui.label('待完善')

with ui.grid(columns=3):
    save_button = ui.button('保存配置', on_click=lambda: save_config())
    run_button = ui.button('一键运行', on_click=lambda: run_external_program())
    # 创建一个按钮，用于停止正在运行的程序
    stop_button = ui.button("停止运行", on_click=lambda: stop_external_program())
    # stop_button.enabled = False  # 初始状态下停止按钮禁用

ui.run()