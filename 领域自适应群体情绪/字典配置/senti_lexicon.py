import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import re
import math
import pynlpir  # 引入依赖包
pynlpir.open()  # 打开分词器
pynlpir.nlpir.ImportUserDict(b"user_dict.csv")


# 功能：对于输入的语料库，提取新词结果，并将新词放入到用户词典中便于之后对评论进行分词
def cal_num(ngrams):
    num = defaultdict(int)
    for i, j in ngrams.items():
        num[j] += 1
    return num


def texts(input_data):
    texts_set = set()
    # 引入tqdm是为了显示进度
    for a in tqdm(input_data):
        # 检查是否为空或非字符串类型，进行转换或跳过
        if not isinstance(a, str):
            if pd.isna(a):  # 如果是空值，跳过
                continue
            a = str(a)  # 将非字符串类型转换为字符串
        if a.encode('utf-8') in texts_set:
            continue
        else:
            texts_set.add(a.encode('utf-8'))
            # 引入正则表达式re是为了预先去掉无意义字符（非中文、非英文、非数字）
            r = "[_. !$%^#￥%&*《》<>「」{}【】()/]"
            sentence = re.sub(r, '', a)
            for t in re.split(u'[^\u4e00-\u9fa50-9a-zA-Z]+', sentence):
                if t:
                    yield t


# 去除停用词后统计词汇，输入：评论数据 输出：[[['很快', 'd']], [['好吃', 'a']], [['味道', 'n'], ['足', 'd']], [['量', 'n'], ['大', 'a']]……]
def cal_word(in_data, stopwords):
    comment = list()
    sentence = list()
    for t in texts(in_data):
        sentence1 = ''
        t += 'END'
        for word in pynlpir.segment(t, pos_tagging=False):
            if word[0] not in list(stopwords):
                sentence1 += word[0]
        newlist = [word for word in pynlpir.segment(sentence1, pos_tagging=False) if word[0] not in list(stopwords)]
        comment.append(newlist)
        sentence.append(sentence1)
    return comment, sentence


# 统计词汇出现次数，输入：[[['很快', 'd']], [['好吃', 'a']], [['味道', 'n'], ['足', 'd']], [['量', 'n'], ['大', 'a']]……]
# 输出：{'很快': 131, '好吃': 175, '味道': 167, '
def construct_lexicon(n, comment):
    ngrams = defaultdict(int)
    for c in comment:
        for i in range(len(c)):
            words = ''
            for j in range(0, n):
                if i + j < len(c):
                    words += c[i + j][0]
                    if len(words) > n:
                        break
                    else:
                        ngrams[words] += 1
                else:
                    break
    ngrams = {i: j for i, j in ngrams.items()}
    return ngrams


# 计算分词之间的互信息，判断两个词汇是否能组成新的词汇
def new_word_find(ngrams, comment, total):
    ngrams_ = defaultdict(int)
    x = round(total / len(ngrams), 1)
    m = 2  # 窗口长度为2
    for c in tqdm(comment):
        if c:
            # c = pynlpir.segment(t)
            new_words = c[0][0]
        else:
            continue
        for i in range(len(c) - 1):
            s_words = c[i][0]
            if i + m - 1 < len(c) - 1:
                words = new_words + c[i + m - 1][0]
                if len(words) > 6:
                    if len(new_words) <= 6:
                        if s_words in new_words and s_words != new_words:
                            ngrams_[new_words] += 1
                    new_words = c[i+1][0]
                    continue
                if min(ngrams[words], ngrams[new_words], ngrams[c[i+1][0]]) > 3 * math.ceil(x):
                    deno = ngrams[new_words] * ngrams[c[i + m - 1][0]]
                    score = math.log2((total * ngrams[words]) / deno)
                    g = max(ngrams[new_words] / ngrams[c[i + 1][0]], ngrams[c[i + 1][0]] / ngrams[new_words])
                    g = math.ceil(g)
                    i_c = math.log2(total / ngrams[c[i + 1][0]])
                    i_n = math.log2(total / ngrams[new_words])
                    if g == 1:
                        min_proba = min(i_c, i_n) - 1
                    else:
                        min_proba = min(i_n, i_c) + math.log2((g - 1) / g)
                    # min_proba = 2
                    if score > min_proba:
                        new_words = new_words + c[i + m - 1][0]
                    else:
                        if s_words in new_words and s_words != new_words:
                            ngrams_[new_words] += 1
                        new_words = c[i + 1][0]
                else:
                    if s_words in new_words and s_words != new_words and ngrams[new_words] > 3 * math.ceil(x):
                        ngrams_[new_words] += 1
                    new_words = c[i + 1][0]

            else:
                if len(new_words) <= 6:
                    if s_words in new_words and s_words != new_words and ngrams[new_words] > 3 * math.ceil(x):
                        ngrams_[new_words] += 1
    return ngrams_


