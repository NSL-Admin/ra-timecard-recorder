# ローカル環境で開発を始めるには

## 初回起動時

1. `/config/slack_secret_config.json.template` を `/config/slack_secret_config.json` にリネームしてください。その後、このリポジトリの `/misc/manifest.yml` をもとに[Slackのポータル](https://api.slack.com/apps)にてSlackアプリケーションを作成し、作成したApp-Level TokenとBot User OAuth Tokenを `/config/slack_secret_config.json` に書き込んでください。

    /config/slack_secret_config.json
    ```
    {
        "app_token": "xapp-xxxxxxxxxxxxx",
        "bot_token": "xoxb-yyyyyyyyyyyyy"
    }
    ```

1. `/config/bot_config.json` を必要に応じて適切に編集してください。

1. このディレクトリで `docker compose up` を実行するとBotが起動します。

## 注意

- `docker-compose.yml` にてこのリポジトリのルートをコンテナ内にbind mountするよう設定しているため、ホスト側でソースコードに変更を加えるとコンテナ側にも反映されます。
  - したがってソースコードを変更した後にコンテナを再ビルドする必要はなく、Ctrl+Cでコンテナを停止して `docker compose up` で再起動すれば変更後のソースコードで動作します。