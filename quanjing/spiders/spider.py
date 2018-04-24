#!/usr/bin/env python
# encoding: utf-8
"""
@author: chenchuan@autohome.com.cn
@time: 2017/03/13
"""
import os
import random
import string

import scrapy
import requests
import urllib.request
import time

from bs4 import BeautifulSoup
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spiders import Spider
from quanjing.items import QuanjingItem
from quanjing.utils import Utils
from selenium import webdriver

domain = 'https://weibo.com'
dummy_domain = 'https://www.baidu.com'


# TODO http://www.cnblogs.com/zhonghuasong/p/5976003.html

def complete_url(_url):
    if not _url.startswith('http', 0, 4):
        _url = domain + _url
    return _url


class QuanjingSpider(Spider):
    name = 'quanjing_spider'
    website_possible_httpstatus_list = [200]
    headers = {  # User-Agent需要根据每个人的电脑来修改
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'weibo.com',
        'Pragma': 'no-cache',
        'Referer': 'https://weibo.com/u/3278620272?profile_ftype=1&is_all=1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    # 要爬取的账号的微博名称
    # 分2批抓取
    # person_site_names = ['210104261', 'converse1956', 'mount9882', 'u/1663232781', 'u/2302781822', 'u/2670774690',
    #                      'u/2765721850', 'u/5478684865']
    person_site_names = ['u/5634198551', 'u/5669048366', 'u/5789602782', 'u/5930221915',
                         'u/6017601387', 'u/6136830353', 'zhangxiqiao']
    max_page_cnt = 10
    # 上线请注释
    # person_site_names = ['u/6017601387']
    # max_page_cnt = 5

    request_params = {"ajwvr": "6", "domain": "100505", "domain_op": "100505", "feed_type": "0", "is_all": "1"}
    profile_request_params = {"profile_ftype": "1", "is_all": "1"}
    request_url = domain + "/p/aj/v6/mblog/mbloglist?"
    title = "u5168u666fu56feu7247"  # 标题字符串：全景图片

    cookie_save_file = "cookie.txt"  # 存cookie的文件名
    cookie_update_time_file = "cookie_timestamp.txt"  # 存cookie时间戳的文件名
    weibo_url = "https://weibo.com/"

    username = "" # 你的微博账号
    password = "" # 你的微博密码

    def start_requests(self):
        result = self.is_valid_cookie()
        if not result:
            # driver = webdriver.Chrome("D:\work\kuaxian3.5\Python\image_crawler-master\SinaWeibo\chromedriver.exe")  # 打开Chrome
            driver = webdriver.Chrome(
                "/usr/bin/chromedriver")  # 打开Chrome
            driver.maximize_window()  # 将浏览器最大化显示
            driver.get(self.weibo_url)  # 打开微博登录页面
            time.sleep(5)  # 因为加载页面需要时间，所以这里延时10s来确保页面已加载完毕
            cookies = self.get_cookies(driver)
            self.save_cookie(cookies)
            self.update_cookie_time(Utils.get_timestamp())
        else:
            cookies = self.get_cookie_from_txt()

        self.headers["Cookie"] = cookies
        all_panorama_dict = {}
        for person_site_name in self.person_site_names:
            max_page_cnt = self.max_page_cnt + 1
            for x in range(1, max_page_cnt):
            # 上线请注释
            # for x in range(5, max_page_cnt):
                if x == max_page_cnt:
                    break
                self.headers["Cookie"] = cookies
                profile_html = self.get_top_weibo(person_site_name, x)
                start_pos = profile_html.find("from=page_100505")
                weibo_id = profile_html[start_pos + 16:start_pos + 26]
                panorama_dict = self.get_panorama_dict(profile_html)
                additional_panorama_dicts = {}

                for y in range(0, 2):  # 有两次下滑加载更多的操作
                    time.sleep(5)
                    profile_html = self.get_weibo(weibo_id, person_site_name, y, x)
                    if x == 1 and y == 1:
                        max_page_cnt = self.get_max_page_cnt(profile_html) + 1
                    tmp_dict = additional_panorama_dicts.copy()
                    tmp_dict.update(self.get_panorama_dict(profile_html))
                    additional_panorama_dicts = tmp_dict.copy()
                tmp_dict = all_panorama_dict.copy()
                tmp_dict.update(panorama_dict)
                tmp_dict.update(additional_panorama_dicts)
                all_panorama_dict = tmp_dict
        yield Request(url=dummy_domain, callback=self.parse_item,
                      meta={"all_panorama_dict": all_panorama_dict})

    def parse_item(self, response):
        all_panorama_dict = response.meta["all_panorama_dict"]
        for panorama in all_panorama_dict:
            item = QuanjingItem()
            item['oid'] = panorama.split('/')[-1]
            item['content'] = all_panorama_dict[panorama]
            yield item

    def get_cookies(self, driver):  # 登录获取cookies
        driver.find_element_by_name("username").send_keys(self.username)  # 输入用户名
        driver.find_element_by_name("password").send_keys(self.password)  # 输入密码
        driver.find_element_by_xpath("//a[@node-type='submitBtn']").click()  # 点击登录按钮
        cookies = driver.get_cookies()  # 获取cookies
        cookie = ""
        # 将返回的Cookies数组转成微博需要的cookie格式
        for x in range(len(cookies)):
            value = cookies[x]['name'] + "=" + cookies[x]['value'] + ";"
            cookie = cookie + value
        return cookie

    def save_cookie(self, cookie):  # 把cookie存到本地
        try:
            f = open(self.cookie_save_file, 'w')
            f.write(cookie)
            f.close()
        except Exception as e:
            print(e)
        finally:
            pass

    def get_cookie_from_txt(self):  # 从本地文件里读取cookie
        f = open(self.cookie_save_file)
        cookie = f.read()
        return cookie

    def update_cookie_time(self, timestamp):  # 把cookie存到本地
        try:
            f = open(self.cookie_update_time_file, 'w')
            f.write(timestamp)
            f.write('\n')
            f.close()
        except Exception as e:
            print(e)
        finally:
            pass

    def get_cookie_update_time(self):  # 获取上一次cookie更新时间
        try:
            f = open(self.cookie_update_time_file)
            lines = f.readlines()
            cookie_update_time = lines[0]
            return cookie_update_time
        except Exception as e:
            print(e)
        finally:
            pass

    def is_valid_cookie(self):  # 判断cookie是否有效
        if not os.path.isfile(self.cookie_update_time_file):
            return False
        else:
            f = open(self.cookie_update_time_file)
            lines = f.readlines()
            if len(lines) == 0:
                return False
            else:
                last_time_stamp = self.get_cookie_update_time()
                if int(Utils.get_timestamp()) - int(last_time_stamp) > 6 * 60 * 60 * 1000:
                    return False
                else:
                    return True

    def get_top_weibo(self, person_site_name, page):  # 每一页顶部微博
        try:
            profile_url = self.weibo_url + person_site_name + "?"
            self.profile_request_params["page"] = page
            response = requests.get(profile_url, headers=self.headers, params=self.profile_request_params, verify=False)
            html = response.text.encode('raw_unicode_escape')
            soup = BeautifulSoup(html, "html.parser")
            script_list = soup.find_all("script")
            script_size = len(script_list)
            tag = 0
            for x in range(script_size):
                if "WB_feed WB_feed_v3 WB_feed_v4" in str(script_list[x]):
                    tag = x
            html_start = str(script_list[tag]).find("<div")
            html_end = str(script_list[tag]).rfind("div>")
            return str(str(script_list[tag].encode('raw_unicode_escape')[html_start:html_end + 4]))
        except Exception as e:
            print(e)
        finally:
            pass

    def get_weibo(self, weibo_id, person_site_name, pagebar, page):  # 通过微博ID和cookie来调取接口
        try:
            self.headers['Referer'] = self.weibo_url + person_site_name + "?profile_ftype=1&is_all=1"
            self.request_params["__rnd"] = Utils.get_timestamp()
            self.request_params["page"] = page
            self.request_params["pre_page"] = page
            self.request_params["pagebar"] = pagebar
            self.request_params["id"] = "100505" + weibo_id
            self.request_params["script_uri"] = "/" + person_site_name
            self.request_params["pl_name"] = "Pl_Official_MyProfileFeed__21"
            self.request_params["profile_ftype"] = 1
            response = requests.get(self.request_url, headers=self.headers, params=self.request_params, verify=False)
            html = response.json()["data"].replace("\t", "")
            html_start = html.find("<div")
            return str(str(html.encode('raw_unicode_escape'))[html_start:])
        except Exception as e:
            print(e)
        finally:
            pass

    def get_panorama_dict(self, html):  # 从返回的html格式的字符串中获取全景图片
        try:
            panorama_url_dict = {}
            result_html = html.replace("\\", "")
            soup = BeautifulSoup(result_html, "html.parser")
            div_list = soup.find_all("div", "WB_text W_f14")
            for x in range(len(div_list)):
                panorama_list = div_list[x].find_all("a")
                for y in range(len(panorama_list)):
                    title_in_html = panorama_list[y].get("title")
                    if title_in_html is not None:
                        if str(title_in_html.encode('raw_unicode_escape')).replace("\\", "").find(self.title) != -1:
                            for div_content in div_list[x].stripped_strings:
                                div_content = div_content[1:].strip().replace("u", "\\u")
                                div_content = Utils.trim_spec_char(div_content)
                                panorama_url_dict[panorama_list[y].get("href")] = div_content
                                break
            return panorama_url_dict
        except Exception as e:
            print(e)
        finally:
            pass

    def get_max_page_cnt(self, html):  # 从返回的html格式的字符串中获取最大页码
        try:
            result_html = html.replace("\\", "")
            html_start = result_html.find("u7b2c&nbsp;")
            html_end = result_html.find("&nbsp;u9875")
            return int(result_html[html_start + 11:html_end])
        except Exception as e:
            print(e)
        finally:
            pass
