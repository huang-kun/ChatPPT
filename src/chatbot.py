import gradio as gr
from openai import OpenAI
import os
import httpx

CHATBOT_USE_TIP = "请描述你想要创建ppt的内容："
CHAT_SAVE_KEYWORDS = ['save', 'Save', '保存']
CHAT_PLACEHOLDER = f'''
举个例子，您可以说：
这是我的个人简历。北京皇家理工大学计算机专业，在大米公司工作5年，从事安卓开发，擅长java和算法数据结构，
参与过畅聊app、自习室app等重要项目研发，定期参与内部技术分享。这里是我的技术博客https://www.myfakeblog.com

如果您对生成的markdown模板比较满意，输入以下任一指令:
{", ".join(map(lambda x: "'" + x + "'", CHAT_SAVE_KEYWORDS))}
即可保存ppt
'''

# 由外部传递一个生成ppt的函数
generate_ppt_function = None


class ChatAI:

    def __init__(self, model='gpt-3.5-turbo', system_prompt='You are a helpful assistant.'):
        self.model = model
        self.llm = self.create_llm_client()
        self.messages = [{'role': 'system', 'content': system_prompt}]

    def get_response(self, user_input):
        if isinstance(user_input, str):
            self.messages.append({'role': 'user', 'content': user_input})
            chat_comp = self.llm.chat.completions.create(model=self.model, messages=self.messages)
            llm_msg = self.get_llm_message(chat_comp)
            self.messages.append({'role': 'assistant', 'content': llm_msg})
            return llm_msg
        else:
            raise TypeError(f"Unsupported type for user_input: {user_input}")
        
    def get_last_ai_response(self):
        for message in reversed(self.messages):
            if message['role'] == 'assistant':
                return message['content']
        return None

    @staticmethod
    def create_llm_client():
        api_key = os.environ["OPENAI_API_KEY"]
        if "OPENAI_BASE_URL" in os.environ:
            base_url = os.environ["OPENAI_BASE_URL"]
            return OpenAI(
                base_url=base_url, 
                api_key=api_key,
                http_client=httpx.Client(
                    base_url=base_url,
                    follow_redirects=True,
                ),
            )
        else:
            return OpenAI(api_key=api_key)

    @staticmethod
    def get_llm_message(chat_completion):
        return chat_completion.choices[0].message.content


def create_chatbot():
    prompt_path = get_path("prompts/formatter.txt")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"prompt file is not found: {prompt_path}")
    with open(prompt_path) as f:
        system_prompt = f.read().strip()

    chat_ai = ChatAI(model='gpt-4o-mini', system_prompt=system_prompt)

    with gr.Blocks(title="ChatPPT Generator") as chatppt_app:
        gr.Markdown(CHATBOT_USE_TIP)
        chatbot = gr.Chatbot(
            placeholder=CHAT_PLACEHOLDER,
            height=800
        )

        def handle_chat(user_input, chat_history):
            if isinstance(user_input, str):
                if user_input in CHAT_SAVE_KEYWORDS:
                    text = chat_ai.get_last_ai_response()
                    return generate_ppt(text)
                else:
                    return chat_ai.get_response(user_input)
            else:
                return "not supported now."
        
        gr.ChatInterface(
            fn=handle_chat,
            chatbot=chatbot,
            # retry_btn=None,
            # undo_btn=None,
        )

    chatppt_app.launch(share=True, server_name="0.0.0.0")


def generate_ppt(text):
    if generate_ppt_function:
        inputs_dir = get_path('inputs')
        user_md_path = os.path.join(inputs_dir, 'homework_ppt.md')
        with open(user_md_path, 'w') as f:
            f.write(text)

        outputs_dir = get_path('outputs')
        if not os.path.exists(outputs_dir):
            os.mkdir(outputs_dir)

        generate_ppt_function(user_md_path)
        
        return "ppt保存成功，请在outputs目录里查看"
    else:
        return "缺失生成ppt的能力"


def get_path(rel_path):
    curr_path = os.path.abspath(__file__)
    src_dir = os.path.dirname(curr_path)
    project_dir = os.path.dirname(src_dir)
    return os.path.join(project_dir, rel_path)


if __name__ == "__main__":
    create_chatbot()