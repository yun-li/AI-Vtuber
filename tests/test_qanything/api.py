import json, logging
import requests
from urllib.parse import urljoin

# from utils.common import Common
# from utils.logger import Configure_logger


class QAnything:
    def __init__(self, data):
        # self.common = Common()
        # 日志文件路径
        # file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        # Configure_logger(file_path)

        self.api_ip_port = data["api_ip_port"]
        self.config_data = data

        self.history = []


    # 获取知识库列表
    def get_list_knowledge_base(self):
        url = urljoin(self.api_ip_port, "/api/local_doc_qa/list_knowledge_base")
        try:
            response = requests.post(url, json={"user_id": self.config_data["user_id"]})
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = json.loads(result)

            logging.debug(ret)
            logging.info(f"本地知识库列表：{ret['data']}")

            return ret['data']
        except Exception as e:
            logging.error(e)
            return None


    def get_resp(self, data):
        """请求对应接口，获取返回值

        Args:
            data (dict): json数据

        Returns:
            str: 返回的文本回答
        """
        try:
            url = self.api_ip_port + "/api/local_doc_qa/local_doc_chat"

            data_json = {
                "user_id": self.config_data["user_id"], 
                "kb_ids": self.config_data["kb_ids"], 
                "question": data["prompt"], 
                "history": self.history
            }

            response = requests.post(url=url, json=data_json)
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = json.loads(result)

            logging.info(ret)

            resp_content = ret["response"]

            # 启用历史就给我记住！
            if self.config_data["history_enable"]:
                self.history = ret["history"]

                while True:
                    # 计算所有字符数
                    total_chars = sum(len(item) for sublist in self.history for item in sublist)

                    # 如果大于限定最大历史数，就剔除第一个元素
                    if total_chars > self.config_data["history_max_len"]:
                        self.history.pop(0)
                    else:
                        break

            return resp_content
        except Exception as e:
            logging.error(e)
            return None


if __name__ == '__main__':
    # 配置日志输出格式
    logging.basicConfig(
        level=logging.DEBUG,  # 设置日志级别，可以根据需求调整
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    data = {
        "api_ip_port": "http://127.0.0.1:8777",
        "user_id": "zzp",
        "kb_ids": ["KB2435554f1fb348ad84a1eb60eaa1c466"],
        "history_enable": True,
        "history_max_len": 300
    }
    qanything = QAnything(data)


    qanything.get_list_knowledge_base()
    logging.info(qanything.get_resp({"prompt": "伊卡洛斯和妮姆芙的关系"}))
    logging.info(qanything.get_resp({"prompt": "伊卡洛斯的英文名"}))
    