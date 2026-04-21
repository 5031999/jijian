import requests
import json

# 父类：统一实现调用逻辑
class BaseModelClient:
    API_KEY = ""
    API_URL = ""

    def chat(self, query, user="user-001", conversation_id=""):
        if not self.API_KEY or not self.API_URL:
            raise Exception("必须配置 API_KEY 和 API_URL")

        headers = {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user
        }

        response = requests.post(self.API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result.get("answer", "")
        else:
            raise Exception(f"请求失败：{response.status_code}，{response.text}")


# ==============================================
# 五个子类，每个对应一个 API_KEY
# ==============================================

class ModelClient1(BaseModelClient):
    API_KEY = "app-wGqov8mdIsjuePLcoo8UOHAV"
    API_URL = "http://43.132.210.224/v1/chat-messages"

class ModelClient2(BaseModelClient):
    API_KEY = "app-wGqov8mdIsjuePLcoo8UOHAV"
    API_URL = "http://43.132.210.224/v1/chat-messages"

class ModelClient3(BaseModelClient):
    API_KEY = "app-wGqov8mdIsjuePLcoo8UOHAV"
    API_URL = "http://43.132.210.224/v1/chat-messages"

class ModelClient4(BaseModelClient):
    API_KEY = "app-wGqov8mdIsjuePLcoo8UOHAV"
    API_URL = "http://43.132.210.224/v1/chat-messages"

class ModelClient5(BaseModelClient):
    API_KEY = "app-wGqov8mdIsjuePLcoo8UOHAV"
    API_URL = "http://43.132.210.224/v1/chat-messages"



# # 使用第1个key
# client1 = ModelClient1()
# answer1 = client1.chat("你是谁")
# print(answer1)
#
# # 使用第3个key
# client3 = ModelClient3()
# answer3 = client3.chat("写一段Python代码")
# print(answer3)