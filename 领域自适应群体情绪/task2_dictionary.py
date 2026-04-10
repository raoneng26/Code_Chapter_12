# -*- coding: utf-8 -*-
from ipaddress import ip_address
import xlrd
import re
# import urllib
import csv
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
from snownlp import SnowNLP

import os
import pyttsx3
import pynlpir  # 引入依赖包
pynlpir.open()  # 打开分词器
from snownlp import SnowNLP
pynlpir.nlpir.ImportUserDict(b"user_dict_xiehe-our.csv")
engine = pyttsx3.init()  # 创建engine并初始化
sentence_senti = {}
sentence_score = []
sentence_score_word=[]
turn_lexicon = pd.read_csv('字典配置/turn.txt')
turn_lexi = turn_lexicon['word'].tolist()
not_lexicon = pd.read_csv('字典配置/not.txt')
not_lexi = not_lexicon['word'].tolist()
adv_lexicon = pd.read_csv('字典配置/adv.txt', sep=',')
adv_lexi = {adv_lexicon['word'][i]: adv_lexicon['score'][i] for i in range(len(adv_lexicon['word']))}
# stop_lexicon = pd.read_csv('cn_stopwords.txt')
stop_lexicon = pd.read_csv('字典配置/stop_words.txt')
stop_words = stop_lexicon['word'].tolist()
word_dict = {}
cut_word = {}


# step2：确定所有数据中带有情感词的句子的情感倾向（拥有分句的）
def get_senti_score(commen):
    for c in tqdm(commen):
        senti = {}
        if len(c) != 0:
            for j, t in enumerate(c):
                t_cut = cut_word[t]
                senti[j] = 0  # 分句情感
                start = 0  # 情感词汇前的否定词范围
                f = 0  # 判断某情感词汇前面的情感词汇位置
                nn = 0  # 计算词汇前否定词数量
                w = 1  # 情感词汇权重
                for i, m in enumerate(t_cut):
                    if m[0] in word_dict:
                        if i - f > 3:
                            start = i - 3
                        elif i - f <= 3:
                            start = f
                        f = i
                        for k in range(start, i):
                            if t_cut[k][0] in not_lexi:
                                nn += 1
                            if t_cut[k][0] in adv_lexi:
                                w = adv_lexi[t_cut[k][0]]
                        if nn % 2 == 0:
                            senti[j] += word_dict[m[0]] * w
                        elif nn % 2 == 1:
                            senti[j] += (-word_dict[m[0]]) * w
                sentence_senti[t] = senti[j]


# step3:根据分句情感判断词汇情感
def get_score(commen2):
    for i, c in enumerate(commen2):
        s = 0
        lenth=0
        if len(c) != 0:
            for j, t in enumerate(c):
                # score = 0
                score = sentence_senti[t]
                t_cut = cut_word[t]
                if t_cut[0][0] == 'TR':
                    score = score * 2
                s += score
                lenth += len(t_cut)
        sentence_score.append(s)
        if lenth==0:
            sentence_score_word.append(lenth)
        else:
            k=s/lenth
            sentence_score_word.append(k)


def calculate_sentiment(file_name):
    if 'xlsx' in file_name:
        data = pd.read_excel(file_name)
    else:
        data = pd.read_csv(file_name, encoding='utf-8', sep=',')
    # 根据新词词典划分句子
    input_data = data['评论内容']
    #input_data = data['review']
    #input_data = data['CONTENT']
    #real_score = data['RATING']
    # 加载情感词典
    word_dict1 = pd.read_csv('word_dict_xiehe-our.csv', sep=';')
    for j in range(len(word_dict1)):
        word_dict[word_dict1['word'][j]] = word_dict1['weight'][j]
    # --------------------stable_lexicon-----------------
    pos_lexicon = pd.read_csv('字典配置/stable_pos.csv', sep=';')
    neg_lexicon = pd.read_csv('字典配置/stable_neg.csv', sep=';')

    # 给句子打上标记，分隔符号表示为\，否定词表示为NOT，转折词表示为TR，每个词汇记录其在句子中的位置
    pos_lexi = pos_lexicon['word'].tolist()
    neg_lexi = neg_lexicon['word'].tolist()
    for i in pos_lexi:
        i = re.sub(' ', '', i)
        if i not in word_dict.keys():
            word_dict[i] = 1
    for j in neg_lexi:
        j = re.sub(' ', '', j)
        if j not in word_dict.keys():
            word_dict[j] = -1

    r = "[_. !$%^@#￥%&*《》<>「」{}【】()/]"
    bet_data = []
    input_data = data['评论内容'].fillna('').astype(str) 
    for text in tqdm(input_data):
        sentence = re.sub(r, '', text)
        sentence = re.sub(r"(http|https|ftp):[a-zA-Z0-9.?/_&=:]*", '', sentence)
        bet_data1 = re.findall(u'[\u4e00-\u9fa50-9a-zA-Z]+', sentence)
        bet_data2 = []
        for b in bet_data1:
            b = b + 'END'
            s_cut = pynlpir.segment(b, pos_names=None)
            cut = []
            for s in s_cut:
                if s[0] in turn_lexi:
                    b = b.replace(s[0], 'TR', 1)
                    s = ('TR', 'z')
                    cut.append(s)
                elif s[0] in stop_words or s[0] == 'END':
                    b = b.replace(s[0], '', 1)
                else:
                    cut.append(s)
            if b != '':
                cut_word[b] = cut
                bet_data2.append(b)
        bet_data.append(bet_data2)
    get_senti_score(bet_data)
    get_score(bet_data)
    score_dic = []
    dic_score_dic = []
    dic_score_dic_word=[]
    max_score=max(sentence_score)
    min_score=min(sentence_score)
    for m in range(len(sentence_score)):
        if sentence_score[m] > 0:
            score_change1 = sentence_score[m] / max_score
            score_dic.append(score_change1)
            dic_score_dic.append(sentence_score[m])
        elif sentence_score[m] <= 0:
            score_change2 = sentence_score[m] / abs(min_score) if min_score != 0 else  sentence_score[m]
            score_dic.append(score_change2)
            dic_score_dic.append(sentence_score[m])

    max_score2 = max(sentence_score_word)
    min_score2 = min(sentence_score_word)
    for m in range(len(sentence_score_word)):
        if sentence_score_word[m] > 0:
            score_change3 = sentence_score_word[m] / max_score2
            dic_score_dic_word.append(score_change3)
        else:
            score_change4 = sentence_score_word[m] / abs(min_score2) if min_score2 != 0 else sentence_score_word[m]
            dic_score_dic_word.append(score_change4)
    


    output1 = {'sentence': input_data, 'score': score_dic, 'dic_score':dic_score_dic, 'word_socre':dic_score_dic_word}
    output = pd.DataFrame(data=output1)
    output.to_csv('output_score_dic.csv', sep=';', index=False)


