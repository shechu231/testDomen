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
    #print(res.text)
    collect=json.loads(res.text)

    #获取详细信息
    detail = 'https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector'.format(
        host=apis['host'])
    res = session.post(url=detail,headers=headers,data=json.dumps({'collectorWid':collect["datas"]['rows'][0]['wid']}))
    schooleTaskWid = json.loads(res.text)
    print(schooleTaskWid['datas']['collector']['schoolTaskWid'])
    print(collect["datas"]['rows'][0]['wid'])
    print(collect['datas']['rows'][0]['formWid'])
    
    getForm='https://{host}/wec-counselor-collector-apps/stu/collector/getFormFields'.format(
        host=apis['host'])
    params = {"pageSize":100,"pageNumber":1,"formWid":collect['datas']['rows'][0]['formWid'],"collectorWid":collect["datas"]['rows'][0]['wid']}
    
    res = session.post(url=getForm,headers=headers,data=json.dumps(params))
    datas_rows = json.loads(res.text)
    #print(datas_rows)
    # for form_Content in datas_row['datas']['rows']:
    #     if form_Content['isRequired']==True:
    #         form_value="四川省/宜宾市/翠屏区/临港校区"
    datas_rows['datas']['rows'][0]['value']="四川省/宜宾市/翠屏区/临港校区"

    item_list=datas_rows['datas']['rows'][1]['fieldItems'][1]
    item_list['isSelected']=1
    datas_rows['datas']['rows'][1]['fieldItems']=[item_list]
    #体温
    datas_rows['datas']['rows'][2]['value']="36"
    datas_rows['datas']['rows'][3]['value']="36"
    datas_rows['datas']['rows'][4]['value']="36"
    #身体状况
    item_list=datas_rows['datas']['rows'][5]['fieldItems'][0]
    item_list['isSelected']=1
    datas_rows['datas']['rows'][5]['fieldItems']=[item_list]
    print(datas_rows['datas']['rows'][5]['fieldItems'])
    #是否返校
    item_list=datas_rows['datas']['rows'][6]['fieldItems'][1]
    item_list['isSelected']=1
    datas_rows['datas']['rows'][6]['fieldItems']=[item_list]
    print(datas_rows['datas']['rows'][6]['fieldItems'])
    for i in range(7,12):
        if datas_rows['datas']['rows'][i]['fieldType']=='2':
            datas_rows['datas']['rows'][i]['fieldItems']=[]

    params_form={"formWid":collect['datas']['rows'][0]['formWid'],"address":"签到地点","collectWid":collect["datas"]['rows'][0]['wid'],"schoolTaskwid":schooleTaskWid['datas']['collector']['schoolTaskWid'],"form":datas_rows['datas']['rows'],"uaIsCpadaily":True}
    print(params_form)
    #填表单
    #form='{"formWid":"717","address":"签到地点","collectWid":"'+collect["datas"]['rows'][0]['wid']+'","schoolTaskWid":"174319","form":[{"wid":"10405","formWid":"717","fieldType":"7","title":"今日具体所在地","description":"","isRequired":true,"hasOtherItems":false,"sort":1,"colName":"field001","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":1,"value":"四川省/宜宾市/翠屏区/临港校区","show":true,"formType":"0","sortNum":"1","logicShowConfig":{}},{"wid":"10406","formWid":"717","fieldType":"2","title":"是否在校","description":"","isRequired":true,"hasOtherItems":false,"sort":2,"colName":"field002","fieldItems":[{"itemWid":"15513","content":"否","imageUrl":null,"isOtherItems":false,"contentExtend":"","otherItemType":"1","basicConfig":null,"showLogic":"","isAnswer":false,"score":null,"isSelected":1,"selectCount":null,"totalCount":0}],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":2,"value":"","show":true,"formType":"0","sortNum":"2","logicShowConfig":{}},{"wid":"10407","formWid":"717","fieldType":"5","title":"上午体温","description":"","isRequired":true,"hasOtherItems":false,"sort":3,"colName":"field003","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":"35.0000","maxValue":"42.0000","decimals":5,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":3,"value":"36","show":true,"formType":"0","sortNum":"3","logicShowConfig":{}},{"wid":"10408","formWid":"717","fieldType":"5","title":"下午体温","description":"","isRequired":true,"hasOtherItems":false,"sort":4,"colName":"field004","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":"35.0000","maxValue":"42.0000","decimals":5,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":4,"value":"36","show":true,"formType":"0","sortNum":"4","logicShowConfig":{}},{"wid":"10409","formWid":"717","fieldType":"5","title":"晚上体温","description":"","isRequired":true,"hasOtherItems":false,"sort":5,"colName":"field005","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":"35.0000","maxValue":"42.0000","decimals":5,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":5,"value":"36","show":true,"formType":"0","sortNum":"5","logicShowConfig":{}},{"wid":"10410","formWid":"717","fieldType":"2","title":"身体状况","description":"","isRequired":true,"hasOtherItems":false,"sort":6,"colName":"field006","fieldItems":[{"itemWid":"15514","content":"身体健康","imageUrl":null,"isOtherItems":false,"contentExtend":"","otherItemType":"1","basicConfig":null,"showLogic":"","isAnswer":false,"score":null,"isSelected":1,"selectCount":null,"totalCount":0}],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":6,"value":"","show":true,"formType":"0","sortNum":"6","logicShowConfig":{}},{"wid":"10411","formWid":"717","fieldType":"2","title":"是否今日返校？","description":"","isRequired":true,"hasOtherItems":false,"sort":7,"colName":"field007","fieldItems":[{"itemWid":"15521","content":"否","imageUrl":null,"isOtherItems":false,"contentExtend":"","otherItemType":"1","basicConfig":null,"showLogic":"","isAnswer":false,"score":null,"isSelected":1,"selectCount":null,"totalCount":0}],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":7,"value":"","show":true,"formType":"0","sortNum":"7","logicShowConfig":{}},{"wid":"10412","formWid":"717","fieldType":"6","title":"到校时间","description":"","isRequired":false,"hasOtherItems":false,"sort":8,"colName":"field008","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":"1","dateType":"0","pointTime":null,"minTime":"1900-01-01 00:00","maxTime":"2099-12-31 23:59","extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":8,"value":"","show":true,"formType":"0","sortNum":"8","logicShowConfig":{}},{"wid":"10413","formWid":"717","fieldType":"2","title":"到校方式","description":"","isRequired":false,"hasOtherItems":false,"sort":9,"colName":"field009","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":9,"value":"","show":true,"formType":"0","sortNum":"9","logicShowConfig":{}},{"wid":"10414","formWid":"717","fieldType":"2","title":"到校是否有同行人员","description":"","isRequired":false,"hasOtherItems":false,"sort":10,"colName":"field010","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":null,"maxValue":null,"decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":10,"value":"","show":true,"formType":"0","sortNum":"10","logicShowConfig":{}},{"wid":"10415","formWid":"717","fieldType":"1","title":"到校同行人员姓名","description":"","isRequired":false,"hasOtherItems":false,"sort":11,"colName":"field011","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":"1","maxValue":"50","decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":11,"value":"","show":true,"formType":"0","sortNum":"11","logicShowConfig":{}},{"wid":"10416","formWid":"717","fieldType":"1","title":"到校同行人员身份证号","description":"","isRequired":false,"hasOtherItems":false,"sort":12,"colName":"field012","fieldItems":[],"scoringRule":"-1","score":null,"answerContent":null,"basicConfig":{"minValue":"1","maxValue":"100","decimals":null,"dateFormatType":null,"dateType":null,"pointTime":null,"minTime":null,"maxTime":null,"extremeLabel":null,"level":null,"isReversal":null,"leftValue":null,"rightValue":null,"voteType":null,"voteMinValue":null,"voteMaxValue":null},"logicWid":12,"value":"","show":true,"formType":"0","sortNum":"12","logicShowConfig":{}}],"uaIsCpadaily":true,"latitude":30.56559,"longitude":104.065668}'

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
    res = session.post(url='https://yibinu.campusphere.net/wec-counselor-collector-apps/stu/collector/submitForm'.format(host=apis['host']),headers=headers,json=params_form)
    if res.status_code!=200:
        os.system("pause")
    print(res.text)

    result=json.loads(res.text)
    if(result['message']!="SUCCESS"):
        x=0/0
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

    
    
