# import thulac
import pandas as pd
import re
from tqdm import tqdm
from collections import defaultdict
import logging
import os
import time
import pyttsx3
import pynlpir  # 引入依赖包
pynlpir.open()  # 打开分词器
pynlpir.nlpir.ImportUserDict(b"user_dict_xiehe-our.csv")
engine = pyttsx3.init()  # 创建engine并初始化


# 功能：对输入的语料库进行情感词汇识别，输出语料库的领域情感词典
def get_logger(log_dir, name, log_filename='info_senti_relu.log', level=logging.INFO):
    try:
        os.makedirs(log_dir)
    except OSError:
        pass

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not logger.handlers:  # 避免重复日志
        # Add file handler
        file_handler = logging.FileHandler(os.path.join(log_dir, log_filename), mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info('Log directory: %s', log_dir)
    return logger


# 计算语料库的种子词汇
def construct_lexicon(comment):
    ngrams = defaultdict(int)
    for j, t in enumerate(comment):
        t_cut = cut_word_in[t]
        for i, m in enumerate(t_cut):
            ngrams[m[0]] += 1
    ngrams = {i: j for i, j in ngrams.items()}
    total = 1. * sum([j for i, j in ngrams.items()])
    x = round(total / len(ngrams), 1)
    return ngrams, x


# 计算情感权重
def cal_weight(word_senti2, ngrams, x):
    for w, q in word_senti2.items():
        p = q[0]
        n = q[1]
        if ngrams[w] > x:
            weight = (p - n) / ngrams[w]
            if abs(weight) >= 0.3:
                word_weight[w] = weight
                add_word.append(w)


# step1:根据分句内的词汇位置构造词典
def get_senti_word_in(word_senti, comment, cha, ngrams, ave):
    for t_cut in comment.values():
        p = 0
        n = 0
        nn = 0  # 否定词数量
        start = 0  # 情感词汇前的否定词范围
        f = 0  # 判断某情感词汇前面的情感词汇位置
        s_word = []
        g = 1
        for i in t_cut:
            if i[1] in cha and i[0] not in word_weight.keys():
                g = 0
        if g == 0:
            for i, m in enumerate(t_cut):
                if m[0] in word_weight.keys():
                    s_word.append(m[0])
                    if i - f > 3:
                        start = i - 3
                    elif i - f <= 3:
                        start = f
                    f = i
                    for k in range(start, i):
                        if t_cut[k][0] in not_lexi:
                            nn += 1  # 确定词汇前后有几个否定词使得情感发生转变；进一步改进：否定词应该与情感词之间有较小的距离
                    if word_weight[m[0]] == 1:
                        if nn % 2 == 0:
                            p += 1
                        elif nn % 2 == 1:
                            n += 1
                    elif word_weight[m[0]] == -1:
                        if nn % 2 == 0:
                            n += 1
                        elif nn % 2 == 1:
                            p += 1
            for i in t_cut:
                if i[1] in cha and i[0] not in s_word and p+n != 0:
                # if i[0] not in s_word:
                    if i[0] in word_senti.keys():
                        word_senti[i[0]][0] += p
                        word_senti[i[0]][1] += n
                    else:
                        word_senti[i[0]] = [p, n]
    cal_weight(word_senti, ngrams, ave)
    return word_senti


# step2：确定所有数据中带有情感词的句子的情感倾向（拥有分句的）
def get_sentence_senti(commen, number):
    if number == 1:
        for c in commen:
            if len(c) != 1:
                senti = {}
                for j, t in enumerate(c):
                    t_cut = cut_word_in[t]
                    senti[j] = 0
                    start = 0  # 情感词汇前的否定词范围
                    f = 0  # 判断某情感词汇前面的情感词汇位置
                    nn = 0  # 计算词汇前否定词数量
                    for i, m in enumerate(t_cut):
                        if m[0] in word_weight.keys():
                            if i - f > 3:
                                start = i - 3
                            elif i - f <= 3:
                                start = f
                            f = i
                            for k in range(start, i):
                                if t_cut[k][0] in not_lexi:
                                    nn += 1
                            if nn % 2 == 0:
                                senti[j] += word_weight[m[0]]
                            elif nn % 2 == 1:
                                senti[j] += -word_weight[m[0]]
                    sentence_senti[t] = senti[j]
    else:
        for c in commen:
            if len(c) != 1:
                senti = {}
                for j, t in enumerate(c):
                    t_cut = cut_word_in[t]
                    g = 1
                    for i, m in enumerate(t_cut):
                        if m[0] in add_word:
                            g = 0
                    if g == 0:
                        senti[j] = 0
                        start = 0  # 情感词汇前的否定词范围
                        f = 0  # 判断某情感词汇前面的情感词汇位置
                        nn = 0  # 计算词汇前否定词数量
                        for i, m in enumerate(t_cut):
                            if m[0] in word_weight.keys():
                                if i - f > 3:
                                    start = i - 3
                                elif i - f <= 3:
                                    start = f
                                f = i
                                for k in range(start, i):
                                    if t_cut[k][0] in not_lexi:
                                        nn += 1
                                if nn % 2 == 0:
                                    senti[j] += word_weight[m[0]]
                                elif nn % 2 == 1:
                                    senti[j] += -word_weight[m[0]]
                        sentence_senti[t] = senti[j]


# step3:根据分句情感判断词汇情感
def get_senti_word_between(commen2, cha, ngrams, word_senti, ave):
    for c in commen2:
        if len(c) > 1:
            for j, t in enumerate(c):
                score = sentence_senti[t]
                f = 0  # 判断某情感词汇前面的情感词汇位置
                nn = 0  # 计算词汇前否定词数量
                g = 1
                t_cut = cut_word_in[t]
                for i in t_cut:
                    if i[0] not in word_senti.keys():
                        g = 0
                if g == 0 and score == 0:
                    if j > 0:
                        if t_cut[0][0] == 'TR':
                            f_score = -sentence_senti[c[j-1]]
                        else:
                            f_score = sentence_senti[c[j-1]]
                    else:
                        f_score = 0
                    if j < len(c) - 1:
                        b_cut = cut_word_in[c[j+1]]
                        if b_cut[0][0] == 'TR':
                            b_score = -sentence_senti[c[j + 1]]
                        else:
                            b_score = sentence_senti[c[j + 1]]
                    else:
                        b_score = 0
                    if f_score + b_score != 0:
                        for i, m in enumerate(t_cut):
                            if i - f > 3:
                                start = i - 3
                            else:
                                start = f
                            for k in range(start, i):
                                if t_cut[k][0] in not_lexi:
                                    nn += 1
                            if b_score >= 0 and f_score >= 0:
                                sentence_senti[t] = 1
                                if m[0] not in word_weight.keys() and m[1] in cha:
                                    if nn % 2 == 0:
                                        if m[0] in word_senti.keys():
                                            word_senti[m[0]][0] += 1
                                        else:
                                            word_senti[m[0]] = [1, 0]
                                    else:
                                        if m[0] in word_senti.keys():
                                            word_senti[m[0]][1] += 1
                                        else:
                                            word_senti[m[0]] = [0, 1]
                            elif b_score <= 0 and f_score <= 0:
                                sentence_senti[t] = -1
                                if m[0] not in word_weight.keys() and m[1] in cha:
                                    if nn % 2 == 0:
                                        if m[0] in word_senti.keys():
                                            word_senti[m[0]][1] += 1
                                        else:
                                            word_senti[m[0]] = [0, 1]
                                    else:
                                        if m[0] in word_senti.keys():
                                            word_senti[m[0]][0] += 1
                                        else:
                                            word_senti[m[0]] = [1, 0]
    cal_weight(word_senti, ngrams, ave)
    return word_senti


def main():
    # data = pd.read_excel("E:\\爬虫任务\\微博爬虫\\郑州暴雨数据\\郑州暴雨_微博数据.xlsx")
    #data = pd.read_csv(r'C:\Users\guy gao\PycharmProjects\dictionary embedding\online_shopping_10_cats\hotel_data.csv', sep=';')
    #data = pd.read_csv('movie_comment.csv', encoding='utf-8')
    data = pd.read_csv('listen_events1.csv', sep=',')
    input_data = data['评论内容'].fillna('').astype(str)  # 处理空值并转换为字符串
    #input_data = data['review']
    #input_data = data['CONTENT']
    stop_words = pd.read_csv('字典配置/stop_words.txt')
    stopwords = stop_words['word'].tolist()
    adv_lexicon = pd.read_csv('字典配置/adv.txt', sep=',')
    adv_lexi = adv_lexicon['word'].tolist()
    # 构建该领域的积极-消极情感词典
    # 给句子打上标记，分隔符号表示为\，否定词表示为NOT，转折词表示为TR，每个词汇记录其在句子中的位置
    r = "[_. !$%^@#￥%&*《》<>「」{}【】()/]"
    in_data = []
    bet_data = []
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
                elif s[0] in stopwords or s[0] in adv_lexi or s[0] == 'END':
                    b = b.replace(s[0], '', 1)
                else:
                    cut.append(s)
            if b != '':
                cut_word_in[b] = cut
                bet_data2.append(b)
                in_data.append(b)
        bet_data.append(bet_data2)
        # for s in re.findall(u'[\u4e00-\u9fa50-9a-zA-Z]+', sentence):
        #     in_data.append(s)
    len_all = 0
    ngrams, ave = construct_lexicon(in_data)
    character = ['uw', 'a']
    logger.info('data: hotel_data-our')
    logger.info('character:%s', character)
    logger.info('join-lexicon threshold value:%s', 0.3)
    # word_senti1 = {}
    num = 0
    while len(word_weight) - len_all != 0:
        num += 1
        len_all = len(word_weight)
        word_senti1 = {}
        # word_senti1 = get_senti_word_in(word_senti1, in_data, stable_pos, stable_neg, character, ngrams, ave)
        word_senti1 = get_senti_word_in(word_senti1, cut_word_in, character, ngrams, ave)
        get_sentence_senti(bet_data, num)
        add_word = []
        word_senti1 = get_senti_word_between(bet_data, character, ngrams, word_senti1, ave)
        logger.info('循环次数:%s', num)
    new_dict = {key: val for key, val in word_weight.items() if val != 0}
    word_dict = pd.DataFrame.from_dict(new_dict, orient='index', columns=['weight'])
    word_dict = word_dict.reset_index().rename(columns={'index': 'word'})
    word_dict.to_csv('word_dict_xiehe-our.csv', sep=';', index=False)


time_start = time.time()
# 加载转折词典和否定词典
turn_lexicon = pd.read_csv('字典配置/turn.txt')
turn_lexi = turn_lexicon['word'].tolist()
not_lexicon = pd.read_csv('字典配置/not.txt')
not_lexi = not_lexicon['word'].tolist()
# 加载stable_word词典
s_neg = pd.read_csv('字典配置/stable_neg.csv', sep=';')
stable_neg = s_neg['word'].tolist()
s_pos = pd.read_csv('字典配置/stable_pos.csv', sep=';')
stable_pos = s_pos['word'].tolist()
sentence_senti = {}
word_weight = {}
for e in stable_pos:
    e = re.sub(' ', '', e)
    word_weight[e] = 1
for d in stable_neg:
    d = re.sub(' ', '', d)
    word_weight[d] = -1
add_word = []
cut_word_in = {}
logger = get_logger('log', 'main')
main()
time_end = time.time()
time_sum = time_end - time_start  # 计算的时间差为程序的执行时间，单位为秒/s
logger.info('len time: %s', time_sum)
engine.say("代码结束")
#engine.runAndWait()  # 等待语音播报完毕
pynlpir.close()
