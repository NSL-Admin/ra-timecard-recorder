# ra-timecard-recorder: Slack Bot that enables RAs to easily record and retrieve timecard.

[![Fly Deploy](https://github.com/NSL-Admin/ra-timecard-recorder/actions/workflows/fly.yml/badge.svg)](https://github.com/NSL-Admin/ra-timecard-recorder/actions/workflows/fly.yml)

## 概要

RAが勤務を記録し管理する作業を支援するBotです。Slackへの勤務報告メッセージの送信によって勤務がデータベースに記録され、月末にCSV形式でダウンロードすることができます。また、別途提供している[Chrome拡張機能](https://github.com/NSL-Admin/ra-timecard-autofiller)を利用することによって、このCSVファイルをもとにMyWasedaの業務従事内容報告画面で出勤簿を自動入力することが可能です。

## Botの使用方法

:bulb: Slack上でこのBotとのDMを開いたときの「ホーム」タブに表示される使い方ガイドも参照してください。

### 初期設定

1. `/init <氏名>` を実行し、ユーザとして登録を行ってください。
2. `/register_ra <RA区分名>` を実行し、RAの登録を行ってください。
   - :warning: `<RA区分名>` は、Slack上で勤務報告を行う際に記載しているものと同じである必要があります。（例: NTTコム, 基盤A）

### 勤務の記録と削除

**勤務の記録**

Botが参加しているチャンネルにおいて、このBotをメンションしてください。その際に送るメッセージは以下のフォーマットを**厳密に**守る形にしてください。フォーマットが正しければ、勤務がデータベースに記録されたタイミングでBotが返信します。

```
@RA timecard recorder [任意のコメント(省略可)]
• 氏名 (例: RA太郎)
• RA区分名 (例: NTTコム)
• 勤務時間 (例: 2023/11/18 15:00-21:00)
• 勤務内容 (例: 学習用データセットの構築)
```

<img src="https://github.com/NSL-Admin/ra-timecard-recorder/assets/37496476/fe550e8f-e67c-404f-9ff6-b6c4f65d11cd" height=60% width=60%>

注意:
- 勤務時間の行の時刻情報は、時・分ともに2桁ずつ記入してください。
  - :o: 09:04   :x: 9:04
- 勤務中に休憩をしたときは、勤務時間の後ろに半角スペースを空け、それに続けて `休憩01:00` のように記入してください。"休憩"という文字列もこの通りに入力してください。全体で `2023/11/18 21:00-22:00 休憩01:00` のようになります。

**勤務記録の削除**

上記で送信した勤務記録のメッセージを削除すると、それに対応する勤務記録がBotのデータベースからも削除されます。

### 勤務時間の確認とCSVファイルのダウンロード

1. `/get_working_hours [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務時間を確認することができます。年月を省略した場合、今月の勤務時間が表示されます。
2. `/download_csv [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務記録をCSVファイル形式でダウンロードすることができます。年月を省略した場合、今月の勤務記録がダウンロードされます。

## ローカル環境で開発を始めるには

1. `utils/dev_database` ディレクトリに移動し、`docker compose up -d` を実行してください。PostgreSQLのコンテナが起動し、内部に開発用データベースが作成されます。

2. 以下のような .db.env という名前のファイルを作成してください。

    .db.env
    ```
    DB_USERNAME=root
    DB_PASSWORD=root
    DB_HOST=localhost
    DB_NAME=ra_timecard_recorder_dev_db
    ```

3. リポジトリ内の `assets/manifest.yml` をもとに[Slackのポータル](https://api.slack.com/apps)にてアプリケーションを作成し、作成したアプリレベルトークンとボットトークンを以下のような .slack.env という名前のファイルに保存してください。

    .slack.env
    ```
    SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx
    SLACK_BOT_TOKEN=xoxb-yyyyyyyyyyyy
    ```

4. PythonからPostgreSQLに接続するために必要となる[psycopgのインストール要件](https://www.psycopg.org/docs/)を満たしているか確認してください。満たしていない場合、6.のpip installが失敗します。

5. Pythonの仮想環境を作成し、このリポジトリフォルダ直下で `pip install -r requirements.txt` を実行して必要なライブラリをインストールしてください。

6. `python app.py` を実行して開発を始めてください。

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