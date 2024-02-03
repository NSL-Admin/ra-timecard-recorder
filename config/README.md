# Botの設定ファイル

## ファイルごとの説明

### `bot_config.json`

Bot自体の設定ファイルです。

- 項目ごとの説明
  - "admin_ids": list[str]
    - `/admin_download_all_records` などの特権コマンドを利用できるユーザのユーザIDのリスト

### `db_secret_config.json`

データベースへの接続情報を書き込む設定ファイルです。

- 項目ごとの説明
  - "username": str
    - PostgreSQLデータベースへアクセスする際のユーザ名
  - "password": str
    - PostgreSQLデータベースへアクセスする際のパスワード
  - "host": str
    - PostgreSQLデータベースのホスト名
  - "db_name": str
    - PostgreSQLデータベース内のデータベース名

### `slack_secret_config.json`

Slackに関する資格情報を書き込む設定ファイルです。

- 項目ごとの説明
  - "app_token": str
    - SlackアプリのApp-Level Token
  - "bot_token": str
    - SlackアプリのBot User OAuth Token