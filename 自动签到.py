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
import uuid
import base64
from pyDes import des, CBC, PAD_PKCS5
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
    cookieStr=""
    try:
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
        for cookie in cookies:
            cookieStr+=cookie["name"]+"="+cookie["value"]+";"
        print(cookieStr[:-1])
        print("模拟浏览器登陆结束")
        bro.quit()
    except:
        bro.quit()
        sleep(2)
        x=0/0
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

def resJsonEncode(res):
    '''响应内容的json解析函数(换而言之，就是res.json()的小优化版本)'''
    try:
        return res.json()
    except Exception as e:
        raise Exception(
            f'响应内容以json格式解析失败({e})，响应内容:\n\n{res.text}')

# 填充表单
def fillForm(form,userInfo):
    index = 0
    for formItem in form[:]:
        # 只处理必填项
        if formItem['isRequired']:
            userForm = userInfo['forms'][index]['form']
            # 判断是否忽略该题
            if 'ignore' in userForm and userForm['ignore']:
                # 设置显示为false
                formItem['show'] = False
                # 清空所有的选项
                if 'fieldItems' in formItem:
                    formItem['fieldItems'].clear()
                index += 1
                continue
            # 判断用户是否需要检查标题
            if userInfo['checkTitle'] == 1:
                # 如果检查到标题不相等
                if formItem['title'].strip() != userForm['title'].strip():
                    raise Exception(
                        f'\r\n第{index + 1}个配置项的标题不正确\r\n您的标题为："{userForm["title"]}"\r\n系统的标题为："{formItem["title"]}"')
            # 填充多出来的参数（新版增加了四个参数，暂时不知道作用）
            formItem['show'] = True
            formItem['formType'] = '0'  # 盲猜是任务类型、待确认
            formItem['sortNum'] = str(formItem['sort'])  # 盲猜是sort排序
            formItem['logicShowConfig'] = {}
            preSelect = []
            # 文本选项直接赋值
            if formItem['fieldType'] in ['1', '5', '6', '7']:
                formItem['value'] = userForm['value']
            # 单选框填充
            elif formItem['fieldType'] == '2':
                # 定义单选框的wid
                itemWid = ''
                # 单选需要移除多余的选项
                fieldItems = formItem['fieldItems']
                for fieldItem in fieldItems[:]:
                    if 'value' not in userForm:
                        raise Exception(
                            f"第{index + 1}个题目出错，题目标题为{formItem['sort']}{formItem['title']}")
                    if fieldItem['content'] != userForm['value']:
                        fieldItems.remove(fieldItem)
                        # 如果之前被选中
                        if fieldItem['isSelected']:
                            preSelect.append(fieldItem['content'])
                    else:
                        itemWid = fieldItem['itemWid']
                        # 当该字段需要填写且存在otherItemType类型时（其他字段）
                        if fieldItem['isOtherItems'] and fieldItem['otherItemType'] == '1':
                            # 当配置文件中不存在other字段时抛出异常
                            if 'other' not in userForm:
                                raise Exception(
                                    f'\r\n第{index + 1}个配置项的选项不正确，该字段存在“other”字段，请在配置文件“title，value”下添加一行“other”字段并且填上对应的值'
                                )
                            fieldItem['contentExtend'] = userForm['other']
                if itemWid == '':
                    raise Exception(
                        f'\r\n第{index + 1}个配置项的选项不正确，该选项为单选，且未找到您配置的值\r\n您上次的选值为：{preSelect}'
                    )
                formItem['value'] = itemWid
            # 多选填充
            elif formItem['fieldType'] == '3':
                # 定义单选框的wid
                itemWidArr = []
                fieldItems = formItem['fieldItems']
                userItems = userForm['value'].split('|')
                for fieldItem in fieldItems[:]:
                    if fieldItem['content'] in userItems:
                        itemWidArr.append(fieldItem['itemWid'])
                        # 当该字段需要填写且存在otherItemType类型时（其他字段）
                        if fieldItem['isOtherItems'] and fieldItem['otherItemType'] == '1':
                            # 当配置文件中不存在other字段时抛出异常
                            if 'other' not in userForm:
                                raise Exception(
                                    f'\r\n第{index + 1}个配置项的选项不正确，该字段存在“other”字段，请在配置文件“title，value”下添加一行“other”字段并且填上对应的值'
                                )
                            fieldItem['contentExtend'] = userForm['other']
                    else:
                        fieldItems.remove(fieldItem)
                        if fieldItem['isSelected']:
                            preSelect.append(fieldItem['content'])
                # 若多选一个都未选中
                if len(itemWidArr) == 0:
                    raise Exception(
                        f'\r\n第{index + 1}个配置项的选项不正确，该选项为多选，且未找到您配置的值\r\n您上次的选值为：{preSelect}'
                    )
                formItem['value'] = ','.join(itemWidArr)
                # 填充其他信息
                formItem.setdefault('http', {
                    'defaultOptions': {
                        'customConfig': {
                            'pageNumberKey': 'pageNumber',
                            'pageSizeKey': 'pageSize',
                            'pageDataKey': 'pageData',
                            'pageTotalKey': 'pageTotal',
                            'data': 'datas',
                            'codeKey': 'code',
                            'messageKey': 'message'
                        }
                    }
                })
                formItem['uploadPolicyUrl'] = '/wec-counselor-collector-apps/stu/oss/getUploadPolicy'
                formItem['saveAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/saveAttachment'
                formItem['previewAttachmentUrl'] = '/wec-counselor-collector-apps/stu/collector/previewAttachment'
                formItem['downloadMediaUrl'] = '/wec-counselor-collector-apps/stu/collector/downloadMedia'
            else:
                raise Exception(
                    f'\r\n第{index + 1}个配置项属于未知配置项，请反馈'
                )
            index += 1
        else:
            # 移除非必填选项
            form.remove(formItem)

def submitForm(session, apis,user):

    
    headers = session.headers
    headers['Content-Type'] = 'application/json'
    queryUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'.format(host=apis['host'])
    params = {
        'pageSize': 20,
        "pageNumber": 1
    }
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 yiban/8.1.11 cpdaily/8.1.11 wisedu/8.1.11',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    res = session.post(queryUrl, data=json.dumps(
            params), headers=headers, verify=False)
    res = resJsonEncode(res)
    
    if res['datas']['totalSize'] < 1:
            raise Exception('查询表单失败，当前没有信息收集任务哦！')
    collectWid = res['datas']['rows'][0]['wid'] #表单id
    formWid = res['datas']['rows'][0]['formWid']
    detailUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector'.format(host=apis['host'])
    res = session.post(detailUrl, headers=headers, data=json.dumps({'collectorWid': collectWid}),
                                verify=False)
    res = resJsonEncode(res)
    schoolTaskWid = res['datas']['collector']['schoolTaskWid']
    getFormUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/getFormFields'.format(host=apis['host'])
    params = {"pageSize": 100, "pageNumber": 1,
                  "formWid": formWid, "collectorWid": collectWid}
    res = session.post(
            getFormUrl, headers=headers, data=json.dumps(params), verify=False)
    res = resJsonEncode(res)
    form = res['datas']['rows']
    
    fillForm(form,user)
    forBody = {
        "formWid": formWid, "address": user['address'], "collectWid": collectWid,
        "schoolTaskWid": schoolTaskWid, "form": form, "uaIsCpadaily": True,
        "latitude": user['lat'], 'longitude': user['lon']
    }

    #params_form = form

    
    #print(params_form)
    forSubmit = {
        "appVersion": "8.1.14",
        "deviceId": str(uuid.uuid1()),
        "lat": "30.574166",
        "lon": "114.244845",
        "model": "OPPO R11 Plus",
        "systemName": "android",
        "systemVersion": "11",
        "userId": user['username'],
    }
    extension = {
        "lon": "114.244845",
        "model": "OPPO R11 Plus",
        "appVersion": "8.1.14",
        "systemVersion": "4.4.4",
        "userId": "181106031",
        "systemName": "android",
        "lat": "30.574166",
        "deviceId": str(uuid.uuid1())
    }
    #处理加密
    forBody = json.dumps(forBody, ensure_ascii=False)
    print('正在请求加密数据...')
    res = session.post("https://api.ruoli.cc/wise/getEncryption", params=forSubmit, data=forBody.encode("utf-8"), verify=False)
    print(res.text)
    res = res.json()
    forSubmit['version'] = 'first_v2'
    forSubmit['calVersion'] = 'firstv'
    forSubmit['bodyString'] = res['data']['bodyString']
    forSubmit['sign'] = res['data']['sign']
    #print(res['data']['bodyString'])
    headers={
        'tenantId':'1018789912947381',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PACM00 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0',
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': DESEncrypt(json.dumps(extension)),
        'Content-Type': 'application/json; charset=utf-8',
        'Host': 'yibinu.campusphere.net',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }
    # 签到
    # print(json.loads(form))

    res = session.post(url='https://yibinu.campusphere.net/wec-counselor-collector-apps/stu/collector/submitForm'.format(host=apis['host']),headers=headers,data=json.dumps(forSubmit))

    print(res.text)
    #result=json.loads(res.text)

