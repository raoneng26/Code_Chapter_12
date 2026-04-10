from test_agent import TestAgent
from thread_send import ThreadSend

from agent_mesa import ModelBase

from agent_mesa import TotLog

import time

#测试样例模型
class TestModel(ModelBase):

    #根据config生成model
    def __init__(self, tar_graph, person_list, llm):
        """
        初始化对话系统中的每个人物和他们的对话流程。

        :param tar_graph: 目标图，表示对话系统的结构。
        :param person_list: 人物列表，包含所有参与对话的人物信息。
        :param llm: 语言模型，用于生成对话内容。
        """
        
        super().__init__(tar_graph, llm)
        
        #设置Agent        
        for cur_id in range(len(person_list)):
            cur_person = person_list[cur_id]
            cur_agent = TestAgent(cur_id, self, cur_person, None)
            self.add_agent(cur_agent, cur_id)
            
            
    def public_debate(self):
        """
        所有Agent听取一阶段的公开辩论。

        此函数模拟了一次公开辩论的过程。它首先打印出辩论开始的时间，然后读取当前辩论的主题总结，
        接着让每个参与者（agent）听取辩论总结。最后，它将此次辩论的内容记录到日志中，并打印出辩论结束的时间。
        
        该方法不接受任何参数，也没有返回值。
        """
        
        print('public_debate: %d start' % self.schedule.time)
        #获取辩论文本
        cur_debate_num = self.schedule.time + 1
        with open('content/%d.txt' % cur_debate_num, encoding='utf-8') as f:
            cur_debate_summary = f.read()
         
        #事件加入日志
        log_item = {
            'debate_content': cur_debate_summary
        }
        TotLog.add_model_log(self.schedule.time, 'public_debate', log_item)

        #多线程请求
        cur_thread = ThreadSend()
        for cur_agent in self.agent_list:
            cur_thread.add_task(cur_agent.listen, (cur_debate_summary, 'public'))
        
        cur_thread.start_thread()


    def public_debate_null(self):
        """
        所有Agent听取一阶段的空的公开辩论。

        此函数模拟了一次公开辩论的过程。它首先打印出辩论开始的时间，然后读取当前辩论的主题总结，
        接着让每个参与者（agent）听取辩论总结。最后，它将此次辩论的内容记录到日志中，并打印出辩论结束的时间。
        
        该方法不接受任何参数，也没有返回值。
        """
        
        print('public_debate: %d start' % self.schedule.time)
        #获取辩论文本
        cur_debate_num = self.schedule.time + 1
        cur_debate_summary = 'null' 
         
        #事件加入日志
        log_item = {
            'debate_content': cur_debate_summary
        }
        TotLog.add_model_log(self.schedule.time, 'public_debate', log_item)

        #多线程请求
        cur_thread = ThreadSend()
        for cur_agent in self.agent_list:
            cur_thread.add_task(cur_agent.listen_null, (cur_debate_summary, 'public'))
        
        cur_thread.start_thread()


    def vote(self):
        """
        所有Agent进行投票。
        """

        #多线程请求
        cur_thread = ThreadSend()
        for cur_agent in self.agent_list:
            cur_thread.add_task(cur_agent.vote, ())

        print('vote task num', cur_thread.get_task_num())

        cur_thread.start_thread()


    def talk(self):
        self.talk_list = ThreadSend()
        self.schedule.step()
        print('talk task num', self.talk_list.get_task_num())
        
        self.talk_list.start_thread()


    def reflect(self):
        """
        所有Agent进行反思。
        """
        #for cur_agent in self.agent_list:
        #    cur_agent.reflect()
        #多线程请求
        cur_thread = ThreadSend()
        for cur_agent in self.agent_list:
            cur_thread.add_task(cur_agent.reflect, ())
        print('reflect task num', cur_thread.get_task_num())
        
        cur_thread.start_thread()


    #整体模型的step函数
    def step(self):
        #听取辩论文本
        st = time.time()
        
        if self.schedule.time < 5:
            self.public_debate()
        else:
            self.public_debate_null()

        print('public_debate time: %.2f' % (time.time() - st))

        st = time.time()
        print('Node Talk: %d' % (self.schedule.time))
        #节点自由讨论
        #self.schedule.step()
        self.talk()
        print('Node Talk time: %.2f' % (time.time() - st))

        st = time.time()
        print('Node Reflect %d' % (self.schedule.time - 1))
        #节点反思
        self.reflect()
        print('Node Reflect time: %.2f' % (time.time() - st))

        st = time.time()
        print('Node Vote %d' % (self.schedule.time - 1))
        #print('Node Vote')
        self.vote()
        print('Node Vote time: %.2f' % (time.time() - st))

        print('-------------------')
        return 0
  
       