def evaluates_senti(file_name):
    if 'xlsx' in file_name:
        data = pd.read_excel(file_name)
    else:
        data = pd.read_csv(file_name, encoding='utf-8', sep=',')
    data.loc[len(data)] = data.columns
    # data1 = data.drop_duplicates(subset=['标题'], keep='last', inplace=False)
    data1 = data.drop_duplicates(subset=['文本'], keep='last', inplace=False)
    data3=pd.read_csv('output_score_dic.csv', encoding='utf-8',  sep=';')
    socre2 = data3['score']
    sours = data['评论内容']
    if len(socre2) < len(data):
        # 使用 concat 将新值添加到 Series
        missing_length = len(data) - len(socre2)
        socre2 = pd.concat([socre2, pd.Series([0] * missing_length)], ignore_index=True)

    # print(len(data))
    # print(len(socre2))
    # print(len(sours))
    # title = data['标题']
    title = data['文本']
    post_time = data['评论时间']
    tag = data['标记']
    # comment_like = data['评论点赞数']
    # comment_num = data['sub_comment_count']
    # ip_address = data['评论属地']
    user_name = data['用户名']
    # gender = data['gender']
    # 平均值
    average_score1 = 0
    average_score2 = 0
    j = 0
    len0 = 0
    len1 = 0
    comment = ''
    with open('宏观集群平均情绪.csv', 'w+', errors='ignore', newline='', encoding='utf-8') as f1:
        with open('微观集群平均情绪.csv', 'w+', errors='ignore', newline='', encoding='utf-8') as f2:
            with open('error.csv', 'a', errors='ignore', newline='', encoding='utf-8') as f3:
                writer1 = csv.writer(f1, delimiter=';')
                writer2 = csv.writer(f2, delimiter=';')
                writer3 = csv.writer(f3, delimiter=';')
                writer3.writerow(['序号', '评论内容', '情绪分数'])
                # writer1.writerow(['文本', '实际爬取到的一级评论内容', '评论时间', '单条评论情绪值', '帖子平均情绪值', '评论点赞数', '评论数', '评论属地', '用户名', '性别'])
                writer1.writerow(['文本', '实际爬取到的一级评论内容', '评论时间', '用户名', '单条评论情绪值'])
                writer2.writerow(['一级评论', '实际爬取到的二级评论内容', '单条评论情绪值', '一级评论平均情绪值'])
                for i in range(0, len(sours)):
                    # try:
                        # sours[i] = ''.join(sours[i].split())  # 去除待情绪分析语料中的空格，防止情绪分析失败
                        # s = SnowNLP(sours[i])
                        # score = s.sentiments
                        # score = score * 2 - 1
                        score = socre2[i]
                        
                        # print(sours[i])
                        # print(score)
                        if tag[i] == 0:  # 计算帖子的一级评论平均情绪值
                            comment = sours[i]
                            if i <= data1.index[j]:
                                average_score1 += float(score)
                                len0 += 1
                                writer1.writerow([title[i], sours[i], post_time[i], user_name[i], score ])
                            elif i > data1.index[j]:
                                if len0 == 0:
                                    average_score1 = 0000000
                                else:
                                    average_score1 = average_score1 / len0
                                # writer1.writerow(['-------', '--------', '--------', '--------', average_score1])
                                writer1.writerow([title[i], sours[i], post_time[i], user_name[i], score])
                                average_score1 = float(score)
                                j += 1
                                len0 = 1
                        elif tag[i] == 1:  # 计算一级评论下二级评论的平均情绪值
                            len1 += 1
                            average_score2 += float(score)
                            writer2.writerow([comment, sours[i], score])
                            if tag[i + 1] != 1:
                                average_score2 = average_score2 / len1
                                writer2.writerow(['-------', '--------', '--------', average_score2])
                                average_score2 = 0
                                len1 = 0
                            else:
                                pass
                        else:
                            if len0 == 0:
                                average_score1 = 0000000
                            else:
                                average_score1 = average_score1 / len0
                            writer1.writerow(['-------', '--------', '--------', '--------', average_score1])
                    # except:
                        # writer3.writerow(sours[i])
                        # writer3.writerow(sours)
    print('task2 finish')


if __name__ == '__main__':
    # filename = input('请输入待处理的文件：')
    # filename = 'test.xlsx'
    filename = 'group_emotion1000\listen_events2.csv'


    calculate_sentiment(filename)
    evaluates_senti(filename)
