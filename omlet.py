#v1.1
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import requests
import os

#个人页网址
profile = 'https://omlet.gg/profile/snow_walker030'
#贴文存储的名称
saveFile = 'post01.json'
#总文件夹
dataFolder = '../omlet_res/'

first = 1   #从第几个贴文开始
last = -1   #获取到第几个贴文（-1代表到完）
continuable = True  #是否沿用旧的linkArr

#
#
#
#

#Func--下载图片（.omlet_res/img/IMG_ID.png）
def download_img(url:str):
    req = requests.get(url)
    with open(url.replace('https://blobs.omlet.gg/blob/',dataFolder+'img/',1)+'.png','wb') as f:
        f.write(req.content)
        f.close()

#Func--下载mod（.omlet_res/mod/MOD_ID.zip）
def download_mod(url:str):
    req = requests.get(url)
    with open(url.replace('https://blobs.omlet.gg/blob/',dataFolder+'mod/',1)+'.zip','wb') as f:
        f.write(req.content)
        f.close()

#Func--创建文件夹
def createDir(path):
    if not os.path.exists(dataFolder+path):
        os.makedirs(dataFolder+path)
        print('已创建：',dataFolder+path)

#建立文件夹（img,mod,video）
createDir('img')
createDir('mod')
createDir('video')

#构建浏览器（Chrome）
chromeOpt = webdriver.ChromeOptions()
chromeOpt.add_argument('--ignore-certificate-errors')
driver = webdriver.Chrome(options=chromeOpt)

linkArr = []
postArr = []
videoPost = ''

#读取旧linkArr.json
if os.path.exists(dataFolder+'linkArr.json') and continuable:
    with open(dataFolder+'linkArr.json') as f:
        linkArr = json.load(f)
        f.close()
else:
    #打开个人页
    driver.get(profile)
    time.sleep(1)

    #滑到底部
    while driver.execute_script('return document.body.scrollHeight - window.scrollY > 800'):
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        time.sleep(1.5)

    #获取贴文HTML<a> linkHTML[]
    linkHTML = driver.find_elements(By.CSS_SELECTOR,'.post-details.clamp.clamp-one-line a:first-child')

    #获取<a>的href linkArr[]
    for link in linkHTML:
        linkArr.append(link.get_property('href'))

    #写入linkArr.json
    with open(dataFolder+'linkArr.json','w') as f:
        json.dump(linkArr,f,ensure_ascii=False,indent=2)
        f.close()

if last == -1 or first > last or last > len(linkArr):
    last = len(linkArr)

print('\n--START CRAWLING--\n贴文数量：',last-first+1,'\n')#-------------------------

index = first
# try:
for ln in linkArr[first-1:last]:
    #sto,vid,pho,qui,mod,pos
    postType = ln[17:20]
    print('\n[ ',str(index),' ]',postType)#-----------------------

    #打开贴文
    driver.get(ln)
    time.sleep(1)

    #检测【更多留言】按钮，有则点击
    try:
        driver.find_element(By.CSS_SELECTOR,'div.view-more-btn__sortable-comment-list__3gZtX')
    except:
        ()
    else:
        driver.execute_script(
            "arguments[0].click();",
            driver.find_element(By.CSS_SELECTOR,'div.view-more-btn__sortable-comment-list__3gZtX')
        )
        time.sleep(1)

    #获取发帖时间、标题、html内容
    date = driver.find_element(By.CSS_SELECTOR,'div.post-details a').get_property('innerHTML')
    title = driver.find_element(By.CSS_SELECTOR,'div.large-post-content h2').get_property('innerHTML')
    content = driver.find_element(By.CLASS_NAME,'large-post-content').get_property('innerHTML')
    print(title)

    #如果发现图片，则遍历下载
    if driver.find_elements(By.CSS_SELECTOR,'div.large-post-content img[src^="https://blobs.omlet.gg/blob/"]'):
        for img in driver.find_elements(By.CSS_SELECTOR,'div.large-post-content img[src^="https://blobs.omlet.gg/blob/"]'):
            #下载图片
            download_img(img.get_property('src'))

    #确认是不是mod贴文
    if postType == 'mod':
        mod_btn = driver.find_element(By.CSS_SELECTOR,'.inner-post-container a[href^="https://blobs.omlet.gg/blob/"]')
        content += mod_btn.get_property('outerHTML')
        download_mod(mod_btn.get_property('href'))

    #如果发现视频，记录起来（txt）
    if driver.find_elements(By.CSS_SELECTOR,'div.large-post-content video[src]'):
        videoPost += ln + '\n'

    #存储留言 commentLs[{留言1},{留言2},{留言3}]
    commentLs = []
    for comment in driver.find_elements(By.CSS_SELECTOR,'div.main__comment__2hRkJ'):
        userText = comment.find_element(By.CLASS_NAME,'username-text').get_property('innerHTML')                #留言者
        cmtDate = comment.find_element(By.CLASS_NAME,'timestamp__comment__Nntm9').get_property('innerHTML')     #留言时间
        try:
            cmtContent = comment.find_element(By.CLASS_NAME,'text-body__comment__2LGUq').get_property('innerText')  #留言内容
        except:
            #如果不是文字，则记录<img>
            img = comment.find_element(By.CSS_SELECTOR,'img[src^="https://blobs.omlet.gg/blob/"]')
            cmtContent = img.get_property('outerHTML')
            #下载图片
            download_img(img.get_property('src'))

        commentLs.append({
            'user':userText,
            'Date':cmtDate,
            'content':cmtContent
        })
    #存储贴文 postArr[{贴文1},{贴文2},{贴文3}]
    postArr.append({
        'href':ln,
        'title':title,
        'date':date,
        'content':content,
        'comment':commentLs
    })
    #下一篇贴文
    index += 1

#关闭浏览器
driver.close()
# except:
#     #出错时存储
#     print('\n伺服器出错，即将储存第 {} 至 {} 篇贴文...'.format(first,index-1))

#写入贴文json
with open(dataFolder+saveFile,'a',encoding='utf-8') as f:
    json.dump(postArr,f,ensure_ascii=False,indent=2)
    f.close()

#记录带视频的贴文
with open(dataFolder+'videoLs.txt','a') as f:
    f.write(videoPost)
    f.close()

#运行结束
print('成功储存 {} 篇贴文'.format(index-first))
