# -*- coding: utf8 -*-
# -*- by:look新
# -*- 2021年10月12日
#
import datetime
import json
import pytz
import requests
import urllib3
import os

urllib3.disable_warnings()
pwd = os.path.dirname(os.path.abspath(__file__)) + os.sep

BASE_URL = "https://api.moguding.net:9000/"
SIGN_URL = "http://api.mcyou.xyz/"

headers = {
        "Host": "api.moguding.net:9000",
        "accept-language": "zh-CN,zh;q=0.8",
        "user-agent": "手机的ua",#查询https://www.ip138.com/useragent/查询
        "sign": "",
        "authorization": "",
        "rolekey": "",
        "content-type": "application/json; charset=UTF-8",
        "accept-encoding": "gzip",
        "cache-control": "no-cache"
}

INFORMATION = {"phone":"账号",
                   "password":"密码"}
MESSAGE = ""
TITLE = ""
UPDATE_INFO = ""
FAILURES_COUNT = 0

# 登录
def login():
    global MESSAGE,FAILURES_COUNT
    if INFORMATION.get("phone") is None or INFORMATION.get("phone").strip() == '':
        MESSAGE += "\n手机号为空"
        return
    if INFORMATION.get("password") is None or INFORMATION.get("password").strip() == '':
        MESSAGE += "\n密码为空"
        return
    requestsBody = {
        "phone": INFORMATION["phone"],
        "password": INFORMATION["password"],
        "loginType": "android",
        "uuid": ""
    }
    url = BASE_URL + "session/user/v1/login"
    response = requests.post(url=url, headers=headers, data=json.dumps(requestsBody), verify=False)
    responseJson = response.json()
    if responseJson["code"] != 200:
        msg = responseJson["msg"]
        FAILURES_COUNT+=1
        print(msg)
        return
    data = responseJson["data"]
    #print(data)
    nikeName = data["nikeName"]
    userId = data["userId"]
    token = data["token"]
    userType = data["userType"]
    moguNo = data["moguNo"]

    newData = {
        "nikeName": nikeName,
        "userId": userId,
        "token": token,
        "userType": userType,
        "moguNo": moguNo
    }
    INFORMATION.update(newData)
def getUserInfo():
    global MESSAGE
    headers.update(
        {"authorization": INFORMATION.get("token"), "rolekey": "student"}
    )
    requestsBody = {}
    url = BASE_URL + "usercenter/user/v1/info"
    response = requests.post(url=url, headers=headers, data=json.dumps(requestsBody), verify=False)
    responseJson = response.json()
    if responseJson["code"] != 200:
        MESSAGE = responseJson["msg"]
        print(responseJson["msg"])
    else:
        data = responseJson["data"]
        nikeName = data["nikeName"]
        userId = data["userId"]
        userType = data["userType"]
        moguNo = data["moguNo"]

        newData = {
            "nikeName": nikeName,
            "userId": userId,
            "userType": userType,
            "moguNo": moguNo
        }
        INFORMATION.update(newData)
# 获取计划
def getPlanByStu():
    global TITLE, MESSAGE
    # 没有token则重新登录
    login()

    getUserInfo()
    paramString = ""
    parameterSign = {
        "userId": INFORMATION["userId"],
        "paramString": paramString,
        "moguNo": INFORMATION["moguNo"],
        "userType": INFORMATION["userType"],
    }
    sign = getSign("getsigninfo.php", parameterSign)
    headers.update(
        {"authorization": INFORMATION.get("token"), "rolekey": "student", "sign": sign}
    )
    requestsBody = {
        "state": paramString
    }
    url = BASE_URL + "practice/plan/v3/getPlanByStu"
    response = requests.post(url=url, headers=headers, data=json.dumps(requestsBody), verify=False)
    responseJson = response.json()
    print(responseJson)
    if responseJson["code"] != 200:
        print(responseJson["msg"])
    else:
        dataList = responseJson["data"]
        data = dataList[len(dataList) - 1]
        planName = data["planName"]
        planId = data["planId"]
        dataNew = {
            "planName": planName,
            "planId": planId,
        }
        INFORMATION.update(dataNew)

# 获取sign
def getSign(url,parameter):
    response = requests.post(url=SIGN_URL + url,data=parameter)
    responseJson = response.json()
    print(responseJson)
    if responseJson["code"] == 200 :
        return responseJson["sign"]

def signIn(type):
    global TITLE, MESSAGE

    if INFORMATION.get("token") is None or INFORMATION.get("token").strip() == '':
        print("没有获取到token，请检查是否正确登录！")
        return

    if INFORMATION.get("planId") is None or INFORMATION.get("planId").strip() == '':
        print("没有获取到planId，请检查是否正确指定签到对象！")
        MESSAGE = "没有获取到planId，请检查是否正确指定签到对象！"
        return

    typeStr = "START" if type == 1 else "END"

    parameterSign = {
        "userId": INFORMATION["userId"],
        "moguNo": INFORMATION["moguNo"],
        "address": "签到地址",
        "device": "Android",
        "planId": INFORMATION["planId"],
        "type": typeStr,
        "latitude": "经度",
        "longitude": "维度"
    }

    sign = getSign("getsignseve.php", parameterSign)
    headers.update({"authorization": INFORMATION.get("token"), "rolekey": "student", "sign": sign})



    requestsBody = {
        "country": "",
        "address": "签到地址",
        "province": "",
        "city": "",
        "latitude": INFORMATION.get("latitude"),
        "description": "",
        "planId": INFORMATION["planId"],
        "type": typeStr,
        "device": "经度",
        "longitude": "维度"
    }

    url = BASE_URL + "attendence/clock/v2/save"

    response = requests.post(url=url, headers=headers, data=json.dumps(requestsBody), verify=False)
    responseJson = response.json()

    if responseJson["code"] != 200:
        msg = responseJson["msg"]
        MESSAGE = msg
        print(msg)
    else:
        createTime = responseJson["data"]["createTime"]
        TITLE = "%s，%s打卡成功!" % (INFORMATION["nikeName"], "上班" if typeStr == "START" else "下班")
        MESSAGE = "  目标:%s\n\n  打卡时间:%s \n\n  打卡地点:%s" % (INFORMATION["planName"], createTime, INFORMATION['address'])

# 主程序
def main():
    global INFORMATION, TITLE, MESSAGE

    getPlanByStu()
    hourNow = datetime.datetime.now(pytz.timezone('PRC')).hour
    signIn(1)  #1上班 0下班
    MESSAGE = UPDATE_INFO + MESSAGE
    if TITLE == "":
        TITLE = "%s,打卡失败!" % (INFORMATION["nikeName"])

    INFORMATION = {}
    MESSAGE = ""
    TITLE = ""


if __name__ == '__main__':
    main()
#sign的地址可能会过期，记得可以加群获取最新签名：568330068
