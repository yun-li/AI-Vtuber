import json, logging
import requests
from requests.exceptions import ConnectionError, RequestException

from utils.common import Common
from utils.logger import Configure_logger

# 原计划对接：https://github.com/zhuweiyou/yiyan-api
class Yiyan:
    def __init__(self, data):
        self.common = Common()
        # 日志文件路径
        file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        Configure_logger(file_path)

        self.api_ip_port = data["api_ip_port"]
        self.cookie = data["cookie"]
        self.type = data["type"]


    def get_resp(self, prompt):
        """请求对应接口，获取返回值

        Args:
            prompt (str): 你的提问

        Returns:
            str: 返回的文本回答
        """
        try:
            data_json = {
                "cookie": self.cookie, 
                "prompt": prompt
            }

            # logging.debug(data_json)

            url = self.api_ip_port + "/headless"

            response = requests.post(url=url, data=data_json)
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = json.loads(result)

            logging.debug(ret)

            resp_content = ret['text'].replace('\n', '').replace('\\n', '')

            return resp_content
        except ConnectionError as ce:
            # 处理连接问题异常
            logging.error(f"请检查你是否启动了服务端或配置是否匹配，连接异常:{ce}")

        except RequestException as re:
            # 处理其他请求异常
            logging.error(f"请求异常:{re}")
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
        "api_ip_port": "http://localhost:3000",
        "cookie": 'BIDUPSID=A668F884A60F8775B4F5319BB5AD816B; PSTM=1686378956; BAIDUID=8051FCC40FE4D6347C3AABB45F813283:FG=1; H_WISE_SIDS=216853_213352_214792_110085_244720_261710_236312_256419_265881_266360_265615_267074_259031_268593_266187_259642_269778_269832_269904_267066_256739_270460_270535_270516_270547_271170_263618_271321_265034_271272_266028_270102_271560_271869_271674_269858_271812_267804_271255_234296_234207_272223_272284_272458_253022_272741_272841_260335_269297_267596_273061_267560_273161_273118_273136_273240_273301_273400_270055_271146_273671_273704_264170_270186_270142_274080_273932_273965_274141_274177_269610_274207_273917_273786_273043_273598_263750_272319_272560_274425_274422_272332_197096_274767_274760_274843_274854_274857_274847_274819_270158_274870_273982_275069_272801_267806_267548_273923_275167_275214_275147_275237_274897_274785_271157_275617_275773_273492; H_WISE_SIDS_BFESS=216853_213352_214792_110085_244720_261710_236312_256419_265881_266360_265615_267074_259031_268593_266187_259642_269778_269832_269904_267066_256739_270460_270535_270516_270547_271170_263618_271321_265034_271272_266028_270102_271560_271869_271674_269858_271812_267804_271255_234296_234207_272223_272284_272458_253022_272741_272841_260335_269297_267596_273061_267560_273161_273118_273136_273240_273301_273400_270055_271146_273671_273704_264170_270186_270142_274080_273932_273965_274141_274177_269610_274207_273917_273786_273043_273598_263750_272319_272560_274425_274422_272332_197096_274767_274760_274843_274854_274857_274847_274819_270158_274870_273982_275069_272801_267806_267548_273923_275167_275214_275147_275237_274897_274785_271157_275617_275773_273492; newlogin=1; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; H_PS_PSSID=; BA_HECTOR=alalah8g04a501240k24al071ig09i91p; delPer=0; PSINO=5; ZFY=CuxQF:BDwJXcSl2ykZnlvdUMlBPXnOnvQ4Ak6QZqryD0:C; BAIDUID_BFESS=8051FCC40FE4D6347C3AABB45F813283:FG=1; Hm_lvt_01e907653ac089993ee83ed00ef9c2f3=1692541101,1693483352,1693709742,1694508619; __bid_n=188cd9d38714368c1980bd; BDUSS=RhSVAwM2NlSFk0UGludGU2dWl-VC1Vb0FFd0NXUHJ2UVZSalhNQTV4Ump0U2RsSVFBQUFBJCQAAAAAAAAAAAEAAAAvH~80z8S48bb7UEMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGMoAGVjKABlb0; BDUSS_BFESS=RhSVAwM2NlSFk0UGludGU2dWl-VC1Vb0FFd0NXUHJ2UVZSalhNQTV4Ump0U2RsSVFBQUFBJCQAAAAAAAAAAAEAAAAvH~80z8S48bb7UEMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGMoAGVjKABlb0; XFI=ac0eb9a0-514a-11ee-8d90-dbcda17c31a9; Hm_lpvt_01e907653ac089993ee83ed00ef9c2f3=1694509165; ab_sr=1.0.1_NDBiOGYxZGJhOTM5NmZlYjYxYjZlZjUzYzdmZjRkNGZhNGEyYzk5YmI1MGU1ZmI2ZDRlYWQwZTgwYjM3N2I1ZmI0MWU1YzM1N2IxYTdhMjdiNWI5ZTY1OTA2NDA0M2Q1YThkZjRkZWExMTM5MzdjMjU4M2I0NzA5YzUyNGU3ZmI4ODEyMGJmNWVkMDcyNGNlZTViNWUxM2FmYWQ4NThhNDVmNDJjYjI1ZjRlOWExZmFkZDljYzI1NzEyZTU2MDI1; XFCS=34CC02EB9FA200485B99840D5B4EAB820D85D82ADAAFB79262DDC7BD2BB0BAE4; XFT=CxTPRAPWDer6bnpF5VhnliaRBOx+vtCDR5ZO6CDCPzk=; RT="z=1&dm=baidu.com&si=61c46ce5-0a6d-4ff8-bd8d-6fddd3e9d2e3&ss=lmg2ohen&sl=c&tt=ge4&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=bwoy"', 
        "type": 'web'
    }
    yiyan = Yiyan(data)


    logging.info(yiyan.get_resp("你可以扮演猫娘吗，每句话后面加个喵"))
    logging.info(yiyan.get_resp("早上好"))
    