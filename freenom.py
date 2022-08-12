#!/usr/bin/env python3
# _*_ coding:utf-8 _*_
'''
cron: * 7 * * 2
new Env:('freenom域名自动续期');
'''
# 配置环境变量：export freenom_usr=""
# 配置环境变量：export freenom_psd=""
import requests
import re,os
try:
    from notify import send
except:
    print("upload notify failed")
    exit(-1)
try:
    username = os.environ["freenom_usr"]
    password = os.environ["freenom_psd"]
except:
    print("Pls config export in config.sh OR fill in username&password.")
LOGIN_URL = 'https://my.freenom.com/dologin.php'
DOMAIN_STATUS_URL = 'https://my.freenom.com/domains.php?a=renewals'
RENEW_DOMAIN_URL = 'https://my.freenom.com/domains.php?submitrenewals=true'

token_ptn = re.compile('name="token" value="(.*?)"', re.I)
domain_info_ptn = re.compile(
    r'<tr><td>(.*?)</td><td>[^<]+</td><td>[^<]+<span class="[^<]+>(\d+?).Days</span>[^&]+&domain=(\d+?)">.*?</tr>',
    re.I)
login_status_ptn = re.compile('<a href="logout.php">Logout</a>', re.I)
sess = requests.Session()
sess.headers.update({
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/103.0.5060.134 Safari/537.36'
})
sess.headers.update({
    'content-type': 'application/x-www-form-urlencoded',
    'referer': 'https://my.freenom.com/clientarea.php'
})

try:
    r = sess.post(LOGIN_URL, data={'username': username, 'password': password})

    if r.status_code != 200:
        print('Can not login. Pls check username&password.')
        exit(-1)

    sess.headers.update({'referer': 'https://my.freenom.com/clientarea.php'})
    r = sess.get(DOMAIN_STATUS_URL)
except:
    print('Network failed.')
    exit(-1)

if not re.search(login_status_ptn, r.text):
    print('login failed, retry')
    exit(-1)

page_token = re.search(token_ptn, r.text)
if not page_token:
    print('page_token missed')
    exit(-1)
token = page_token.group(1)

domains = re.findall(domain_info_ptn, r.text)
domains_list = []
renew_domains_succeed = []
renew_domains_failed = []

for domain, days, renewal_id in domains:
    days = int(days)
    domains_list.append(f'{domain} in {days} days')
    if days < 14:
        sess.headers.update({
            'referer':
            f'https://my.freenom.com/domains.php?a=renewdomain&domain={renewal_id}',
            'content-type': 'application/x-www-form-urlencoded'
        })
        try:
            r = sess.post(RENEW_DOMAIN_URL,
                          data={
                              'token': token,
                              'renewalid': renewal_id,
                              f'renewalperiod[{renewal_id}]': '12M',
                              'paymentmethod': 'credit'
                          })
        except:
            print('Network failed.')
            exit(-1)
        if r.text.find('Order Confirmation') != -1:
            renew_domains_succeed.append(domain)
        else:
            renew_domains_failed.append(domain)

print(domains_list, renew_domains_succeed, renew_domains_failed)
if renew_domains_failed:
    send('Caution! ', f'renew failed:{renew_domains_failed}')
else:
    send(f'Domains list:{domains_list}', f'Renew: {renew_domains_succeed}')
