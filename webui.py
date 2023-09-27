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

    def common_textEdit_handle(content):
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
    except Exception as e:
        logging.error(f"无法写入配置文件！\n{e}")

    return True

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
    run_page = ui.tab('运行')
    common_config_page = ui.tab('通用配置')
    llm_page = ui.tab('大语言模型')
    tts_page = ui.tab('文本转语音')
    svc_page = ui.tab('变声')
    copywriting_page = ui.tab('文案')
    docs_page = ui.tab('文档')
    about_page = ui.tab('关于')

with ui.tab_panels(tabs, value=run_page).classes('w-full'):
    with ui.tab_panel(run_page):
        save_button = ui.button('保存配置', on_click=lambda: save_config())
        run_button = ui.button('一键运行', on_click=lambda: run_external_program())
        # 创建一个按钮，用于停止正在运行的程序
        stop_button = ui.button("停止运行", on_click=lambda: stop_external_program())
        # stop_button.enabled = False  # 初始状态下停止按钮禁用
    with ui.tab_panel(common_config_page):
        with ui.grid(columns=2):
            ui.label('待完善')
            select_platform = ui.select({'talk': '聊天模式', 'bilibli': '哔哩哔哩', 'dy': '抖音', 'ks': '快手', 'douyu': '斗鱼'}, value=config.get("platform"))
    with ui.tab_panel(llm_page):
        ui.label('待完善')
    with ui.tab_panel(tts_page):
        ui.label('待完善')
    with ui.tab_panel(svc_page):
        ui.label('待完善')
    with ui.tab_panel(copywriting_page):
        ui.label('待完善')
    with ui.tab_panel(docs_page):
        ui.label('待完善')
    with ui.tab_panel(about_page):
        ui.label('待完善')

ui.run()