import pandas as pd
import numpy as np

# 定义智能体类别及其对应的agent范围
AGENT_CATEGORIES = {
    '普通公众': list(range(0, 440)),  # agent0-24
    '患者及家属': list(range(440, 580)),  # agent25-31
    '医学生': list(range(580, 680)),  # agent32-36
    '政策制定者': list(range(680, 720)),  # agent37-38
    '医学专家': list(range(720, 820)),  # agent39-43
    '教育工作者': list(range(820, 880)),  # agent44-46
    '媒体': list(range(880, 960)),  # agent47-50
    '协和校友': list(range(960, 1000))  # agent51-52
}


def calculate_group_emotions(file, output_file):
    # 读取CSV文件
    df = pd.read_csv(file, sep=';', encoding='utf-8')
    
    # 初始化结果字典
    results = {
        '智能体类别': [],
        '平均情绪值': [],
        '智能体数量': [],
        '情绪标准差': [],  # cre1
        '情绪分叉度': [],  # cre2
        '集群信任度': []   # cre
    }
    
    # 对每个类别计算平均情绪值和集群信任度指标
    for category, agent_range in AGENT_CATEGORIES.items():
        # 构建agent名称列表
        agent_names = [f'agent_{i}' for i in agent_range]
        
        # 筛选该类别的所有评论
        category_df = df[df['用户名'].isin(agent_names)]
        
        if not category_df.empty:
            # 计算平均情绪值
            avg_emotion = category_df['单条评论情绪值'].mean()
            
            # 计算情绪标准差 (cre1)
            std_dev = category_df['单条评论情绪值'].std()
            if not pd.notna(std_dev):
                std_dev = 0
            
            # 计算情绪分叉度 (cre2)
            max_positive = category_df[category_df['单条评论情绪值'] > 0]['单条评论情绪值'].max()
            min_negative = category_df[category_df['单条评论情绪值'] < 0]['单条评论情绪值'].min()
            
            if pd.notna(max_positive) and pd.notna(min_negative):
                bifurcation = max_positive - min_negative
            else:
                bifurcation = 0
            
            cre2 = (2 - bifurcation) / 2
            
            # 计算集群信任度 (cre)
            cre = 0.5 * std_dev + 0.5 * cre2
            
            # 添加结果
            results['智能体类别'].append(category)
            results['平均情绪值'].append(round(avg_emotion, 4))
            results['智能体数量'].append(len(agent_range))
            results['情绪标准差'].append(round(std_dev, 4))
            results['情绪分叉度'].append(round(cre2, 4))
            results['集群信任度'].append(round(cre, 4))
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(results)
    
    # 归一化集群信任度
    max_cre = results_df['集群信任度'].max()
    if max_cre != 0:
        results_df['集群信任度'] = results_df['集群信任度'] / max_cre
    
    # 计算群体情绪指数
    emo_index = results_df['平均情绪值'] * results_df['集群信任度']
    results_df['群体情绪'] = emo_index

    # # 群体情绪指数归一化
    # max_emo_index = emo_index.max()
    # min_emo_index = emo_index.min()
    # max_emo = max(abs(max_emo_index), abs(min_emo_index))
    # emo_index = emo_index / max_emo

    # results_df['归一化的群体情绪'] = emo_index

    # 保存结果到CSV文件
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';')
    print(f'结果已保存到{output_file}')
    
    return results_df

def calculate_overall_emotions(file, existing_output_file):
    # 读取CSV文件
    df = pd.read_csv(file, sep=';', encoding='utf-8')
    
    # 初始化结果字典
    results = {
        '智能体类别': ['总体'],
        '平均情绪值': [],
        '智能体数量': [],
        '情绪标准差': [],  # cre1
        '情绪分叉度': [],  # cre2
        '集群信任度': []   # cre
    }
    
    # 计算所有智能体的总体情绪指标
    # 计算平均情绪值
    avg_emotion = df['单条评论情绪值'].mean()
    
    # 计算情绪标准差 (cre1)
    std_dev = df['单条评论情绪值'].std()
    if not pd.notna(std_dev):
        std_dev = 0
    
    # 计算情绪分叉度 (cre2)
    max_positive = df[df['单条评论情绪值'] > 0]['单条评论情绪值'].max()
    min_negative = df[df['单条评论情绪值'] < 0]['单条评论情绪值'].min()
    
    if pd.notna(max_positive) and pd.notna(min_negative):
        bifurcation = max_positive - min_negative
    else:
        bifurcation = 0
    
    cre2 = (2 - bifurcation) / 2
    
    # 计算集群信任度 (cre)
    cre = 0.5 * std_dev + 0.5 * cre2
    
    # 添加结果
    results['平均情绪值'].append(round(avg_emotion, 4))
    results['智能体数量'].append(len(df))
    results['情绪标准差'].append(round(std_dev, 4))
    results['情绪分叉度'].append(round(cre2, 4))
    results['集群信任度'].append(round(cre, 4))
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(results)
    
    # 计算群体情绪指数
    emo_index = results_df['平均情绪值'] * results_df['集群信任度']
    results_df['群体情绪'] = emo_index
    
    # 读取现有的CSV文件
    try:
        existing_df = pd.read_csv(existing_output_file, sep=';', encoding='utf-8')
        # 合并两个DataFrame
        combined_df = pd.concat([existing_df, results_df], ignore_index=True)
        # 保存合并后的结果
        combined_df.to_csv(existing_output_file, index=False, encoding='utf-8-sig', sep=';')
        print(f'总体结果已追加到{existing_output_file}')
    except FileNotFoundError:
        # 如果文件不存在，直接保存结果
        results_df.to_csv(existing_output_file, index=False, encoding='utf-8-sig', sep=';')
        print(f'总体结果已保存到{existing_output_file}')
    
    return results_df

if __name__ == '__main__':
    file = 'group_emotion1000\宏观集群平均情绪3.csv'
    output_file = '群体情绪3.csv'
    # 计算并显示分类结果
    results = calculate_group_emotions(file, output_file)

    print('\n各类智能体情绪统计结果：')
    print(results)
    
    # 计算并显示总体结果，使用同一个输出文件
    overall_results = calculate_overall_emotions(file, output_file)

    print('\n总体智能体情绪统计结果：')
    print(overall_results)