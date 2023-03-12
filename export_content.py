import os
import json
import markdown

CONTENT_DIR = 'content'

class ContentLoader:
    def __init__(self, content_dir):
        self.content_dir = content_dir
        self.contents = []
    
    def dump(self, filename='contents.json'):
        with open(filename, 'w',  encoding='utf-8') as f:
            json.dump({"pages": self.contents}, f)
        
    def load(self, path=''):
        if path == '':
            path = self.content_dir
        
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                self.load(file_path)
            if os.path.isfile(file_path) and os.path.splitext(file_path)[-1] == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    md = markdown.Markdown(extensions = ['meta'])
                    md.convert(content)
                    self.contents.append(dict({
                        'path': path,
                        'lines': content.split('---')[2].split('\n') # メタデータを取り除いてlineを入れていく。
                    }, **md.Meta))

                    
def main():
    loader = ContentLoader(CONTENT_DIR)
    loader.load()
    loader.dump()


if __name__ == '__main__':
    main()