# DES加密
def DESEncrypt(s, key='b3L26XNL'):
    key = key
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    encrypt_str = k.encrypt(s)
    return base64.b64encode(encrypt_str).decode()

def sign(account,password,user):
    cookies=getCookie(account,password)#获取cookie值
    #print(cookies)
    print(getCpdailyApis())
    apis=getCpdailyApis()#获取登陆的网址，网址是固定的
    session=getSession(getCpdailyApis(),cookies)#传递cookie值
    submitForm(session,apis,user)#提交表单,进行签到
    print("************************************************************************")
if __name__=="__main__":
    while(isNetChainOK()!=True):
        print("电脑还没有联网")
        sleep(1)
    print("联网成功")

    
    users={'author': '若离QQ：2909998156', 'sendType': 0, 'emailApiUrl': 'https://api.ruoli.cc/sendMail', 'myQmsgKey': '', 'encryptApi': 'https://api.ruoli.cc/wise/getEncryption', 'users': []}
    
    account=sys.argv[1] #获取参数
    print(account)
    accounts=account.split("#"); #分开用户
    for one in accounts:
        user = {'user': {'type': 1, 'schoolName': '宜宾学院', 'username': '', 'password': '', 'address': '四川省/宜宾市/翠屏区/临港校区', 'sendKey': '', 'lon': 104.616858, 'lat': 28.793022, 'checkTitle': 1, 'proxy': '', 'isOffset': True, 'forms': [{'form': {'title': '今日具体所在地', 'value': '四川省/宜宾市/翠屏区/临港校区'}}, {'form': {'title': '是否在校', 'value': '是'}}, {'form': {'title': '上午体温', 'value': 36.2}}, {'form': {'title': '下午体温', 'value': 36.4}}, {'form': {'title': '晚上体温', 'value': 36.1}}, {'form': {'title': '身体状况', 'value': '身体健康'}}, {'form': {'title': '是否今日返校？', 'value': '否'}}]}}
        account=one.split("pwd:")#分开用户账号和密码
        #print(account)
        user['user']["username"]=account[0]
        user["user"]["password"]=account[1]
        users['users'].append(user)
        
    
    for i in users["users"]:
        #print(i["user"]["username"],i["user"]["password"],i["user"])
        sign(i["user"]["username"],i["user"]["password"],i["user"])
