# Cloud Speech-to-Text を利用したリアルタイム音声認識（サンプルベース）

## Google Cloud Platform の設定

* [Google Cloud Platform](https://cloud.google.com/?hl=ja)
* GCP のコンソールに Google アカウントでログインする。
* プロジェクトを作成する
* Cloud Speech-to-Text API を有効化する
* 認証情報でサービスアカウントを作成する
* サービスアカウントキー（JSON）をダウンロードする

## プロジェクト作成

```powershell
> poetry new speechtotext --name app
> cd speechtotext
```

## pyproject.toml の編集（Pythonバージョン）

```text
[tool.poetry.dependencies]
python = "^3.6"
```

## プロジェクト設定

```powershell
> pyenv update
> pyenv versions
> pyenv install 3.6.8
> pyenv local 3.6.8
> pyenv rehash
> python -V
Python 3.6.8
```

## バージョン更新

```powershell
> python -m pip install --upgrade pip
> python -m pip install --upgrade setuptools
```

## ライブラリの追加

```powershell
> poetry add pylint
> poetry add google-cloud-speech
> poetry add pyaudio
> poetry add six
```

## ライブラリの一括追加

```powershell
> poetry install
```

## 環境変数の設定（サービスアカウントキー）

```text
環境変数 GOOGLE_APPLICATION_CREDENTIALS に、サービスアカウントキーのJSONファイルのパスを設定しておく
```

## プログラムの実行

```powershell
> poetry run python main.py
```

## 補足

言語コード  ：ja-JP
モデル      ：command_and_search
エンハンスド：有効
