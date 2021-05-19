from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import re

# COURSE = "模拟电子技术基础"
COURSES = ["电子线路设计、测试与实验（二）", '电子线路设计、测试与实验（一）', "模拟电子技术基础", '数字电子技术基础']
COURSES_PAGES=1 #总共有展示课的页面数(下面那个课程的小卡片有多少页)
SCRAP_TIMES=5#对每个单元爬取多少次
pattern=re.compile(r'\W*',flags=re.UNICODE)

def run(playwright):
    for COURSE in COURSES:
        course_dir=re.sub(pattern,'',COURSE)
        os.makedirs('./source/scrap_results/'+course_dir,exist_ok=True)
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="./source/auth.json")

        # Open new page
        page = context.new_page()

        # Go to https://www.icourse163.org/home.htm?userId=1395783954
        # page.goto("https://www.icourse163.org/home.htm?userId=1469066306")

        # Go to https://www.icourse163.org/home.htm?userId=1395783954#/home/course
        # page.goto("https://www.icourse163.org/home.htm?userId=1395783954&from=study&p=1")

        for i in range(COURSES_PAGES):
            page_str = "https://www.icourse163.org/home.htm?userId=1469066306&from=study&p=1#/home/course?userId=1395783954&from=study&p=" + \
                str(i+1)
            page.goto(page_str)
            page.wait_for_timeout(1000)
            soup = BeautifulSoup(page.content(), features='lxml')
            course_list = soup.find('div', class_='course-panel-body-wrapper').find_all("div", class_='course-card-wrapper')
            assert course_list != None

            link=None
            for course in course_list:
                box=course.find('div',class_='box')
                course_name=box.find('span',class_='text')
                if(course_name.string==COURSE):
                    link = box.find('a', attrs={'data-action': '课程tag-非新学期课程'})
                if link!=None:
                    break

            if link!=None:
                break                                    
        
        if link==None:
            print('请确保已加入之前的课程')
            exit(1)
        link = 'https://www.icourse163.org/'+link['href']

        assert link!=None
        
        page1=context.new_page()
        page1.goto(link)

        # Click text="测验与作业"
        page1.click("text=测验与作业")
        # page1.wait_for_load_state('load')
        page1.wait_for_timeout(3000)
        for time in range(SCRAP_TIMES):
            page1.wait_for_timeout(3000)
            soup1 = BeautifulSoup(page1.content(), features='lxml')
            units_list = soup1.find_all('div', class_='m-chapterQuizHwItem')
            for unit in units_list:
                # unit_name=unit.h4.string.replace('\\','').replace('/','')
                unit_name=re.sub(pattern,'',unit.h4.string)

                a = unit.find('a', class_='j-quizBtn u-btn u-btn-default f-fr') #找到这个单元对应的前往测验按钮

                #点击"前往测验"
                page1.click('a[id=\"'+str(a['id'])+'\"]')

                # Click text="开始测验"
                page1.wait_for_timeout(1000)
                # page1.wait_for_load_state('load')
                try:
                    page1.click("text=\"开始测验\"")
                except:
                    pass

                # Click text="提交答案"
                page1.wait_for_timeout(1000)
                page1.click("text=\"提交答案\"")

                # Click text="确定"
                # with page1.expect_navigation(url="https://www.icourse163.org/learn/HUST-481015?tid=1450249446#/learn/quizscore?id=1222237501&aid=2302533181"):
                with page1.expect_navigation():
                    page1.click("text=\"确定\"")
                
                #开始处理
                page1.wait_for_load_state('load')
                page1.wait_for_timeout(1000)
                soup2 = BeautifulSoup(page1.content(), features='lxml')
                problems = soup2.find_all('div', class_='m-choiceQuestion u-questionItem analysisMode')
                problems.append(soup2.find('div', class_='m-choiceQuestion u-questionItem analysisMode last'))
                problems.append(soup2.find('div',class_='m-choiceQuestion u-questionItem analysisMode first'))
                # assert problems!=None
                res_problems=[]
                for problem in problems:
                    res_problem={}

                    #找问题的题目
                    # problem_captions=problem.find('p')
                    # problem_captions=problem_captions.find_all('span')

                    problem_captions=problem.find('div',class_='qaDescription')
                    problem_captions=problem_captions.find_all('p')
                    res_caption=''
                    for problem_caption in problem_captions:
                        # for content in problem_caption.contents:
                            # res_caption += str(content)
                        res_caption+=problem_caption.text
                    # res_problem['caption']=res_caption
                    res_problem['caption']=''.join(res_caption.split())#处理一下\xa0的问题


                    # res_problem_caption=problem_captions.text
                    # # res_problem_caption=''
                    # # for problem_caption in problem_captions:
                    # #     # if problem_caption.string!=None:
                    # #     #     res_problem_caption+=problem_caption.string
                    # #     # else:
                    # #         # res_problem_caption+=problem_caption.contents[0]
                    # #     res_problem_caption+=problem_caption.text
                    # # res_problem_caption+=problem_captions.text
                    # # print(res_problem_caption)
                    # res_problem['caption']=''.join(res_problem_caption.split())#处理一下\xa0的问题

                    #找问题的答案选项
                    type=problem.find('div', class_='qaCate j-qacate f-fl')#题目类型
                    type=type.span['class'][0]
                    ans_choices=problem.find('span', class_='f-f0 tt2')
                    ans_choices=ans_choices.string
                    res_answer = ''
                    choice_list = problem.find_all('li', class_='f-cb')
                    if type=='duo' :#多选
                        for ans_choice in ans_choices:
                            if ord(ans_choice) < ord('A') or ord(ans_choice) > ord('Z'):
                                continue  # 处理多选的里面的那个句号(格式为"A,B")
                            ans_choice = ord(ans_choice)-ord('A')
                            answer = choice_list[ans_choice]
                            
                            answer = answer.find('p')
                            for content in answer.contents:
                                res_answer += str(content)
                            res_answer+=','
                    elif type=='dan' :#单选
                        ans_choice=ans_choices
                        ans_choice = ord(ans_choice)-ord('A')
                        answer = choice_list[ans_choice]

                        answer = answer.find('p')
                        for content in answer.contents:
                            res_answer+=str(content)

                    elif type=='pan' : #判断
                        ans_choice=ans_choices
                        ans_choice = ord(ans_choice)-ord('A')
                        answer = choice_list[ans_choice].find('span')
                        res_answer += answer['class'][0][7:]
                    else:
                        print(type)
                        exit(1)

                    res_problem['answer'] = ''.join(res_answer.split())

                    #找问题的解答
                    try:
                        res_analysis_info = problem.find('div', class_='analysisInfo answrong').contents[1]
                        # res_problem['analysis'] = ''.join(res_analysis_info.contents[1][4:].split())
                        res_analysis = ''
                        for content in res_analysis_info.contents:
                            res_analysis += str(content)
                        res_problem['analysis']=res_analysis
                    except:
                        res_problem['analysis'] = ''
                        pass
                        # print('problem:')
                        # print(problem)
                    # print('let show the res_answer')
                    # print(res_problem)
                    res_problems.append(res_problem)
                    # page1.wait_for_timeout(5000)
                    # fp.write(json.dumps(res_problems,ensure_ascii=False))
            
                try:
                    #新表就可以直接写
                    fp=open('./source/scrap_results/'+course_dir+'/'+unit_name+'.json','x',encoding='utf-8')
                    fp.write(json.dumps(res_problems, ensure_ascii=False))
                    fp.close()
                except:
                    #旧表就要做下数据的合并
                    old_table=pd.read_json('./source/scrap_results/'+course_dir+'/'+unit_name+'.json',encoding='utf-8')
                    # fp=open('./scrap_results/'+course_dir+'/'+unit_name+'.json','a+',encoding='utf-8')
                    # fp=open('./scrap_results/'+course_dir+'/'+unit_name+'.json','w',encoding='utf-8')
                    new_table=pd.DataFrame(res_problems)
                    new_table=pd.merge(old_table, new_table,how='outer')
                    new_table.to_json('./source/scrap_results/'+course_dir+'/'+unit_name+'.json',force_ascii=False,orient='records')
                

                # page1.wait_for_timeout(5000)
                # break
                # continue
                page1.wait_for_timeout(1000)
                page1.click('text=测验与作业')#返回单元列表处
                page1.wait_for_timeout(1000)


        # Close page
        page1.close()

        # Close page
        page.close()

        # ---------------------
        context.close()
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
