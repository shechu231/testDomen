# -*- coding:utf-8 -*-
import sys
import requests
import json
from urllib.parse import urlparse
from selenium import webdriver
from time import sleep
from selenium.webdriver.chrome.options import Options
import socket
import os
#判断设备是否联网
def isNetOK(testserver):
    s = socket.socket()
    s.settimeout(3)
    try:
        status = s.connect_ex(testserver)
        if status == 0:
            s.close()
            return True
        else:
            return False
    except Exception as e:
        return False

def isNetChainOK(testserver=('www.baidu.com', 443)):
    isOK = isNetOK(testserver)
    return isOK

#获取cookie,通过浏览器登陆方式
def getCookie(useranme,password):
    print("模拟浏览器登陆开始")
    # 无头浏览器
    chrome_options = Options()
    # 后面的两个是固定写法 必须这么写 无头浏览器
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    bro = webdriver.Chrome(executable_path="./chromedriver",options=chrome_options)
    # 登陆的网址
    bro.get('http://authserver.yibinu.edu.cn/authserver/login?service=https%3A%2F%2Fyibinu.campusphere.net%2Fportal%2Flogin')
    sleep(10)
    # 模拟登陆开始
    bro.find_element_by_id("username").send_keys(useranme)
    bro.find_element_by_id("password").send_keys(password)
    bro.find_elements_by_xpath('//form[@id="casLoginForm"]//button[@type="submit"]')[0].click()
    sleep(6)
    # 获取cookie
    cookies = bro.get_cookies()
    # print(cookies)
    cookieStr=""
    for cookie in cookies:
        cookieStr+=cookie["name"]+"="+cookie["value"]+";"
    print(cookieStr[:-1])
    print("模拟浏览器登陆结束")
    bro.close()
    return cookieStr[:-1]

