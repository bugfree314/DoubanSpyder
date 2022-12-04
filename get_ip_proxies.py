#!python

import requests
from bs4 import BeautifulSoup
from pandas import DataFrame

base_url = 'https://www.kuaidaili.com/free/inha/'  # +page num
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    # 'Cookie': 'Hm_lpvt_7ed65b1cc4b810e9fd37959c9bb51b31=1668567145; Hm_lvt_7ed65b1cc4b810e9fd37959c9bb51b31=1668566130; _ga=GA1.2.1664604482.1668566130; _gid=GA1.2.711564170.1668566130; _gcl_au=1.1.2062328034.1668566131; channelid=0; sid=1668564531959599'
}
ip_pool_info = []
page = 1
r = requests.get(base_url+str(page), headers=headers)
assert r.status_code == 200
r.encoding='u8'
soup = BeautifulSoup(r.text)
main_tag = soup.find('table', class_='table table-bordered table-striped')
tags = main_tag.find('tbody').findAll('tr')
ip_pool_info = [{i.attrs['data-title']:i.text for i in t.findAll('td')} for t in tags]
df = DataFrame(ip_pool_info)
df.to_json('ip_proxy_pool.json')
