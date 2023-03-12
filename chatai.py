import pdb
import openai
from docopt import docopt
import os
from os.path import join, dirname
from dotenv import load_dotenv
import tiktoken
from make_index import VectorStore

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

enc = tiktoken.get_encoding("cl100k_base")
def get_size(input_str):
    return len(enc.encode(input_str))

INDEX_FILE = "contents.pickle"
MAX_PROMPT_SIZE = 4096
RETURN_SIZE = 500
MAX_HELP_USE_COUNT = 5

SYSTEM_PROMPT = '''
あなたはチャットサポートの一員です。
あなたが知り得ることを 「知識」 として与えます。その 「知識」 だけを用いて{return_size}文字以内で回答してください。
追加で知識が与えられた場合、それもあなたの知っていることとして構いません。
最高のサポートをするために質問が必要であれば質問して構いません。
'''
SYSTEM_PROMPT_SIZE = get_size(SYSTEM_PROMPT)

PROMPT = """
## 知識
{text}

## 質問
{input}
""".strip()


class AIChat:
    def __init__(self, with_content=False):
        openai.api_key = os.environ.get("OPENAI_KEY")
        self.vector_store = VectorStore(INDEX_FILE)
        self.message_history = []
        self.response_history = []
        
        self.message_history.append({
            'role': 'system',
            'content': SYSTEM_PROMPT.format(return_size=RETURN_SIZE)
        })


    def response(self, user_input):
        if user_input == 'debug':
            result = [(index, len(item['content'])) for index, item in enumerate(self.message_history)]
            pdb.set_trace()
            return ''
        
        text = self.make_knowledge_text(user_input)
        prompt = PROMPT.format(input=user_input, text=text, return_size=RETURN_SIZE)
        
        self.message_history.append({
            'role': 'user',
            'content': prompt}
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.message_history,
            temperature=0.5,
        )

        self.message_history.append({
            'role': response['choices'][0]['message']['role'],
            'content': response['choices'][0]['message']['content']
        })
        
        self.response_history.append(response)

        return response['choices'][0]['message']['content']

    def total_token(self):
        total_tokens = map(
            lambda res: res['usage']['total_tokens'],
            self.response_history
        )
        return sum(token for token in total_tokens)
    
    def get_prompt_size(self, user_input):
        prompt_size = 0
        prompt_size += sum(get_size(message['content']) for message in self.message_history)
        prompt_size += get_size(user_input)
        return prompt_size
    
    def all_user_inputs(self, user_input):
        inputs = []
        for message in self.message_history:
            if message['role'] == 'user':
                inputs.append(message['content'])
        
        inputs.append(user_input)
        
        return " ".join(inputs).strip()
    
    def make_knowledge_text(self, user_input):
        prompt_size =  self.get_prompt_size(user_input)
        
        rest = MAX_PROMPT_SIZE - RETURN_SIZE - SYSTEM_PROMPT_SIZE - prompt_size
        if rest < prompt_size:
            raise RuntimeError("too large input!")
        rest -= prompt_size
        
        all_user_inputs = self.all_user_inputs(user_input)
        samples = self.vector_store.get_sorted(all_user_inputs)
        
        to_use = []
        used_title = []
        help_use_count = 1
        for _sim, body, title in samples:
            if help_use_count > MAX_HELP_USE_COUNT:
                break
            
            if title in used_title:
                continue
            
            size = get_size(body)
            if rest < size:
                break
            
            to_use.append(body)
            used_title.append(title)
            print("\nUSE:", title, body)
            rest -= size
            help_use_count += 1

        text = "\n\n".join(to_use)
        return text

def main():

    __doc__ = """
Usage:
    chatai.py [--version] [--help] [--with-content]
    chatai.py --chat

Options:
    -h --help       ヘルプを表示する。
    --version       バージョンを表示する。
    """

    args = docopt(__doc__)
    # print(args)

    if args['--version']:
        print('AIChat 1.0')
        return

    if args['--chat']:
        with_content = args['--with-content']
        chatai = AIChat(with_content=with_content)

        while True:
            # ユーザーからの入力を受け取る
            user_input = input('>> User: ')

            # ユーザーからの入力が「終了」だった場合にプログラムを終了する
            if user_input == '終了':
                break

            # chataiからの応答を取得する
            response = chatai.response(user_input)
            print('>> AIChat: ' + response)


if __name__ == '__main__':
    main()