import os
import re
import bs4
import time
import datetime
import urllib.request  
from bs4 import BeautifulSoup  
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

 
class download_documents(object):
    
    def __init__(self,url,save_file_name):
        self.url = url
        self.save_file_name = save_file_name
        self.error = "" 

    def save_error(self):
        with open('./logs.txt','a+',encoding='utf-8') as fn:
            fn.write(self.error)
            fn.close() 
        
    def get_document_names(self):      
        
        html = urllib.request.urlopen(self.url)  
        content = html.read()  
        html.close()
        print("已获得该页面!")
        soup = BeautifulSoup(content, "lxml")
        print("页面解析完毕！ ")        
        document_lst = soup.find_all('a', class_="short_name")
        print("当前页 疑似找到[%d]个文档\n"% len(document_lst))
        for i in document_lst: 
            print("%s\t"%i)
        print("\n")
        dir_nums = 0
        list_nums = 0
        #document_names = filter(lambda x : x.rfind('.')>0, [document.string for document in document_lst] )  # 过滤掉目录文件夹
        document_names = []
        for doc in document_lst:
            if(doc.string.rfind('.') > 0):
                document_names.append(doc.string)
                print("筛选出文档: %s"%(doc.string))
        print("-"*12)
        dir_nums = len(document_lst) - len(document_names)  # 计算目录数,用于后面的滚动条下拉判断
        list_nums = len(document_lst)  
                                
        return (document_names,dir_nums,list_nums)
    
    def get_documents(self):
        #设置Chrome浏览器，并启动
        chrome_options = webdriver.ChromeOptions()
        # 不加载图片(提升加载速度)；设置默认保存文件径路
        prefs = {"profile.managed_default_content_settings.images":2,\
                 "download.default_directory": '%s' %self.save_file_name}
        chrome_options.add_experimental_option("prefs",prefs)
        browser = webdriver.Chrome(options=chrome_options) #启动浏览器
        print("浏览器已启动")
        (document_names,dir_nums,list_nums) = self.get_document_names()  #取得文档   目录
        browser.maximize_window() #窗口最大化
        browser.set_page_load_timeout(15) # 最大等待时间为30s
        
        #当加载时间超过30秒后，自动停止加载该页面
        try:
            browser.get(self.url)
        except TimeoutException:
            browser.execute_script('window.stop()')
       
         
        #遍历所有的tags,下载文档
        for i in range(list_nums ):  #len(document_names)):
            #当开始的12首歌下载完后，需要下拉网页内嵌的滚动条        
            if i >= 12:
                #找到网页内嵌的滚动条
                Drag = browser.find_element_by_class_name("jspDrag")
                #获取滚动槽的高度
                groove = browser.find_element_by_class_name("jspTrack")
                height_of_groove = int(re.sub("\D","",str(groove.get_attribute("style"))))
                #利用鼠标模拟拖动来下拉该滚动条
                move_of_y = (  i ) * height_of_groove/list_nums  #(  len(document_names) )  #每次下拉的滚动条的高度  # 待检测是否有Bug
                ActionChains(browser).drag_and_drop_by_offset(Drag, 0, move_of_y).perform() 
            
            elem_lst = browser.find_elements_by_class_name("short_name") #所有歌的tags
            elem= elem_lst[i]
            elem.click()  #点击该tag,切换到该文档的下载页面 5
            time.sleep(3)
            try:
                button = browser.find_element_by_id("download_big_btn") #按下下载按钮
            except NoSuchElementException:
                print("该文档不存在")
                browser.back()
                continue
            j = 0
            if dir_nums <= 0 :
                j = i
            else:
                j = i - dir_nums
            #print("i = %d j =%d docs_nums=%d dir_nums=%d "%(i,j,len(document_names),dir_nums))
            print("已找到第%d个文档: %s"%(j+1, document_names[j]))
            button.click()
            print("%s 正在下载中..."%document_names[j])
            file_exit_flg = len(os.listdir(r"%s"%self.save_file_name))
            time.sleep(6)#8
            #文档是否存在处理，如果存在，输出“下载成功”，否则等待15秒，再次判断后决定是否刷新页面            
            if len(os.listdir(r"%s"%self.save_file_name)) == file_exit_flg +1:
                print("%s 下载成功！\n"%document_names[j])
            else:
                exit_flag = 0 #退出标志，尝试下载5次，5次下载仍未成功后输出“下载失败!”
                while True:
                    time.sleep(5) #8

                    if len(os.listdir(r"%s"%self.save_file_name)) == file_exit_flg +1:
                        print("%s 下载成功！\n"%document_names[j])
                        break
                    print("%s 下载未成功，再次尝试下载！"%document_names[j])
                    browser.refresh() #等待15秒后，文件还未下载，则刷新网页
                    time.sleep(5)
                    print("已刷新网页！")
                    
                    #刷新网页后执行刚才的操作
                    button = browser.find_element_by_id("download_big_btn")
                    button.click()
                    print("%s 正在下载中..."%document_names[j])
                    file_exit_flg = len(os.listdir(r"%s"%self.save_file_name))
                    time.sleep(5) #8
                    exit_flag += 1
                    if exit_flag == 5:
                        print("%s 下载失败！\n========================\n"%document_names[j])
                        self.error = "at[%d]  %s 下载失败！\n Url: %s\n"%(i,document_names[j],self.url)
                        self.save_error()
                        break
                    
            browser.back() # 网页后退
            time.sleep(3) #8
    
        browser.close() #操作结束，关闭Chrome浏览器
        print("\n本页面操作已经结束!请前往下载位置(%s)查看下载文件.  Y(^O^)Y \n"% self.save_file_name)
        
        

def main():
    d1 = datetime.datetime.now()
    #下载文档的网页网址
    for pn in range(2,3):
        url = 'https://vdisk.weibo.com/s/d2rNCv_IVmawi?parents_ref=,d2rNCv_IVmawi&category_id=0&pn=2' 
        print("当前页面是:\n%s\n"%url)
        #保存文件的目录
        save_file_name = r"C:\Users\Administrator\Desktop\Huffman code"
        for_test = download_documents(url,save_file_name)
        try:
            for_test.get_documents()
        except TimeoutException:
            sum_of_files = len(os.listdir(save_file_name))
            print("下载超时啦！！！此次操作共下载了%d个文档(可能有重复或未下载完的)，到此就结束了哦 ^o^" % sum_of_files)
    d2 = datetime.datetime.now()
    print("开始时间：",d1)
    print("结束时间：",d2)
    print("一共用时：",d2-d1)
    
main()
