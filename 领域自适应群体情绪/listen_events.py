import json
import csv
import os

# 定义输入和输出文件路径
input_file = os.path.join('log1000/log3', 'event.json')
output_file = '领域自适应群体情绪/listen_events3.csv'

# 读取JSON文件
print(f"正在读取文件: {input_file}...")
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    print(f"成功读取 {len(events)} 个事件")
except Exception as e:
    print(f"读取文件时出错: {e}")
    exit(1)

# 检查文件结构
if len(events) > 0:
    print(f"第一个事件的结构: {list(events[0].keys())}")
    if 'type' in events[0]:
        print(f"第一个事件的类型: {events[0]['type']}")
    else:
        print("警告: 事件中没有找到'type'字段")

# 过滤出所有type为listen的事件
listen_events = []
for event in events:
    if event.get('type') == 'listen':
        listen_events.append(event)

print(f"找到 {len(listen_events)} 个listen类型的事件")

# 将过滤后的事件写入CSV文件
print(f"正在写入CSV文件: {output_file}...")
try:
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        # 定义CSV文件的列名
        fieldnames = ['文本', '发布者', '评论时间', '用户名', '评论内容', '标记']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # 写入每个事件的数据
        for event in listen_events:
            # 提取所需字段
            content = event.get('item', {}).get('content', '')
            source = event.get('item', {}).get('source', '')
            ts = event.get('ts', 0)
            owner = event.get('owner', '')
            opinion = event.get('item', {}).get('opinion', '')
            
            # 写入CSV行
            writer.writerow({
                '文本': content,
                '发布者': source,
                '评论时间': ts,
                '用户名': owner,
                '评论内容': opinion,
                '标记': 0  # 默认标记为0
            })
    
    print(f"成功将 {len(listen_events)} 个事件写入CSV文件")
    print(f"CSV文件已保存至: {os.path.abspath(output_file)}")
except Exception as e:
    print(f"写入CSV文件时出错: {e}")
    exit(1)