def main():
    # 提取微博文本内容
    # data = pd.read_excel("E:\\爬虫任务\\微博爬虫\\郑州暴雨数据\\郑州暴雨_微博数据.xlsx")
    #data = pd.read_csv(r'C:\Users\guy gao\PycharmProjects\dictionary embedding\online_shopping_10_cats\hotel_data.csv', sep=';')
    #data = pd.read_csv('movie_comment.csv',encoding='utf-8')
    data = pd.read_csv('listen_events1.csv', sep=',')
    input_data = data['评论内容']
    #input_data = data['CONTENT']
    all_word1 = pd.read_csv('字典配置/all_word.csv', sep=';')
    all_word = all_word1['word'].tolist()
    stop_words = pd.read_csv('字典配置/stop_words.txt')
    stopwords = stop_words['word'].tolist()
    # for i in range(2):
    word, sentence = cal_word(input_data, stopwords)
    n = 6
    ngrams = construct_lexicon(n, word)
    total = 1. * sum([j for i, j in ngrams.items()])  # 总字数
    print('----新词发现----')
    ngrams_ = new_word_find(ngrams, word, total)
    ngrams_ = {i: j for i, j in ngrams_.items()}
    new_lexicon = []
    keys = ngrams_.keys()
    y = round(total / len(ngrams), 1)
    x = 1
    # 将输出字典写入文件中
    for i, j in ngrams_.items():
        if i not in all_word and j > y:
            for k in keys:
                if i in k and i != k:
                    x = 0
            if x == 1:
                new_lexicon.append([i, 'uw'])
            x = 1
    new_word = pd.DataFrame(data=new_lexicon, columns=['word', 'label'])
    new_word.to_csv('new_word_xiehe-our.csv', sep='\t', columns=['word', 'label'], index=False)
    # 加载转折词典和否定词典
    turn_lexicon = pd.read_csv('字典配置/turn.txt')
    not_lexicon = pd.read_csv('字典配置/not.txt')
    adv_lexicon = pd.read_csv('字典配置/adv.txt', sep=',')
    adv_lexi = adv_lexicon['word']
    adv_lexi = pd.DataFrame(data=adv_lexi, columns=['word'])
    s_neg = pd.read_csv('字典配置/stable_neg.csv', sep=';')
    s_pos = pd.read_csv('字典配置/stable_pos.csv', sep=';')
    #user_dict = s_neg.append([turn_lexicon, not_lexicon, s_pos, stop_words, adv_lexi, new_word], ignore_index=True)
    user_dict = pd.concat([s_neg, turn_lexicon, not_lexicon, s_pos, stop_words, adv_lexi, new_word], ignore_index=True)
    user_dict['label'] = 'uw'
    user_dict = user_dict.drop_duplicates()
    user_dict.to_csv('user_dict_xiehe-our.csv', sep='\t', index=False)


main()
pynlpir.close()
