import pandas as pd
import numpy as np

def normalize_group_emotions():
    # 读取三个CSV文件
    df1 = pd.read_csv('group_emotion1000/群体情绪1.csv', sep=';', encoding='utf-8')
    df2 = pd.read_csv('group_emotion1000/群体情绪2.csv', sep=';', encoding='utf-8')
    df3 = pd.read_csv('group_emotion1000/群体情绪3.csv', sep=';', encoding='utf-8')
    
    # 获取所有群体情绪值
    all_emotions = pd.concat([
        df1['群体情绪'],
        df2['群体情绪'],
        df3['群体情绪']
    ])
    
    # 计算最大绝对值用于归一化
    max_abs_emotion = max(abs(all_emotions.max()), abs(all_emotions.min()))
    
    # 对每个DataFrame进行归一化处理
    def normalize_and_save(df, output_file):
        # 复制DataFrame以避免修改原始数据
        df_normalized = df.copy()
        # 归一化群体情绪
        df_normalized['归一化的群体情绪'] = df['群体情绪'] / max_abs_emotion
        # 保存结果
        df_normalized.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';')
        return df_normalized
    
    # 处理并保存每个文件
    results = {
        '群体情绪1': normalize_and_save(df1, 'group_emotion1000/群体情绪1.csv'),
        '群体情绪2': normalize_and_save(df2, 'group_emotion1000/群体情绪2.csv'),
        '群体情绪3': normalize_and_save(df3, 'group_emotion1000/群体情绪3.csv')
    }
    
    print('归一化处理完成，结果已保存到新文件中。')
    return results

if __name__ == '__main__':
    # 执行归一化处理
    results = normalize_group_emotions()
    
    # 显示处理结果
    for name, df in results.items():
        print(f'\n{name}的归一化结果：')
        print(df[['智能体类别', '群体情绪', '归一化的群体情绪']])