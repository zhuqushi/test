import sys
sys.path.append(".")

import requests
import json

import re

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode


# 登陆部分
# 定义加密函数，参数t为明文，e为密钥
def encrypt(t, e):
    # 将明文t转换为字符串
    t = str(t)
    # 将密钥e编码为utf-8格式
    key = e.encode('utf-8')
    # 创建AES加密对象，使用ECB模式
    cipher = AES.new(key, AES.MODE_ECB)
    # 将明文t编码为utf-8格式，并使用AES.block_size进行填充
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    # 使用AES加密对象对填充后的明文进行加密
    encrypted_text = cipher.encrypt(padded_text)
    # 将加密后的文本进行base64编码，并解码为utf-8格式
    return b64encode(encrypted_text).decode('utf-8')



def Login(headers_Login, username, password):
    # 将用户名和固定字符串拼接，取前16位作为密钥
    key = (str(username) + "0000000000000000")[:16]
    # 使用密钥加密密码
    encrypted_text = encrypt(password, key)
    # 定义登录接口地址
    login_url = 'https://wzxy.chaoxing.com/basicinfo/mobile/login/username'
    # 定义登录参数
    params = {
        "schoolId": school_id,
        "username": username,
        "password": encrypted_text
    }
    # 发送登录请求
    login_req = requests.post(login_url, params=params, headers=headers_Login)
    # 解析返回的json数据
    text = json.loads(login_req.text)
    # 判断登录是否成功
    if text['code'] == 0:
        # 打印登录成功信息
        print(f"{username}账号登陆成功！")
        # 获取返回的cookie
        set_cookie = login_req.headers['Set-Cookie']
        # 从cookie中提取JWSESSION
        jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
        # 返回JWSESSION
        return jws
    else:
        # 打印登录失败信息
        print(f"{username}登陆失败，请检查账号密码！")
        # 返回False
        return False

def upload_blue_data(blue1, headers_Sign, id, signid):
    # 定义一个字典，包含蓝牙数据
    data = {
        "blue1": blue1,
        "blue2": [],
        # "blue2": list(blue2.values()),
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
        "street": "博学街"}
        # 这里原来的请求体没有location字段，但是解包小程序post的请求体是有location字段的，加上试一下
    }
    # 发送POST请求，上传蓝牙数据
    response = requests.post(
        url=f"https://wzxy.chaoxing.com/dormSign/mobile/receive/doSignByDevice?id={id}&signId={signid}",
        headers=headers_Sign, json=data)
    if response.status_code == 200:
        # 解析返回的JSON数据
        response_data = response.json()
        # 判断返回的code是否为0，即打卡成功
        if response_data.get("code") == 0:
            # 发送打卡成功的通知
            print("打卡成功")
            return 0
        elif response_data.get("code") == 1:
            # 发送打卡结束的通知
            print("打卡已结束")
            return 1
        else:
            # 发送打卡失败的通知
            print("打卡失败")
            return 1
    else:
        # 请求失败，返回1
        return 1


def doBluePunch(headers,headers_Sign):
    # 获取签到日志
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
    except:
        print("获取签到日志失败！")
    return upload_blue_data(blue1, headers_Sign, location_id, sign_id)

# 蓝牙模块结束


def main():
    global school_id
    userinfo = {
        "2211100511": "lsy19126" # 用户列表最后一行结束不需要加逗号
    }
    school_id = 614
    # 登录Headers
    headers_Login = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; WLZ-AN00 Build/HUAWEIWLZ-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 XWEB/4343 MMWEBSDK/20220903 Mobile Safari/537.36 MMWEBID/4162 MicroMessenger/8.0.28.2240(0x28001C35) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wxce6d08f781975d91'}
    for key, value in userinfo.items():
    # 从这里开始下面的代码一直到main函数结束都要添加一个缩进
        getjws = Login(headers_Login, key, value)

        jws = getjws  # 手动填写jws

        # 鉴权Headers
        headers = {
            # 【新增】sec-ch-ua-platform: 表示客户端操作系统平台
            'sec-ch-ua-platform': '"Android"',
            # 【新增】sec-ch-ua: 浏览器品牌标识，用于设备指纹识别
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Android WebView";v="134"',
            # 【新增】sec-ch-ua-mobile: 是否是移动设备
            'sec-ch-ua-mobile': '?1',
            # 【修改】Host 从 gw.wozaixiaoyuan.com 改为 wzxy.chaoxing.com
            'Host': 'wzxy.chaoxing.com',
            # 【保留】连接保持活跃
            'Connection': 'keep-alive',
            # 【保留】接受 JSON 格式数据
            'Accept': 'application/json, text/plain, */*',
            # 【修改】jwsession 和 cookie 中 JWSESSION 的值更明确地对应真实抓包中的值
            'jwsession': jws,
            "cookie": f'JWSESSION={jws}; WZXYSESSION={jws}',
            # 【修改】User-Agent 更换为与抓包一致的真实微信小程序环境下的 UA
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RTE-AL00 Build/HUAWEIRNA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.136 Mobile Safari/537.36 XWEB/1340095 MMWEBSDK/20250201 MMWEBID/7220 MicroMessenger/8.0.58.2841(0x28003A3C) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64 miniProgram/wx252bd59b6381cfc1',
            # 【保留】发送内容类型为 JSON
            'Content-Type': 'application/json;charset=UTF-8',
            # 【保留】表示请求来自微信小程序
            'X-Requested-With': 'com.tencent.mm',
            # 【保留】跨域请求相关
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            # 【修改】Referer 从 health 页面改为 dormSign/message 页面
            'Referer': 'https://wzxy.chaoxing.com/h5/mobile/dormSign/index/message ',
            # 【新增】支持更多编码格式（gzip、deflate、br、zstd）
            'Accept-Encoding': 'gzip, deflate, br',
            # 【修改】Accept-Language 更加完整
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

        doBluePunch(headers, headers_Sign)

if __name__ == "__main__":
    print("ok")
    main()



