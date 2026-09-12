from openai import OpenAI
from dotenv import load_dotenv
from search import search_web

import os
import json


load_dotenv()


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)



# =========================
# Memory
# =========================


MEMORY_FILE="memory.json"



def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return {
            "user_info":{}
        }


    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)


    except:

        return {
            "user_info":{}
        }



def save_memory():

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=4
        )



memory=load_memory()



# =========================
# Memory Agent
# =========================


def should_save_memory(text):


    response=client.chat.completions.create(

        model="deepseek-v4-flash",

        messages=[

            {
                "role":"system",
                "content":
                """
                判断用户输入是否包含长期值得保存的信息。

                需要保存：

                - 用户身份
                - 兴趣
                - 技能
                - 工作
                - 学习方向
                - 长期目标
                - 回复偏好


                不要保存：

                - 一次性问题
                - 临时事件
                - 普通知识


                只回答：

                YES

                或者

                NO
                """
            },


            {
                "role":"user",
                "content":text
            }

        ],

        temperature=0

    )


    return response.choices[0].message.content.strip()=="YES"





def update_memory(text):


    response=client.chat.completions.create(

        model="deepseek-v4-flash",

        messages=[

            {

                "role":"system",

                "content":
                """
                你是长期记忆提取器。

                从用户输入提取长期信息。

                返回严格JSON。

                例如：

                {
                "name":"Example User",
                "interest":"AI Agent",
                "goal":"成为AI工程师"
                }


                没有信息返回：

                {}

                不要解释。
                """
            },


            {
                "role":"user",
                "content":text
            }

        ],

        temperature=0

    )



    result=response.choices[0].message.content.strip()


    try:

        info=json.loads(result)


        if info:

            memory["user_info"].update(info)

            save_memory()


            print(
                "\n[记忆更新]",
                info
            )


    except Exception as e:

        print(
            "Memory解析失败:",
            e
        )






# =========================
# Search Agent
# =========================



def need_search(text):


    response=client.chat.completions.create(

        model="deepseek-v4-flash",

        messages=[

            {
                "role":"system",

                "content":
                """
                判断是否需要联网。

                需要：

                - 最新消息
                - 当前价格
                - 新闻
                - 最近发布
                - 实时数据


                不需要：

                - 教程
                - 编程解释
                - 数学
                - 普通知识


                只回答YES或者NO。
                """
            },


            {
                "role":"user",
                "content":text
            }

        ],

        temperature=0

    )


    return (
        response
        .choices[0]
        .message
        .content
        .strip()
        =="YES"
    )





# =========================
# Chat Context
# =========================


messages=[

    {
        "role":"system",

        "content":
        f"""
        你是一个智能AI助手。


        用户长期信息：

        {memory["user_info"]}


        请根据用户特点调整回答。
        """
    }

]





# =========================
# Main Loop
# =========================


while True:


    question=input("\n你：")



    if question=="退出":

        break




    # ---------
    # Memory
    # ---------


    if should_save_memory(question):

        update_memory(question)



        messages[0]["content"]=f"""

你是一个智能AI助手。


用户长期信息：

{memory["user_info"]}

"""





    # 当前请求上下文

    current_messages=messages.copy()




    # ---------
    # Search
    # ---------


    if need_search(question):


        print("\n正在搜索网络...\n")


        web=search_web(question)



        current_messages.append(

            {
                "role":"system",

                "content":
                f"""
                以下是联网资料：

                {web}


                请结合资料回答。
                """
            }

        )




    current_messages.append(

        {
            "role":"user",
            "content":question
        }

    )




    # ---------
    # DeepSeek
    # ---------


    response=client.chat.completions.create(

        model="deepseek-v4-flash",

        messages=current_messages,

        stream=True,

        extra_body={

            "thinking":{

                "type":"enabled"

            }

        }

    )



    answer=""



    print("\nAI:\n")



    for chunk in response:


        delta=chunk.choices[0].delta



        # reasoning

        if hasattr(delta,"reasoning_content"):

            if delta.reasoning_content:

                print(
                    delta.reasoning_content,
                    end="",
                    flush=True
                )



        # answer

        if delta.content:

            print(
                delta.content,
                end="",
                flush=True
            )

            answer+=delta.content



    print("\n")



    # 保存聊天上下文


    messages.append(

        {
            "role":"user",
            "content":question
        }

    )


    messages.append(

        {
            "role":"assistant",
            "content":answer
        }

    )