def getCpdailyApis():
    apis = {}
    params = {
        'ids': '1018789912947381'
    }
    res = requests.get(url='https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params)
    if res.status_code!=200:
        os.system("pause")
    data = res.json()['data'][0]
    joinType = data['joinType']
    idsUrl = data['idsUrl']
    ampUrl = data['ampUrl']
    if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
        parse = urlparse(ampUrl)
        host = parse.netloc
        res = requests.get(parse.scheme + '://' + host)
        parse = urlparse(res.url)
        apis[
            'login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
        apis['host'] = host

    ampUrl2 = data['ampUrl2']
    if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
        parse = urlparse(ampUrl2)
        host = parse.netloc
        res = requests.get(parse.scheme + '://' + host)
        parse = urlparse(res.url)
        apis['login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
        apis['host'] = host
    return apis

def getSession(apis,cookieStr):
    cookies = {}
    # 借助上一个项目开放出来的登陆API，模拟登陆
    # res = 'HWWAFSESID=6146773724bb62d491;HWWAFSESTIME=1621905097753;MOD_AUTH_CAS=ST-5695784-GRMg5sgGKiH3NVeznBeC1621905087691-Oduf-cas'
    print(cookieStr)
    # 解析cookie
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    session = requests.session()
    session.cookies = requests.utils.cookiejar_from_dict(cookies, cookiejar=None, overwrite=True)
    # print(session.cookies)
    return session
def submitForm(session, apis):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 yiban/8.1.11 cpdaily/8.1.11 wisedu/8.1.11',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    queryCollectWidUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'.format(
        host=apis['host'])
    params = {
        'pageSize': 6,
        'pageNumber': 1
    }
    res = session.post(queryCollectWidUrl, headers=headers,
                       data=json.dumps(params))
    if res.status_code!=200:
        os.system("pause")
    print(res.text)

    collect=json.loads(res.text)
    print(collect["datas"]['rows'][0]['wid'])
    form='{"formWid":"543","address":"中国四川省宜宾市翠屏区","collectWid":"'+collect["datas"]['rows'][0]['wid']+'","schoolTaskWid":"142331","form":[{"wid":"7284","formWid":"543","fieldType":1,"title":"今日具体所在地","description":"","minLength":1,"sort":"1","maxLength":300,"isRequired":1,"imageCount":-2,"hasOtherItems":0,"colName":"field001","value":"四川省/宜宾市/翠屏区","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[],"area1":"四川省","area2":"宜宾市","area3":"翠屏区"},{"wid":"7285","formWid":"543","fieldType":2,"title":"是否在校","description":"","minLength":0,"sort":"2","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field002","value":"10970","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[{"itemWid":"10970","content":"是","isOtherItems":0,"contendExtend":null,"isSelected":1}]},{"wid":"7286","formWid":"543","fieldType":5,"title":"上午体温","description":"","minLength":0,"sort":"3","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field003","value":"36","minValue":35,"maxValue":42,"isDecimal":true,"fieldItems":[]},{"wid":"7287","formWid":"543","fieldType":5,"title":"下午体温","description":"","minLength":0,"sort":"4","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field004","value":"36","minValue":35,"maxValue":42,"isDecimal":true,"fieldItems":[]},{"wid":"7288","formWid":"543","fieldType":5,"title":"晚上体温","description":"","minLength":0,"sort":"5","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field005","value":"36","minValue":35,"maxValue":42,"isDecimal":true,"fieldItems":[]},{"wid":"7289","formWid":"543","fieldType":2,"title":"身体状况","description":"","minLength":0,"sort":"6","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field006","value":"10972","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[{"itemWid":"10972","content":"身体健康","isOtherItems":0,"contendExtend":null,"isSelected":1}]},{"wid":"7290","formWid":"543","fieldType":2,"title":"是否今日返校？","description":"","minLength":0,"sort":"7","maxLength":null,"isRequired":1,"imageCount":null,"hasOtherItems":0,"colName":"field007","value":"10979","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[{"itemWid":"10979","content":"否","isOtherItems":0,"contendExtend":null,"isSelected":1}]},{"wid":"7291","formWid":"543","fieldType":1,"title":"到校时间","description":"","minLength":1,"sort":"8","maxLength":300,"isRequired":0,"imageCount":-1,"hasOtherItems":0,"colName":"field008","value":"","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[],"tempValue":""},{"wid":"7292","formWid":"543","fieldType":2,"title":"到校方式","description":"","minLength":0,"sort":"9","maxLength":null,"isRequired":0,"imageCount":null,"hasOtherItems":0,"colName":"field009","value":"","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[]},{"wid":"7293","formWid":"543","fieldType":2,"title":"到校是否有同行人员","description":"","minLength":0,"sort":"10","maxLength":null,"isRequired":0,"imageCount":null,"hasOtherItems":0,"colName":"field010","value":"","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[]},{"wid":"7294","formWid":"543","fieldType":1,"title":"到校同行人员姓名","description":"","minLength":1,"sort":"11","maxLength":50,"isRequired":0,"imageCount":null,"hasOtherItems":0,"colName":"field011","value":"","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[]},{"wid":"7295","formWid":"543","fieldType":1,"title":"到校同行人员身份证号","description":"","minLength":1,"sort":"12","maxLength":100,"isRequired":0,"imageCount":null,"hasOtherItems":0,"colName":"field012","value":"","minValue":0,"maxValue":0,"isDecimal":true,"fieldItems":[]}],"uaIsCpadaily":true,"latitude":28.823728,"longitude":104.689019}'

    # detailCollector = 'https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector'.format(
    #     host=host)
    # res = session.post(url=detailCollector, headers=headers,
    #                    data=json.dumps({"collectorWid": collectWid}), verify=not debug)
    # schoolTaskWid = res.json()['datas']['collector']['schoolTaskWid']

    headers={
        'tenantId':'1018789912947381',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PACM00 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0',
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': '6XkC1UAk07fK0uTaGPUu77i/+r7j/o1JQ/XygRxee2LMiX5H+w/BOrLr7jYW HhkJ4NsXsQgSis/0/xM9y3Nvt+11z190ul2ht49jixDTvDZfO1ewPSVkb3Kp axSzywZFRSPyEXunxbsDs2Hzstytw8WP0G6iXRrkVQScv63hVMFOMDCDlSXR BS2AA3Dg7govQoaGgSaGX8cuLc7JMViofZXWvuSwVcuAMT94l/67fxjt8kQr 1ANNQdz5e3tNFQvp',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': 'yibinu.campusphere.net',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }
    # 签到
    # print(json.loads(form))
    res = session.post(url='https://yibinu.campusphere.net/wec-counselor-collector-apps/stu/collector/submitForm'.format(host=apis['host']),headers=headers,json=json.loads(form))
    if res.status_code!=200:
        os.system("pause")
    print(res.text)

    result=json.loads(res.text)
    # print(result['message'])
    if(result['message']!="该收集已填写无需再次填写"):
        if(result['message']!="SUCCESS"):
            os.system("pause")
def sign(account,password):
    cookies=getCookie(account,password)#获取cookie值
    #print(cookies)
    print(getCpdailyApis())
    apis=getCpdailyApis()#获取登陆的网址，网址是固定的
    session=getSession(getCpdailyApis(),cookies)#传递cookie值
    submitForm(session,apis)#提交表单,进行签到
    print("************************************************************************")
if __name__=="__main__":
    while(isNetChainOK()!=True):
        print("电脑还没有联网")
        sleep(1)
    print("联网成功")

    account=sys.argv[1] #获取参数
    print(account)
    accounts=account.split("#"); #分开用户
    #打印账号
    print(accounts)
    for one in accounts:
        account=one.split("pwd:")#分开用户账号和密码
        #print(account)
        sign(account[0],account[1])

    
    
