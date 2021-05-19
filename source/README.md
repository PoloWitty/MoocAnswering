***如非必要, 此文件夹内文件勿动***

## 本文件夹下文件说明

`scrap_results` 是爬取的数据, 以json的格式存储

`static` 是flask加载主界面时需要的静态文件(js,css,图片之类的)

`templetes` 是flask渲染页面用的

`client.py` 是之前对服务器发POST做测试用的

`mooc_scraping.py` 是爬虫的主程序, 如果要爬取更多的数据就要修改这个文件

## 爬虫程序的dependency

- playwright
- bs4
- pandas

看懂代码之后, 开始爬取之前先要`playwright open --save-storage=auth.json www.icourse163.org` 用来生成登录mooc用的cookie等header, 不然没办法登录mooc看往年的题目