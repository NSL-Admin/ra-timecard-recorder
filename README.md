# ra-timecard-recorder: Slack Bot that enables RAs to easily record and retrieve timecard.

## 概要

RAが勤務を記録し管理する作業を支援するBotです。Slackへの勤務報告メッセージの送信によって勤務がデータベースに記録され、月末にCSV形式でダウンロードすることができます。また、別途提供している[Chrome拡張機能]()を利用することによって、このCSVファイルをもとにMy Wasedaの業務従事内容報告画面で出勤簿を自動入力することが可能です。

## Botの使用方法

### 初期設定

1. `/init <氏名>` を実行し、ユーザとして登録を行ってください。
2. `/register_ra <RA区分名>` を実行し、RAの登録を行ってください。
   - :warning: `<RA区分名>` は、Slack上で勤務報告を行う際に記載しているものと同じである必要があります。（例: NTTコム, 基盤A）

### 勤務の記録

Botが参加しているチャンネルにおいて、このBotをメンションしてください。その際に送るメッセージは以下のフォーマットを**厳密に**守る形にしてください。フォーマットが正しければ、勤務がデータベースに記録されたタイミングでBotが返信します。

```
@RA timecard recorder [任意のコメント(省略可)]
• 氏名 (例: RA太郎)
• RA区分名 (例: NTTコム)
• 勤務時間 (例: 2023/11/18 21:00-22:00)
• 勤務内容 (例: 学習用データセットの構築)
```

注意:
- 勤務時間の行の時刻情報は、時・分ともに2桁ずつ記入してください。
  - :o: 09:04   :x: 9:04
- 勤務中に休憩をしたときは、勤務時間の後ろに半角スペースを空け、それに続けて `(休憩01:00)` のように記入してください。括弧や"休憩"という文字列はこの通りに入力してください。

### 勤務時間の確認とCSVファイルのダウンロード

1. `/get_working_hours [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務時間を確認することができます。年月を省略した場合、今月の勤務時間が表示されます。
2. `/download_csv [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務記録をCSVファイル形式でダウンロードすることができます。年月を省略した場合、今月の勤務記録がダウンロードされます。

## ローカル環境で開発を始めるには

1. 以下のようなDockerfileとdocker-compose.ymlを作成し、 `docker compose up` でコンテナを起動してください。

    Dockerfile
    ```
    FROM postgres
    ```

    docker-compose.yml
    ```
    version: '3'
    services:
    db:
        build: .
        ports:
        - 5432:5432
        environment:
        POSTGRES_USER: root
        POSTGRES_PASSWORD: root
    ```

2. `psql -h localhost -p 5432 -U root` を実行してパスワードに `root` を入力してDBにログインし、 `CREATE TABLE test_db;` を実行して `test_db` という名前のデータベースを作成してください。

3. 以下のような .db.env という名前のファイルを作成してください。

    .db.env
    ```
    DB_USERNAME=root
    DB_PASSWORD=root
    DB_HOST=localhost
    DB_NAME=test_db
    ```

4. リポジトリ内の manifest.yml をもとに[Slackのポータル](https://api.slack.com/apps)にてアプリケーションを作成し、作成したアプリレベルトークンとボットトークンを以下のような .slack.env という名前のファイルに保存してください。

    .slack.env
    ```
    SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx
    SLACK_BOT_TOKEN=xoxb-yyyyyyyyyyyy
    ```

5. PythonからPostgreSQLに接続するために必要となる[psycopgのインストール要件](https://www.psycopg.org/docs/)を満たしているか確認してください。満たしていない場合、6.のpip installが失敗します。

6. Pythonの仮想環境を作成し、このリポジトリのフォルダで `pip install -r requirements.txt` を実行して必要なライブラリをインストールしてください。

7. `python app.py` を実行して開発を始めてください。

## 本番環境にデプロイするには

このリポジトリ内のコードはすぐに[fly.io](https://fly.io)にデプロイ出来るようになっています。
また、mainリポジトリにPull Requestをマージすることでfly.ioへのデプロイが自動的に行われます。

1. 各種PaaSのコントロールパネルにて、以下の環境変数を設定してください。
   - DB_USERNAME: PostgreSQLデータベースへアクセスする際のユーザ名
   - DB_PASSWORD: PostgreSQLデータベースへアクセスする際のパスワード
   - DB_HOST: PostgreSQLデータベースのホスト名
   - DB_NAME: PostgreSQLデータベース内のデータベース名
   - SLACK_APP_TOKEN: Slackアプリのアプリレベルトークン
   - SLACK_BOT_TOKEN: Slackアプリのボットトークン

2. このリポジトリにすでに置かれているDockerfileをもとにコンテナイメージをビルドし、デプロイしてください。