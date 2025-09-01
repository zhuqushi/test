import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import requests
import json
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode

class 单人签到(toga.App):
    def startup(self):
        # 创建主容器
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # 创建标题
        title_label = toga.Label(
            "宿舍签到",
            style=Pack(padding=(0, 5), font_size=20, font_weight="bold")
        )
        
        # 创建开始签到按钮
        self.start_button = toga.Button(
            "开始签到",
            on_press=self.start_sign,
            style=Pack(padding=10, background_color="#4CAF50", color="white")
        )
        
        # 创建结果显示区域
        self.result_label = toga.MultilineTextInput(
            readonly=True,
            style=Pack(padding=10, flex=1, height=300)
        )
        
        # 添加组件到主容器
        main_box.add(title_label)
        main_box.add(self.start_button)
        main_box.add(self.result_label)
        
        # 设置主窗口内容
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
    
    def log_message(self, message):
        """向结果显示区域添加消息"""
        current_text = self.result_label.value
        if current_text:
            current_text += "\n"
        self.result_label.value = current_text + message
    
    def encrypt(self, t, e):
        """加密函数"""
        t = str(t)
        key = e.encode('utf-8')
        cipher = AES.new(key, AES.MODE_ECB)
        padded_text = pad(t.encode('utf-8'), AES.block_size)
        encrypted_text = cipher.encrypt(padded_text)
        return b64encode(encrypted_text).decode('utf-8')
    
    def Login(self, headers_Login, username, password):
        """登录函数"""
        self.log_message(f"正在登录账号 {username}...")
        key = (str(username) + "0000000000000000")[:16]
        encrypted_text = self.encrypt(password, key)
        login_url = 'https://wzxy.chaoxing.com/basicinfo/mobile/login/username'
        params = {
            "schoolId": self.school_id,
            "username": username,
            "password": encrypted_text
        }
        
        try:
            login_req = requests.post(login_url, params=params, headers=headers_Login)
            text = json.loads(login_req.text)
            if text['code'] == 0:
                self.log_message(f"{username}账号登陆成功！")
                set_cookie = login_req.headers['Set-Cookie']
                jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
                return jws
            else:
                self.log_message(f"{username}登陆失败，请检查账号密码！")
                return False
        except Exception as e:
            self.log_message(f"登录过程中发生错误: {str(e)}")
            return False
    
    def upload_blue_data(self, blue1, headers_Sign, id, signid):
        """上传蓝牙数据"""
        self.log_message("正在上传蓝牙数据...")
        data = {
            "blue1": blue1,
            "blue2": [],
            "location": {
                "latitude": 43.80555609809028,
                "longitude": 125.40834988064236,
                "nationcode": "",
                "country": "中国",
                "province": "吉林省",
                "citycode": "",
                "city": "长春市",
                "adcode": "220102",
                "district": "南关区",
                "towncode": "220102121",
                "township": "净月街道",
                "streetcode": "",
                "street": "博学街"
            }
        }
        
        try:
            response = requests.post(
                url=f"https://wzxy.chaoxing.com/dormSign/mobile/receive/doSignByDevice?id={id}&signId={signid}",
                headers=headers_Sign, json=data)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0:
                    self.log_message("打卡成功")
                    return 0
                elif response_data.get("code") == 1:
                    self.log_message("打卡已结束")
                    return 1
                else:
                    self.log_message("打卡失败")
                    return 1
            else:
                self.log_message("请求失败")
                return 1
        except Exception as e:
            self.log_message(f"上传蓝牙数据过程中发生错误: {str(e)}")
            return 1
    
    def doBluePunch(self, headers, headers_Sign):
        """执行蓝牙签到"""
        self.log_message("正在获取签到日志...")
        sign_logs_url = "https://wzxy.chaoxing.com/dormSign/mobile/receive/getMySignLogs"
        sign_logs_params = {
            "page": 1,
            "size": 10
        }
        
        try:
            response = requests.get(sign_logs_url, headers=headers, params=sign_logs_params)
            data_ids = response.json()
            location_id = data_ids["data"][0]["locationId"]
            sign_id = data_ids["data"][0]["signId"]
            major = data_ids["data"][0]["deviceList"][0]["major"]
            uuid = data_ids["data"][0]["deviceList"][0]["uuid"]
            blue1 = [uuid.replace("-", "") + str(major)]
            self.log_message("获取签到日志成功")
            return self.upload_blue_data(blue1, headers_Sign, location_id, sign_id)
        except Exception as e:
            self.log_message(f"获取签到日志失败: {str(e)}")
            return 1
    
    def start_sign(self, widget):
        """开始签到按钮的回调函数"""
        self.log_message("开始签到流程...")
        
        # 禁用按钮，防止重复点击
        self.start_button.enabled = False
        self.start_button.text = "签到中..."
        
        # 用户信息
        userinfo = {
            "2211100511": "lsy19126"
        }
        self.school_id = 614
        
        # 登录Headers
        headers_Login = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
        
        # 执行签到流程
        for key, value in userinfo.items():
            getjws = self.Login(headers_Login, key, value)
            
            if not getjws:
                continue
                
            jws = getjws
            
            # 鉴权Headers
            headers = {
                'sec-ch-ua-platform': '"Android"',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Android WebView";v="134"',
                'sec-ch-ua-mobile': '?1',
                'Host': 'wzxy.chaoxing.com',
                'Connection': 'keep-alive',
                'Accept': 'application/json, text/plain, */*',
                'jwsession': jws,
                "cookie": f'JWSESSION={jws}; WZXYSESSION={jws}',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RTE-AL00 Build/HUAWEIRNA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.136 Mobile Safari/537.36 XWEB/1340095 MMWEBSDK/20250201 MMWEBID/7220 MicroMessenger/8.0.58.2841(0x28003A3C) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64 miniProgram/wx252bd59b6381cfc1',
                'Content-Type': 'application/json;charset=UTF-8',
                'X-Requested-With': 'com.tencent.mm',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://wzxy.chaoxing.com/h5/mobile/dormSign/index/message ',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en-US;q=0.7,en;q=0.6'
            }
            
            # 签到Headers
            headers_Sign = {
                'Host': 'wzxy.chaoxing.com',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json',
                'JWSESSION': f"{jws}",
                'Accept-Encoding': 'gzip,compress,br,deflate',
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.59(0x18003b2a) NetType/WIFI Language/zh_CN',
                'Referer': 'https://servicewechat.com/wx252bd59b6381cfc1/1/page-frame.html '
            }
            
            result = self.doBluePunch(headers, headers_Sign)
            if result == 0:
                self.log_message("签到流程完成")
            else:
                self.log_message("签到流程失败")
        
        # 重新启用按钮
        self.start_button.enabled = True
        self.start_button.text = "开始签到"

def main():
    return 单人签到()
