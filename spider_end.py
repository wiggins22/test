# -*- coding: utf-8 -*-
"""
Created on Tue Aug  7 09:00:49 2018

@author: Administrator
"""
from bs4 import BeautifulSoup
from lxml import etree
from chardet import  detect
from urllib import request,parse
import gzip,time,re,os
from urls_n import DisUrls
from mongo import MongoDB
from fake_useragent import UserAgent
from random import randint
def dowmloadHtml(urls):
    '''
    下载器 参数urls为一个url管理器对象
    '''
    #重复确认待爬是否空队列
    for x in range(3):
        url=urls.get()
        if url:
            break
        time.sleep(1)
    #当待爬为空时返回爬虫终止条件
    if not url:
       return False,False
    #构造下载对象并下载
    headers={
            'User-Agent':UserAgent().random
            }
    req=request.Request(url,headers=headers)
    try:
        r=request.urlopen(req)
        data=r.read()
        if r.getheader('Content-Encoding')=='gzip':
            data=gzip.decompress(data)
        #下载未成功处理
        if not check_download(r):
           urls.move(url)
           return False,url
        html=data.decode(detect(data)['encoding'],errors='ignore')
        return html,r.url
    except:
        urls.move(url)
        return False,url
    
def check_download(r):
    '''
    下载响应检测方法，用来检测是否下载成功
    @r 下载响应对象
    '''
    if r.getcode()==200:
        return True
    else:
        print('ERROR',r.getcode())
        return False
    
def links(url,html,urls):
    '''
    url分析
    @url 当前要分析的页面请求地址url
    @html 待分析的html代码
    @urls url管理器对象
    '''
    sel=etree.HTML(str(html))
    links=sel.xpath('//a/@href')
    for i in range(len(links)):
        links[i]=parse.urljoin(url,links[i])
    for x in links:
        try:
            if '.'.join(x.split('/')[2].split('.')[-2:])=='.'.join(url.split('/')[2].split('.')[-2:]):
                urls.add(x)
        except:
            pass
def options(urls,dbs):
    '''
    爬虫分析代码
    @urls url管理器实例
    @dbs 数据存储对象实例
    '''
    html,url=dowmloadHtml(urls)
    
    if url==False:
        return False
    if html==False:
        return True
    sel=etree.HTML(html)
    if re.search(r'buycar/b-dealer',url):
        try:
            car_data={
                    'imgs':sel.xpath('//ul[@id="taoche-details-piclist"]/li/img/@data-zoomimage'),
                    'car_name':sel.xpath('//h1[@class="title"]/text()')[0],
                    'car_price':sel.xpath('//strong[@class="price-this"]/text()')[0],
                       }
        except:
            print('ERROR',url)
            return True
        '''for i in range(len(car_data['imgs'])):
            headers={
            'Referer':url
            }
            src=parse.urljoin(url,car_data['imgs'][i])
            filename='./imges/'+str(time.time())+'_'+str(randint(10,99))+'.'+src.split('.')[-1]
            req=request.Request(src,headers=headers)
            #request.urlretrieve(src,filename)
            with open(filename,'wb') as f:
                r=request.urlopen(req)
                f.write(r.read())
                car_data['imgs'][i]={'souce':src,'local':filename}
        '''
        print(car_data)
        dbs.add_one('car',car_data)
        links(url,html,urls)
    else:
        links(url,html,urls)
    return True

def tt(urls,dbs):
    while True:
        a=options(urls,dbs)
        if not a:
            break
if __name__=='__main__':
    #爬虫调度主程序
    #from multiprocessing import Pool
    from threading import Thread
    #pool=Pool(5)
    spider_name='car'
    star_url='http://xian.taoche.com/all/?from=2103093&reffer=https://www.baidu.com/s?wd=%E6%B7%98%E8%BD%A6%E7%BD%91&rsv_spt=1&rsv_iqid=0xe7e34e6800000427&issp=1&f=8&rsv_bp=0&rsv_idx=2&ie=utf-8&tn=baiduhome_pg&rsv_enter=1&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&inputT=2355&rsv_sug4=2356'
    urls=DisUrls(spider=spider_name,url=star_url)
    dbs=MongoDB(db=spider_name)
    #线程调度方式一
    for x in range(5):
        t=Thread(target=tt,args=(urls,dbs))
        t.start()
    t.join()
    #线程调度方式二
'''    while True:
        #pool.apply_async(options,args=(urls,dbs))
        t=Thread(target=options,args=(urls,dbs))
        t.start()
        #设置爬虫结束条件
        for x in range(3):
            if len(urls)!=0:
                break
            time.sleep(3)
        if len(urls)==0:
            break
    #pool.close()
    #pool.join()'''
    