## 使い方

0. pythonをセットアップする

```
# pipenvをinstallしてなければinstallしてから

pipenv sync
```

1. OpenAIのAPI TOKENを取得して `.env` ファイルに保存

```
OPENAI_API_KEY=sk-...
```

2. 読み込みたいコンテンツをjsonにする

export_content.pyのCONTENT_DIRをコンテンツが格納されているPATHに切り替える

```sh
python export_content.py
```

3. コンテンツの埋め込み表現をつくる

```sh
python make_index.py
```

4. チャットを起動する

```sh
python chatai.py --chat
```
