from flask import Flask,request,Response,jsonify,render_template,abort
import json
import pandas as pd
from flask_cors import CORS
import os
import re

pattern=re.compile(r'\W*',flags=re.UNICODE)

app=Flask(
    __name__,static_folder='./source/static\\',template_folder='./source/templates\\'
)
CORS(app,supports_credentials=True)

@app.route('/')
def hello_world():
    # return 'Hello, my dear guest!'
    return render_template('./index.html')

@app.route('/search',methods=['POST'])
def search():
    course = re.sub(pattern, '', request.json['course'])
    # unit=request.json['unit'].replace('\\','').replace('/','').replace('\xa0',' ')
    unit = re.sub(pattern, '', request.json['unit'])
    problems=request.json['problems']
    query=pd.DataFrame(problems)
    # for i in range(len(query)):
    #     query.iloc[i, 0] = ''.join(query.iloc[i, 0].split())
    # print(len(query))
    print('接收到'+str(len(query))+'个题目')
    answers=pd.read_json('./source/scrap_results/'+course+'/'+str(unit)+'.json',encoding='utf-8')
    res_answer=pd.merge(query, answers,how='inner',on='caption')
    res_answer=res_answer.to_json('answer.json',orient='records',force_ascii=False)
    # print('get an search request')
    return jsonify(res_answer)

@app.route('/result',methods=['GET'])
def show_result():
    if not os.path.exists('answer.json'):
        abort(401)
    results=pd.read_json('answer.json',orient='records',encoding='utf-8',dtype=list)
    # results=result.values.tolist()
    res_result=[]
    for i in range(len(results)):
        res={}
        res['caption']=results.iloc[i,0]
        # res['answer'] = results.iloc[i, 1].replace('spans', 'span s').replace('imgs','img s')
        res['answer'] = results.iloc[i, 1]
        res['analysis']=results.iloc[i,2]
        res_result.append(res)
    # print(result)
    os.remove('answer.json')
    return render_template('search_result.html',questions=res_result)
    
@app.errorhandler(401)
def page_error(error):
    # 返回元组,若没有第二个401,则默认为200
    # return render_template('error.html', error_info=error), 401
    return "尚未对该门课程或该章节进行爬取,或者需要重新运行页面脚本",401

if __name__=='__main__':
    app.run(debug=True,host='localhost',port='80')
