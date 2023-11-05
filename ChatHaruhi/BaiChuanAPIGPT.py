import os
import json
import time
import hashlib
import requests

from .BaseLLM import BaseLLM

BAICHUAN_API_AK = os.getenv("BAICHUAN_API_AK")
BAICHUAN_API_SK = os.getenv("BAICHUAN_API_SK")

def sign(secret_key, data):
    json_data = json.dumps(data)
    time_stamp = int(time.time())
    input_string = secret_key + json_data + str(time_stamp)
    md5 = hashlib.md5()
    md5.update(input_string.encode('utf-8'))
    encrypted = md5.hexdigest()
    return encrypted

def do_request(messages, api_key, secret_key):
    url = "https://api.baichuan-ai.com/v1/chat"

    data = {
        "model": "Baichuan2-53B",
        "messages": messages
    }

    signature = sign(secret_key, data)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
        "X-BC-Request-Id": "your requestId",
        "X-BC-Timestamp": str(int(time.time())),
        "X-BC-Signature": signature,
        "X-BC-Sign-Algo": "MD5",
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

class BaiChuanAPIGPT(BaseLLM):
    def __init__(self, model="baichuan-api", api_key=None, secret_key=None, verbose=False):
        super(BaiChuanAPIGPT, self).__init__()
        self.api_key = api_key or BAICHUAN_API_AK
        self.secret_key = secret_key or BAICHUAN_API_SK
        self.verbose = verbose
        self.model_name = model
        self.prompts = []
        if self.verbose:
            print('model name, ', self.model_name)
            if self.api_key is None or self.secret_key is None:
                print('Please set BAICHUAN_API_AK and BAICHUAN_API_SK')

    def initialize_message(self):
        self.prompts = []

    def ai_message(self, payload):
        self.prompts.append({"role":"assistant","content":payload})

    def system_message(self, payload):
        self.prompts.append({"role":"user","content":payload})

    def user_message(self, payload):
        self.prompts.append({"role":"user","content":payload})

    def get_response(self):
        max_try = 5
        sleep_interval = 3

        for i in range(max_try):
            response = do_request(self.prompts, self.api_key, self.secret_key)
            if response is not None:
                if self.verbose:
                    print('Get Baichuan API response success')
                messages = response['data']['messages']
                if len(messages) > 0:
                    return messages[-1]['content'].strip("\"'")
            else:
                if self.verbose:
                    print('Get Baichuan API response failed, retrying...')
                time.sleep(sleep_interval)
            
    def print_prompt(self):
        for message in self.prompts:
            print(f"{message['role']}: {message['content']}")
            