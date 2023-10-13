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

        config_data["thanks"]["entrance_enable"] = switch_thanks_entrance_enable.value
        config_data["thanks"]["entrance_copy"] = input_thanks_entrance_copy.value
        config_data["thanks"]["gift_enable"] = switch_thanks_gift_enable.value
        config_data["thanks"]["gift_copy"] = input_thanks_gift_copy.value
        config_data["thanks"]["lowest_price"] = round(float(input_thanks_lowest_price.value), 2)
        config_data["thanks"]["follow_enable"] = switch_thanks_follow_enable.value
        config_data["thanks"]["follow_copy"] = input_thanks_follow_copy.value

        # 音频随机变速
        config_data["audio_random_speed"]["normal"]["enable"] = switch_audio_random_speed_normal_enable.value
        config_data["audio_random_speed"]["normal"]["speed_min"] = round(float(input_audio_random_speed_normal_speed_min.value), 2)
        config_data["audio_random_speed"]["normal"]["speed_max"] = round(float(input_audio_random_speed_normal_speed_max.value), 2)
        config_data["audio_random_speed"]["copywriting"]["enable"] = switch_audio_random_speed_copywriting_enable.value
        config_data["audio_random_speed"]["copywriting"]["speed_min"] = round(float(input_audio_random_speed_copywriting_speed_min.value), 2)
        config_data["audio_random_speed"]["copywriting"]["speed_max"] = round(float(input_audio_random_speed_copywriting_speed_max.value), 2)

        config_data["live2d"]["enable"] = switch_live2d_enable.value
        config_data["live2d"]["port"] = int(input_live2d_port.value)

        tmp_arr = []
        # logging.info(schedule_var)
        for index in range(len(schedule_var) // 3):
            tmp_json = {
                "enable": False,
                "time": 60,
                "copy": []
            }
            tmp_json["enable"] = schedule_var[str(3 * index)].value
            tmp_json["time"] = round(float(schedule_var[str(3 * index + 1)].value), 1)
            tmp_json["copy"] = common_textarea_handle(schedule_var[str(3 * index + 2)].value)

            tmp_arr.append(tmp_json)
        # logging.info(tmp_arr)
        config_data["schedule"] = tmp_arr

        config_data["key_mapping"]["enable"] = switch_key_mapping_enable.value
        config_data["key_mapping"]["start_cmd"] = input_key_mapping_start_cmd.value
        tmp_arr = []
        # logging.info(key_mapping_config_var)
        for index in range(len(key_mapping_config_var) // 3):
            tmp_json = {
                "keywords": [],
                "keys": [],
                "similarity": 1
            }
            tmp_json["keywords"] = common_textarea_handle(key_mapping_config_var[str(3 * index)].value)
            tmp_json["keys"] = common_textarea_handle(key_mapping_config_var[str(3 * index + 1)].value)
            tmp_json["similarity"] = key_mapping_config_var[str(3 * index + 2)].value

            tmp_arr.append(tmp_json)
        # logging.info(tmp_arr)
        config_data["key_mapping"]["config"] = tmp_arr

        """
        LLM
        """
        if True:
            config_data["openai"]["api"] = input_openai_api.value
            config_data["openai"]["api_key"] = common_textarea_handle(textarea_openai_api_key.value)
            config_data["chatgpt"]["model"] = select_chatgpt_model.value
            config_data["chatgpt"]["temperature"] = round(float(input_chatgpt_temperature.value), 1)
            config_data["chatgpt"]["max_tokens"] = int(input_chatgpt_max_tokens.value)
            config_data["chatgpt"]["top_p"] = round(float(input_chatgpt_top_p.value), 1)
            config_data["chatgpt"]["presence_penalty"] = round(float(input_chatgpt_presence_penalty.value), 1)
            config_data["chatgpt"]["frequency_penalty"] = round(float(input_chatgpt_frequency_penalty.value), 1)
            config_data["chatgpt"]["preset"] = input_chatgpt_preset.value

            config_data["claude"]["slack_user_token"] = input_claude_slack_user_token.value
            config_data["claude"]["bot_user_id"] = input_claude_bot_user_id.value

            config_data["claude2"]["cookie"] = input_claude2_cookie.value
            config_data["claude2"]["use_proxy"] = switch_claude2_use_proxy.value
            config_data["claude2"]["proxies"]["http"] = input_claude2_proxies_http.value
            config_data["claude2"]["proxies"]["https"] = input_claude2_proxies_https.value
            config_data["claude2"]["proxies"]["socks5"] = input_claude2_proxies_socks5.value

            config_data["chatglm"]["api_ip_port"] = input_chatglm_api_ip_port.value
            config_data["chatglm"]["max_length"] = int(input_chatglm_max_length.value)
            config_data["chatglm"]["top_p"] = round(float(input_chatglm_top_p.value), 1)
            config_data["chatglm"]["temperature"] = round(float(input_chatglm_temperature.value), 2)
            config_data["chatglm"]["history_enable"] = switch_chatglm_history_enable.value
            config_data["chatglm"]["history_max_len"] = int(input_chatglm_history_max_len.value)

            config_data["chat_with_file"]["chat_mode"] = select_chat_with_file_chat_mode.value
            config_data["chat_with_file"]["data_path"] = input_chat_with_file_data_path.value
            config_data["chat_with_file"]["separator"] = input_chat_with_file_separator.value
            config_data["chat_with_file"]["chunk_size"] = int(input_chat_with_file_chunk_size.value)
            config_data["chat_with_file"]["chunk_overlap"] = int(input_chat_with_file_chunk_overlap.value)
            config_data["chat_with_file"]["local_vector_embedding_model"] = select_chat_with_file_local_vector_embedding_model.value
            config_data["chat_with_file"]["chain_type"] = input_chat_with_file_chain_type.value
            config_data["chat_with_file"]["question_prompt"] = input_chat_with_file_question_prompt.value
            config_data["chat_with_file"]["local_max_query"] = int(input_chat_with_file_local_max_query.value)
            config_data["chat_with_file"]["show_token_cost"] = switch_chat_with_file_show_token_cost.value

            config_data["chatterbot"]["name"] = input_chatterbot_name.value
            config_data["chatterbot"]["db_path"] = input_chatterbot_db_path.value

            config_data["text_generation_webui"]["api_ip_port"] = input_text_generation_webui_api_ip_port.value
            config_data["text_generation_webui"]["max_new_tokens"] = int(input_text_generation_webui_max_new_tokens.value)
            config_data["text_generation_webui"]["mode"] = input_text_generation_webui_mode.value
            config_data["text_generation_webui"]["character"] = input_text_generation_webui_character.value
            config_data["text_generation_webui"]["instruction_template"] = input_text_generation_webui_instruction_template.value
            config_data["text_generation_webui"]["your_name"] = input_text_generation_webui_your_name.value

            config_data["sparkdesk"]["type"] = select_sparkdesk_type.value
            config_data["sparkdesk"]["cookie"] = input_sparkdesk_cookie.value
            config_data["sparkdesk"]["fd"] = input_sparkdesk_fd.value
            config_data["sparkdesk"]["GtToken"] = input_sparkdesk_GtToken.value
            config_data["sparkdesk"]["app_id"] = input_sparkdesk_app_id.value
            config_data["sparkdesk"]["api_secret"] = input_sparkdesk_api_secret.value
            config_data["sparkdesk"]["api_key"] = input_sparkdesk_api_key.value

            config_data["langchain_chatglm"]["api_ip_port"] = input_langchain_chatglm_api_ip_port.value
            config_data["langchain_chatglm"]["chat_type"] = select_langchain_chatglm_chat_type.value
            config_data["langchain_chatglm"]["knowledge_base_id"] = input_langchain_chatglm_knowledge_base_id.value
            config_data["langchain_chatglm"]["history_enable"] = switch_langchain_chatglm_history_enable.value
            config_data["langchain_chatglm"]["history_max_len"] = int(input_langchain_chatglm_history_max_len.value)

            config_data["zhipu"]["api_key"] = input_zhipu_api_key.value
            config_data["zhipu"]["model"] = select_zhipu_model.value
            config_data["zhipu"]["top_p"] = input_zhipu_top_p.value
            config_data["zhipu"]["temperature"] = input_zhipu_temperature.value
            config_data["zhipu"]["history_enable"] = switch_zhipu_history_enable.value
            config_data["zhipu"]["history_max_len"] = input_zhipu_history_max_len.value

            config_data["bard"]["token"] = input_bard_token.value

            config_data["yiyan"]["api_ip_port"] = input_yiyan_api_ip_port.value
            config_data["yiyan"]["type"] = select_yiyan_type.value
            config_data["yiyan"]["cookie"] = input_yiyan_cookie.value

            config_data["tongyi"]["type"] = select_tongyi_type.value
            config_data["tongyi"]["cookie_path"] = input_tongyi_cookie_path.value

        """
        TTS
        """
        if True:
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
    
        """
        SVC
        """
        if True:
            config_data["ddsp_svc"]["enable"] = switch_ddsp_svc_enable.value
            config_data["ddsp_svc"]["config_path"] = input_ddsp_svc_config_path.value
            config_data["ddsp_svc"]["api_ip_port"] = input_ddsp_svc_api_ip_port.value
            config_data["ddsp_svc"]["fSafePrefixPadLength"] = round(float(input_ddsp_svc_fSafePrefixPadLength.value), 1)
            config_data["ddsp_svc"]["fPitchChange"] = round(float(input_ddsp_svc_fPitchChange.value), 1)
            config_data["ddsp_svc"]["sSpeakId"] = int(input_ddsp_svc_sSpeakId.value)
            config_data["ddsp_svc"]["sampleRate"] = int(input_ddsp_svc_sampleRate.value)

            config_data["so_vits_svc"]["enable"] = switch_so_vits_svc_enable.value
            config_data["so_vits_svc"]["config_path"] = input_so_vits_svc_config_path.value
            config_data["so_vits_svc"]["api_ip_port"] = input_so_vits_svc_api_ip_port.value
            config_data["so_vits_svc"]["spk"] = input_so_vits_svc_spk.value
            config_data["so_vits_svc"]["tran"] = round(float(input_so_vits_svc_tran.value), 1)
            config_data["so_vits_svc"]["wav_format"] = input_so_vits_svc_wav_format.value

    except Exception as e:
        logging.error(f"无法写入配置文件！\n{e}")
        logging.error(traceback.format_exc())

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


def textarea_data_change(data):
    """
    字符串数组数据格式转换
    """
    tmp_str = ""
    for tmp in data:
        tmp_str = tmp_str + tmp + "\n"
    
    return tmp_str


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
            select_platform = ui.select(label='平台', options={'talk': '聊天模式', 'bilibili': '哔哩哔哩', 'dy': '抖音', 'ks': '快手', 'douyu': '斗鱼'}, value=config.get("platform"))

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
        
        with ui.card().style("margin:10px 0px"):
            ui.label('哔哩哔哩')
            with ui.grid(columns=3):
                select_bilibili_login_type = ui.select(
                    label='登录方式',
                    options={'手机扫描': '手机扫描', 'cookie': 'cookie', '不登录': '不登录'},
                    value=config.get("bilibili", "login_type")
                )
                input_bilibili_cookie = ui.input(label='cookie', placeholder='b站登录后F12抓网络包获取cookie，强烈建议使用小号！有封号风险', value=config.get("bilibili", "cookie"))
                input_bilibili_ac_time_value = ui.input(label='ac_time_value', placeholder='b站登录后，F12控制台，输入window.localStorage.ac_time_value获取(如果没有，请重新登录)', value=config.get("bilibili", "ac_time_value"))
        with ui.card().style("margin:10px 0px"):
            ui.label('音频播放')
            with ui.grid(columns=2):
                switch_play_audio_enable = ui.switch('启用', value=config.get("play_audio", "enable"))
                input_play_audio_out_path = ui.input(label='音频输出路径', placeholder='音频文件合成后存储的路径，支持相对路径或绝对路径', value=config.get("play_audio", "out_path"))
        with ui.card().style("margin:10px 0px"):
            ui.label('念弹幕')
            with ui.grid(columns=3):
                switch_read_comment_enable = ui.switch('启用', value=config.get("read_comment", "enable"))
                switch_read_comment_read_username_enable = ui.switch('念用户名', value=config.get("read_comment", "read_username_enable"))
                switch_read_comment_voice_change = ui.switch('变声', value=config.get("read_comment", "voice_change"))
            with ui.grid(columns=2):
                textarea_read_comment_read_username_copywriting = ui.textarea(label='念用户名文案', placeholder='念用户名时使用的文案，可以自定义编辑多个（换行分隔），实际中会随机一个使用', value=textarea_data_change(config.get("read_comment", "read_username_copywriting")))
        with ui.card().style("margin:10px 0px"):
            ui.label('念用户名')
            with ui.grid(columns=2):
                switch_read_user_name_enable = ui.switch('启用', value=config.get("read_user_name", "enable"))
                switch_read_user_name_voice_change = ui.switch('启用变声', value=config.get("read_user_name", "voice_change"))
            with ui.grid(columns=2):
                textarea_read_user_name_reply_before = ui.textarea(label='前置回复', placeholder='在正经回复前的念用户名的文案，目前是本地问答库-文本 触发时使用', value=textarea_data_change(config.get("read_user_name", "reply_before")))
                textarea_read_user_name_reply_after = ui.textarea(label='后置回复', placeholder='在正经回复后的念用户名的文案，目前是本地问答库-音频 触发时使用', value=textarea_data_change(config.get("read_user_name", "reply_after")))
        with ui.card().style("margin:10px 0px"):
            ui.label('日志')
            with ui.grid(columns=3):
                select_comment_log_type = ui.select(
                    label='弹幕日志类型',
                    options={'问答': '问答', '问题': '问题', '回答': '回答', '不记录': '不记录'},
                    value=config.get("comment_log_type")
                )

                switch_captions_enable = ui.switch('启用', value=config.get("captions", "enable"))
                input_captions_file_path = ui.input(label='字幕日志路径', placeholder='字幕日志存储路径', value=config.get("captions", "file_path"))
        with ui.card().style("margin:10px 0px"):
            ui.label('本地问答')
            with ui.grid(columns=4):
                switch_local_qa_text_enable = ui.switch('启用文本匹配', value=config.get("local_qa", "text", "enable"))
                select_local_qa_text_type = ui.select(
                    label='弹幕日志类型',
                    options={'json': '自定义json', 'text': '一问一答'},
                    value=config.get("local_qa", "text", "type")
                )
                input_local_qa_text_file_path = ui.input(label='文本问答数据路径', placeholder='本地问答文本数据存储路径', value=config.get("local_qa", "text", "file_path"))
                input_local_qa_text_similarity = ui.input(label='文本最低相似度', placeholder='最低文本匹配相似度，就是说用户发送的内容和本地问答库中设定的内容的最低相似度。\n低了就会被当做一般弹幕处理', value=config.get("local_qa", "text", "similarity"))
            with ui.grid(columns=4):
                switch_local_qa_audio_enable = ui.switch('启用音频匹配', value=config.get("local_qa", "audio", "enable"))
                input_local_qa_audio_file_path = ui.input(label='音频存储路径', placeholder='本地问答音频文件存储路径', value=config.get("local_qa", "audio", "file_path"))
                input_local_qa_audio_similarity = ui.input(label='音频最低相似度', placeholder='最低音频匹配相似度，就是说用户发送的内容和本地音频库中音频文件名的最低相似度。\n低了就会被当做一般弹幕处理', value=config.get("local_qa", "audio", "similarity"))
        with ui.card().style("margin:10px 0px"):
            ui.label('过滤')    
            with ui.grid(columns=2):
                textarea_filter_before_must_str = ui.textarea(label='弹幕前缀', placeholder='弹幕过滤，必须携带的触发前缀字符串（任一）\n例如：配置#，那么就需要发送：#你好', value=textarea_data_change(config.get("filter", "before_must_str")))
                textarea_filter_after_must_str = ui.textarea(label='弹幕后缀', placeholder='弹幕过滤，必须携带的触发后缀字符串（任一）\n例如：配置。那么就需要发送：你好。', value=textarea_data_change(config.get("filter", "before_must_str")))
            with ui.grid(columns=4):
                input_filter_badwords_path = ui.input(label='违禁词路径', placeholder='本地违禁词数据路径（你如果不需要，可以清空文件内容）', value=config.get("filter", "badwords_path"))
                input_filter_bad_pinyin_path = ui.input(label='违禁拼音路径', placeholder='本地违禁拼音数据路径（你如果不需要，可以清空文件内容）', value=config.get("filter", "bad_pinyin_path"))
                input_filter_max_len = ui.input(label='最大单词数', placeholder='最长阅读的英文单词数（空格分隔）', value=config.get("filter", "max_len"))
                input_filter_max_char_len = ui.input(label='最大单词数', placeholder='最长阅读的字符数，双重过滤，避免溢出', value=config.get("filter", "max_char_len"))
            with ui.grid(columns=4):
                input_filter_comment_forget_duration = ui.input(label='弹幕遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "comment_forget_duration"))
                input_filter_comment_forget_reserve_num = ui.input(label='弹幕保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "comment_forget_reserve_num"))
                input_filter_gift_forget_duration = ui.input(label='礼物遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "gift_forget_duration"))
                input_filter_gift_forget_reserve_num = ui.input(label='礼物保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "gift_forget_reserve_num"))
            with ui.grid(columns=4):
                input_filter_entrance_forget_duration = ui.input(label='入场遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "entrance_forget_duration"))
                input_filter_entrance_forget_reserve_num = ui.input(label='入场保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "entrance_forget_reserve_num"))
                input_filter_follow_forget_duration = ui.input(label='入场遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "follow_forget_duration"))
                input_filter_follow_forget_reserve_num = ui.input(label='入场保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "follow_forget_reserve_num"))
            with ui.grid(columns=4):
                input_filter_talk_forget_duration = ui.input(label='聊天遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "talk_forget_duration"))
                input_filter_talk_forget_reserve_num = ui.input(label='聊天保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "talk_forget_reserve_num"))
                input_filter_schedule_forget_duration = ui.input(label='定时遗忘间隔', placeholder='指的是每隔这个间隔时间（秒），就会丢弃这个间隔时间中接收到的数据，\n保留数据在以下配置中可以自定义', value=config.get("filter", "schedule_forget_duration"))
                input_filter_schedule_forget_reserve_num = ui.input(label='定时保留数', placeholder='保留最新收到的数据的数量', value=config.get("filter", "schedule_forget_reserve_num"))
        with ui.card().style("margin:10px 0px"):
            ui.label('答谢')     
            with ui.grid(columns=2):
                switch_thanks_entrance_enable = ui.switch('启用入场欢迎', value=config.get("thanks", "entrance_enable"))
                input_thanks_entrance_copy = ui.input(label='入场文案', placeholder='用户进入直播间的相关文案，请勿动 {username}，此字符串用于替换用户名', value=config.get("thanks", "entrance_copy"))
            with ui.grid(columns=3):
                switch_thanks_gift_enable = ui.switch('启用礼物答谢', value=config.get("thanks", "gift_enable"))
                input_thanks_gift_copy = ui.input(label='礼物文案', placeholder='用户赠送礼物的相关文案，请勿动 {username} 和 {gift_name}，此字符串用于替换用户名和礼物名', value=config.get("thanks", "gift_copy"))
                input_thanks_lowest_price = ui.input(label='最低答谢礼物价格', value=config.get("thanks", "lowest_price"), placeholder='设置最低答谢礼物的价格（元），低于这个设置的礼物不会触发答谢')
            with ui.grid(columns=2):
                switch_thanks_follow_enable = ui.switch('启用关注答谢', value=config.get("thanks", "follow_enable"))
                input_thanks_follow_copy = ui.input(label='关注文案', value=config.get("thanks", "follow_copy"), placeholder='用户关注时的相关文案，请勿动 {username}，此字符串用于替换用户名')
        
        with ui.card().style("margin:10px 0px"):
            ui.label('音频随机变速')     
            with ui.grid(columns=3):
                switch_audio_random_speed_normal_enable = ui.switch('普通音频变速', value=config.get("audio_random_speed", "normal", "enable"))
                input_audio_random_speed_normal_speed_min = ui.input(label='速度下限', value=config.get("audio_random_speed", "normal", "speed_min"))
                input_audio_random_speed_normal_speed_max = ui.input(label='速度上限', value=config.get("audio_random_speed", "normal", "speed_max"))
            with ui.grid(columns=3):
                switch_audio_random_speed_copywriting_enable = ui.switch('文案音频变速', value=config.get("audio_random_speed", "copywriting", "enable"))
                input_audio_random_speed_copywriting_speed_min = ui.input(label='速度下限', value=config.get("audio_random_speed", "copywriting", "speed_min"))
                input_audio_random_speed_copywriting_speed_max = ui.input(label='速度上限', value=config.get("audio_random_speed", "copywriting", "speed_max"))

        with ui.card().style("margin:10px 0px"):
            ui.label('Live2D') 
            with ui.grid(columns=1):
                switch_live2d_enable = ui.switch('启用', value=config.get("live2d", "enable"))
            with ui.grid(columns=2):
                input_live2d_port = ui.input(label='端口', value=config.get("live2d", "port"))
                
        with ui.card().style("margin:10px 0px"):
            ui.label('定时任务')
            schedule_var = {}
            for index, schedule in enumerate(config.get("schedule")):
                with ui.grid(columns=3):
                    schedule_var[str(3 * index)] = ui.switch(text=f"启用任务{index}", value=schedule["enable"])
                    schedule_var[str(3 * index + 1)] = ui.input(label="循环周期", value=schedule["time"], placeholder='定时任务循环的周期时长（秒），即每间隔这个周期就会执行一次')
                    schedule_var[str(3 * index + 2)] = ui.textarea(label="文案列表", value=textarea_data_change(schedule["copy"]), placeholder='存放文案的列表，通过空格或换行分割，通过{变量}来替换关键数据，可修改源码自定义功能')

        with ui.card().style("margin:10px 0px"):
            ui.label('按键映射')
            with ui.grid(columns=2):
                switch_key_mapping_enable = ui.switch('启用', value=config.get("key_mapping", "enable"))
                input_key_mapping_start_cmd = ui.input(label='命令前缀', value=config.get("key_mapping", "start_cmd"), placeholder='想要触发此功能必须以这个字符串做为命令起始，不然将不会被解析为按键映射命令')
            key_mapping_config_var = {}
            for index, key_mapping_config in enumerate(config.get("key_mapping", "config")):
                with ui.grid(columns=3):
                    key_mapping_config_var[str(3 * index)] = ui.textarea(label="关键词", value=textarea_data_change(key_mapping_config["keywords"]), placeholder='此处输入触发的关键词')
                    key_mapping_config_var[str(3 * index + 1)] = ui.textarea(label="按键", value=textarea_data_change(key_mapping_config["keys"]), placeholder='此处输入你要映射的按键，以+号拼接（按键名参考pyautogui规则）')
                    key_mapping_config_var[str(3 * index + 2)] = ui.input(label="相似度", value=key_mapping_config["similarity"], placeholder='关键词与用户输入的相似度，默认1即100%')
    
    with ui.tab_panel(llm_page):
        with ui.card().style("margin:10px 0px"):
            ui.label("ChatGPT/闻达")
            with ui.grid(columns=2):
                input_openai_api = ui.input(label='API地址', placeholder='API请求地址，支持代理', value=config.get("openai", "api"))
                textarea_openai_api_key = ui.textarea(label='API密钥', placeholder='API KEY，支持代理', value=textarea_data_change(config.get("openai", "api_key")))
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
                input_chatgpt_temperature = ui.input(label='温度', placeholder='控制生成文本的随机性。较高的温度值会使生成的文本更随机和多样化，而较低的温度值会使生成的文本更加确定和一致。', value=config.get("chatgpt", "temperature"))
            with ui.grid(columns=2):
                input_chatgpt_max_tokens = ui.input(label='最大令牌数', placeholder='限制生成回答的最大长度。', value=config.get("chatgpt", "max_tokens"))
                input_chatgpt_top_p = ui.input(label='前p个选择', placeholder='Nucleus采样。这个参数控制模型从累积概率大于一定阈值的令牌中进行采样。较高的值会产生更多的多样性，较低的值会产生更少但更确定的回答。', value=config.get("chatgpt", "top_p"))
            with ui.grid(columns=2):
                input_chatgpt_presence_penalty = ui.input(label='存在惩罚', placeholder='控制模型生成回答时对给定问题提示的关注程度。较高的存在惩罚值会减少模型对给定提示的重复程度，鼓励模型更自主地生成回答。', value=config.get("chatgpt", "presence_penalty"))
                input_chatgpt_frequency_penalty = ui.input(label='存在惩罚', placeholder='控制生成回答时对已经出现过的令牌的惩罚程度。较高的频率惩罚值会减少模型生成已经频繁出现的令牌，以避免重复和过度使用特定词语。', value=config.get("chatgpt", "frequency_penalty"))
            with ui.grid(columns=2):
                input_chatgpt_preset = ui.input(label='预设', placeholder='用于指定一组预定义的设置，以便模型更好地适应特定的对话场景。', value=config.get("chatgpt", "preset"))
                input_chatgpt_preset.style("width:400px") 
        with ui.card().style("margin:10px 0px"):
            ui.label("Claude")
            with ui.grid(columns=2):
                input_claude_slack_user_token = ui.input(label='slack_user_token', placeholder='Slack平台配置的用户Token，参考文档的Claude板块进行配置', value=config.get("claude", "slack_user_token"))
                input_claude_slack_user_token.style("width:400px")
                input_claude_bot_user_id = ui.input(label='bot_user_id', placeholder='Slack平台添加的Claude显示的成员ID，参考文档的Claude板块进行配置', value=config.get("claude", "bot_user_id"))
                input_claude_slack_user_token.style("width:400px") 
        with ui.card().style("margin:10px 0px"):
            ui.label("Claude2")
            with ui.grid(columns=2):
                input_claude2_cookie = ui.input(label='cookie', placeholder='claude.ai官网，打开F12，随便提问抓个包，请求头cookie配置于此', value=config.get("claude2", "cookie"))
                input_claude2_cookie.style("width:400px")
                switch_claude2_use_proxy = ui.switch('启用代理', value=config.get("claude2", "use_proxy"))
            with ui.grid(columns=2):
                input_claude2_proxies_http = ui.input(label='proxies_http', placeholder='http代理地址，默认为 http://127.0.0.1:10809', value=config.get("claude2", "proxies", "http"))
                input_claude2_proxies_http.style("width:400px") 
                input_claude2_proxies_https = ui.input(label='proxies_https', placeholder='https代理地址，默认为 http://127.0.0.1:10809', value=config.get("claude2", "proxies", "https"))
                input_claude2_proxies_https.style("width:400px")
            with ui.grid(columns=2):
                input_claude2_proxies_socks5 = ui.input(label='proxies_socks5', placeholder='socks5代理地址，默认为 socks://127.0.0.1:10808', value=config.get("claude2", "proxies", "socks5"))
                input_claude2_proxies_socks5.style("width:400px") 
        with ui.card().style("margin:10px 0px"):
            ui.label("ChatGLM")
            with ui.grid(columns=2):
                input_chatglm_api_ip_port = ui.input(label='API地址', placeholder='ChatGLM的API版本运行后的服务链接（需要完整的URL）', value=config.get("chatglm", "api_ip_port"))
                input_chatglm_api_ip_port.style("width:400px")
                input_chatglm_max_length = ui.input(label='最大长度限制', placeholder='生成回答的最大长度限制，以令牌数或字符数为单位。', value=config.get("chatglm", "max_length"))
                input_chatglm_max_length.style("width:400px")
            with ui.grid(columns=2):
                input_chatglm_top_p = ui.input(label='前p个选择', placeholder='也称为 Nucleus采样。控制模型生成时选择概率的阈值范围。', value=config.get("chatglm", "top_p"))
                input_chatglm_top_p.style("width:400px")
                input_chatglm_temperature = ui.input(label='前p个选择', placeholder='温度参数，控制生成文本的随机性。较高的温度值会产生更多的随机性和多样性。', value=config.get("chatglm", "temperature"))
                input_chatglm_temperature.style("width:400px")
            with ui.grid(columns=2):
                switch_chatglm_history_enable = ui.switch('上下文记忆', value=config.get("chatglm", "history_enable"))
                input_chatglm_history_max_len = ui.input(label='最大记忆长度', placeholder='最大记忆的上下文字符数量，不建议设置过大，容易爆显存，自行根据情况配置', value=config.get("chatglm", "history_max_len"))
                input_chatglm_history_max_len.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("chat_with_file")
            with ui.grid(columns=2):
                lines = ["claude", "openai_gpt", "openai_vector_search"]
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_chat_with_file_chat_mode = ui.select(
                    label='聊天模式', 
                    options=data_json, 
                    value=config.get("chat_with_file", "chat_mode")
                )
                input_chat_with_file_data_path = ui.input(label='数据文件路径', placeholder='加载的本地zip数据文件路径（到x.zip）, 如：./data/伊卡洛斯百度百科.zip', value=config.get("chat_with_file", "data_path"))
                input_chat_with_file_data_path.style("width:400px")
            with ui.grid(columns=2):
                input_chat_with_file_separator = ui.input(label='分隔符', placeholder='拆分文本的分隔符，这里使用 换行符 作为分隔符。', value=config.get("chat_with_file", "separator"))
                input_chat_with_file_separator.style("width:400px")
                input_chat_with_file_chunk_size = ui.input(label='块大小', placeholder='每个文本块的最大字符数(文本块字符越多，消耗token越多，回复越详细)', value=config.get("chat_with_file", "chunk_size"))
                input_chat_with_file_chunk_size.style("width:400px")
            with ui.grid(columns=2):
                input_chat_with_file_chunk_overlap = ui.input(label='块重叠', placeholder='两个相邻文本块之间的重叠字符数。这种重叠可以帮助保持文本的连贯性，特别是当文本被用于训练语言模型或其他需要上下文信息的机器学习模型时', value=config.get("chat_with_file", "chunk_overlap"))
                input_chat_with_file_chunk_overlap.style("width:400px")
                lines = ["sebastian-hofstaetter/distilbert-dot-tas_b-b256-msmarco", "GanymedeNil/text2vec-large-chinese"]
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_chat_with_file_local_vector_embedding_model = ui.select(
                    label='模型', 
                    options=data_json, 
                    value=config.get("chat_with_file", "local_vector_embedding_model")
                )
            with ui.grid(columns=2):
                input_chat_with_file_chain_type = ui.input(label='链类型', placeholder='指定要生成的语言链的类型，例如：stuff', value=config.get("chat_with_file", "chain_type"))
                input_chat_with_file_chain_type.style("width:400px")
                input_chat_with_file_question_prompt = ui.input(label='问题总结提示词', placeholder='通过LLM总结本地向量数据库输出内容，此处填写总结用提示词', value=config.get("chat_with_file", "question_prompt"))
                input_chat_with_file_question_prompt.style("width:400px")
            with ui.grid(columns=2):
                input_chat_with_file_local_max_query = ui.input(label='最大查询数据库次数', placeholder='最大查询数据库次数。限制次数有助于节省token', value=config.get("chat_with_file", "local_max_query"))
                input_chat_with_file_local_max_query.style("width:400px")
                switch_chat_with_file_show_token_cost = ui.switch('显示成本', value=config.get("chat_with_file", "show_token_cost"))
        with ui.card().style("margin:10px 0px"):
            ui.label("Chatterbot")
            with ui.grid(columns=2):
                input_chatterbot_name = ui.input(label='bot名称', placeholder='bot名称', value=config.get("chatterbot", "name"))
                input_chatterbot_name.style("width:400px")
                input_chatterbot_db_path = ui.input(label='数据库路径', placeholder='数据库路径（绝对或相对路径）', value=config.get("chatterbot", "db_path"))
                input_chatterbot_db_path.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("text_generation_webui")
            with ui.grid(columns=2):
                input_text_generation_webui_api_ip_port = ui.input(label='API地址', placeholder='text-generation-webui开启API模式后监听的IP和端口地址', value=config.get("text_generation_webui", "api_ip_port"))
                input_text_generation_webui_api_ip_port.style("width:400px")
                input_text_generation_webui_max_new_tokens = ui.input(label='max_new_tokens', placeholder='自行查阅', value=config.get("text_generation_webui", "max_new_tokens"))
                input_text_generation_webui_max_new_tokens.style("width:400px")
            with ui.grid(columns=2):
                input_text_generation_webui_mode = ui.input(label='模式', placeholder='自行查阅', value=config.get("text_generation_webui", "mode"))
                input_text_generation_webui_mode.style("width:400px")
                input_text_generation_webui_character = ui.input(label='character', placeholder='自行查阅', value=config.get("text_generation_webui", "character"))
                input_text_generation_webui_character.style("width:400px")
            with ui.grid(columns=2):
                input_text_generation_webui_instruction_template = ui.input(label='API地址', placeholder='自行查阅', value=config.get("text_generation_webui", "instruction_template"))
                input_text_generation_webui_instruction_template.style("width:400px")
                input_text_generation_webui_your_name = ui.input(label='your_name', placeholder='自行查阅', value=config.get("text_generation_webui", "your_name"))
                input_text_generation_webui_your_name.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("讯飞星火")
            with ui.grid(columns=2):
                lines = ["web", "api"]
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_sparkdesk_type = ui.select(
                    label='类型', 
                    options=data_json, 
                    value=config.get("sparkdesk", "type")
                )
                input_sparkdesk_cookie = ui.input(label='cookie', placeholder='web抓包请求头中的cookie，参考文档教程', value=config.get("sparkdesk", "cookie"))
                input_sparkdesk_cookie.style("width:400px")
            with ui.grid(columns=2):
                input_sparkdesk_fd = ui.input(label='fd', placeholder='web抓包负载中的fd，参考文档教程', value=config.get("sparkdesk", "fd"))
                input_sparkdesk_fd.style("width:400px")      
                input_sparkdesk_GtToken = ui.input(label='GtToken', placeholder='web抓包负载中的GtToken，参考文档教程', value=config.get("sparkdesk", "GtToken"))
                input_sparkdesk_GtToken.style("width:400px")
            with ui.grid(columns=2):
                input_sparkdesk_app_id = ui.input(label='app_id', placeholder='申请官方API后，云平台中提供的APPID', value=config.get("sparkdesk", "app_id"))
                input_sparkdesk_app_id.style("width:400px")      
                input_sparkdesk_api_secret = ui.input(label='api_secret', placeholder='申请官方API后，云平台中提供的APISecret', value=config.get("sparkdesk", "api_secret"))
                input_sparkdesk_api_secret.style("width:400px") 
            with ui.grid(columns=2):
                input_sparkdesk_api_key = ui.input(label='api_key', placeholder='申请官方API后，云平台中提供的APIKey', value=config.get("sparkdesk", "api_key"))
                input_sparkdesk_api_key.style("width:400px") 
        with ui.card().style("margin:10px 0px"):
            ui.label("Langchain_ChatGLM")
            with ui.grid(columns=2):
                input_langchain_chatglm_api_ip_port = ui.input(label='API地址', placeholder='langchain_chatglm的API版本运行后的服务链接（需要完整的URL）', value=config.get("langchain_chatglm", "api_ip_port"))
                input_langchain_chatglm_api_ip_port.style("width:400px")
                lines = ["模型", "知识库", "必应"]
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_langchain_chatglm_chat_type = ui.select(
                    label='类型', 
                    options=data_json, 
                    value=config.get("langchain_chatglm", "chat_type")
                )
            with ui.grid(columns=2):
                input_langchain_chatglm_knowledge_base_id = ui.input(label='知识库名称', placeholder='本地存在的知识库名称，日志也有输出知识库列表，可以查看', value=config.get("langchain_chatglm", "knowledge_base_id"))
                input_langchain_chatglm_knowledge_base_id.style("width:400px")
                switch_langchain_chatglm_history_enable = ui.switch('显示成本', value=config.get("langchain_chatglm", "history_enable"))
            with ui.grid(columns=2):
                input_langchain_chatglm_history_max_len = ui.input(label='最大记忆长度', placeholder='最大记忆的上下文字符数量，不建议设置过大，容易爆显存，自行根据情况配置', value=config.get("langchain_chatglm", "history_max_len"))
                input_langchain_chatglm_history_max_len.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("智谱AI")
            with ui.grid(columns=2):
                input_zhipu_api_key = ui.input(label='api key', placeholder='具体参考官方文档，申请地址：https://open.bigmodel.cn/usercenter/apikeys', value=config.get("zhipu", "api_key"))
                input_zhipu_api_key.style("width:400px")
                lines = ['chatglm_pro', 'chatglm_std', 'chatglm_lite', 'characterglm']
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_zhipu_model = ui.select(
                    label='模型', 
                    options=data_json, 
                    value=config.get("zhipu", "model")
                )
            with ui.grid(columns=2):
                input_zhipu_top_p = ui.input(label='top_p', placeholder='用温度取样的另一种方法，称为核取样\n取值范围是：(0.0,1.0)；开区间，不能等于 0 或 1，默认值为 0.7\n模型考虑具有 top_p 概率质量的令牌的结果。所以 0.1 意味着模型解码器只考虑从前 10% 的概率的候选集中取tokens\n建议您根据应用场景调整 top_p 或 temperature 参数，但不要同时调整两个参数', value=config.get("zhipu", "top_p"))
                input_zhipu_top_p.style("width:400px")
                input_zhipu_temperature = ui.input(label='temperature', placeholder='采样温度，控制输出的随机性，必须为正数\n取值范围是：(0.0,1.0]，不能等于 0,默认值为 0.95\n值越大，会使输出更随机，更具创造性；值越小，输出会更加稳定或确定\n建议您根据应用场景调整 top_p 或 temperature 参数，但不要同时调整两个参数', value=config.get("zhipu", "temperature"))
                input_zhipu_temperature.style("width:400px")
            with ui.grid(columns=2):
                switch_zhipu_history_enable = ui.switch('上下文记忆', value=config.get("zhipu", "history_enable"))
                input_zhipu_history_max_len = ui.input(label='最大记忆长度', placeholder='最长能记忆的问答字符串长度，超长会丢弃最早记忆的内容，请慎用！配置过大可能会有丢大米', value=config.get("zhipu", "history_max_len"))
                input_zhipu_history_max_len.style("width:400px")
            with ui.grid(columns=2):
                input_zhipu_user_info = ui.input(label='用户信息', placeholder='用户信息，当使用characterglm时需要配置', value=config.get("zhipu", "user_info"))
                input_zhipu_user_info.style("width:400px")
                input_zhipu_bot_info = ui.input(label='角色信息', placeholder='角色信息，当使用characterglm时需要配置', value=config.get("zhipu", "bot_info"))
                input_zhipu_bot_info.style("width:400px")
            with ui.grid(columns=2):
                input_zhipu_bot_name = ui.input(label='角色名称', placeholder='角色名称，当使用characterglm时需要配置', value=config.get("zhipu", "bot_name"))
                input_zhipu_bot_name.style("width:400px")
                input_zhipu_user_name = ui.input(label='用户名称', placeholder='用户名称，默认值为用户，当使用characterglm时需要配置', value=config.get("zhipu", "user_name"))
                input_zhipu_user_name.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("Bard")
            with ui.grid(columns=2):
                input_bard_token = ui.input(label='token', placeholder='登录bard，打开F12，在cookie中获取 __Secure-1PSID 对应的值', value=config.get("bard", "token"))
                input_bard_token.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("文心一言")
            with ui.grid(columns=2):
                input_yiyan_api_ip_port = ui.input(label='API地址', placeholder='yiyan-api启动后监听的ip端口地址', value=config.get("yiyan", "api_ip_port"))
                input_yiyan_api_ip_port.style("width:400px")
                lines = ['web']
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_yiyan_type = ui.select(
                    label='模型', 
                    options=data_json, 
                    value=config.get("yiyan", "type")
                )
            with ui.grid(columns=2):
                input_yiyan_cookie = ui.input(label='cookie', placeholder='文心一言登录后，跳过debug后，抓取请求包中的cookie', value=config.get("yiyan", "cookie"))
                input_yiyan_cookie.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("通义千问")
            with ui.grid(columns=2):
                lines = ['web']
                data_json = {}
                for line in lines:
                    data_json[line] = line
                select_tongyi_type = ui.select(
                    label='模型', 
                    options=data_json, 
                    value=config.get("tongyi", "type")
                )
                input_tongyi_cookie_path = ui.input(label='cookie路径', placeholder='通义千问登录后，通过浏览器插件Cookie Editor获取Cookie JSON串，然后将数据保存在这个路径的文件中', value=config.get("tongyi", "cookie_path"))
                input_tongyi_cookie_path.style("width:400px")
    with ui.tab_panel(tts_page):
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
            ui.label("elevenlabs")
            with ui.grid(columns=2):
                input_elevenlabs_api_key = ui.input(label='api密钥', placeholder='elevenlabs密钥，可以不填，默认也有一定额度的免费使用权限，具体多少不知道', value=config.get("elevenlabs", "api_key"))
            with ui.grid(columns=2):
                input_elevenlabs_voice = ui.input(label='说话人', placeholder='选择的说话人名', value=config.get("elevenlabs", "voice"))
            with ui.grid(columns=2):
                input_elevenlabs_model = ui.input(label='模型', placeholder='选择的模型', value=config.get("elevenlabs", "model"))
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
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
        with ui.card().style("margin:10px 0px"):
            ui.label("DDSP-SVC")
            with ui.grid(columns=2):
                switch_ddsp_svc_enable = ui.switch('启用', value=config.get("ddsp_svc", "enable"))
                input_ddsp_svc_config_path = ui.input(label='配置文件路径', placeholder='模型配置文件config.yaml的路径(此处可以不配置，暂时没有用到)', value=config.get("ddsp_svc", "config_path"))
                input_ddsp_svc_config_path.style("width:400px")
            with ui.grid(columns=2):
                input_ddsp_svc_api_ip_port = ui.input(label='API地址', placeholder='flask_api服务运行的ip端口，例如：http://127.0.0.1:6844', value=config.get("ddsp_svc", "api_ip_port"))
                input_ddsp_svc_api_ip_port.style("width:400px")
                input_ddsp_svc_fSafePrefixPadLength = ui.input(label='安全前缀填充长度', placeholder='安全前缀填充长度，不知道干啥用，默认为0', value=config.get("ddsp_svc", "fSafePrefixPadLength"))
                input_ddsp_svc_fSafePrefixPadLength.style("width:400px")
            with ui.grid(columns=2):
                input_ddsp_svc_fPitchChange = ui.input(label='变调', placeholder='音调设置，默认为0', value=config.get("ddsp_svc", "fPitchChange"))
                input_ddsp_svc_fPitchChange.style("width:400px")
                input_ddsp_svc_sSpeakId = ui.input(label='说话人ID', placeholder='说话人ID，需要和模型数据对应，默认为0', value=config.get("ddsp_svc", "sSpeakId"))
                input_ddsp_svc_sSpeakId.style("width:400px")
            with ui.grid(columns=2):
                input_ddsp_svc_sampleRate = ui.input(label='采样率', placeholder='DAW所需的采样率，默认为44100', value=config.get("ddsp_svc", "sampleRate"))
                input_ddsp_svc_sampleRate.style("width:400px")
        with ui.card().style("margin:10px 0px"):
            ui.label("SO-VITS-SVC")
            with ui.grid(columns=2):
                switch_so_vits_svc_enable = ui.switch('启用', value=config.get("so_vits_svc", "enable"))
                input_so_vits_svc_config_path = ui.input(label='配置文件路径', placeholder='模型配置文件config.json的路径', value=config.get("so_vits_svc", "config_path"))
                input_so_vits_svc_config_path.style("width:400px")
            with ui.grid(columns=2):
                input_so_vits_svc_api_ip_port = ui.input(label='API地址', placeholder='flask_api_full_song服务运行的ip端口，例如：http://127.0.0.1:1145', value=config.get("so_vits_svc", "api_ip_port"))
                input_so_vits_svc_api_ip_port.style("width:400px")
                input_so_vits_svc_spk = ui.input(label='说话人', placeholder='说话人，需要和配置文件内容对应', value=config.get("so_vits_svc", "spk"))
                input_so_vits_svc_spk.style("width:400px") 
            with ui.grid(columns=2):
                input_so_vits_svc_tran = ui.input(label='音调', placeholder='音调设置，默认为1', value=config.get("so_vits_svc", "tran"))
                input_so_vits_svc_tran.style("width:400px")
                input_so_vits_svc_wav_format = ui.input(label='输出音频格式', placeholder='音频合成后输出的格式', value=config.get("so_vits_svc", "wav_format"))
                input_so_vits_svc_wav_format.style("width:400px") 
    with ui.tab_panel(copywriting_page):
        ui.label('待完善')

    with ui.tab_panel(docs_page):
        ui.label('在线文档：')
        ui.link('https://luna.docs.ie.cx/', 'https://luna.docs.ie.cx/', new_tab=True)
    with ui.tab_panel(about_page):
        ui.label('webui采用nicegui框架搭建，目前还在施工中，部分功能可以使用。敬请期待。')

with ui.grid(columns=3):
    save_button = ui.button('保存配置', on_click=lambda: save_config())
    run_button = ui.button('一键运行', on_click=lambda: run_external_program())
    # 创建一个按钮，用于停止正在运行的程序
    stop_button = ui.button("停止运行", on_click=lambda: stop_external_program())
    # stop_button.enabled = False  # 初始状态下停止按钮禁用

ui.run()