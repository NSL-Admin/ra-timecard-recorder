# Slack Botの "App Home" に表示するビューをpublishするためのスクリプト

[Slack BotのApp Home](https://api.slack.com/surfaces/app-home)に表示したいビューを[Block Kit Builder](https://app.slack.com/block-kit-builder/T032TE5A2PP#%7B%22type%22:%22home%22,%22blocks%22:%5B%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22This%20is%20a%20Block%20Kit%20example%22%7D,%22accessory%22:%7B%22type%22:%22image%22,%22image_url%22:%22https://api.slack.com/img/blocks/bkb_template_images/notifications.png%22,%22alt_text%22:%22calendar%20thumbnail%22%7D%7D%5D%7D)で作った後に、完成したビューを保存したJSONファイルの内容をSlack APIへPOSTするためのスクリプトです。

### 使い方

1. `pip install requests` でrequestsパッケージをインストールしてください。

2. このディレクトリで
    ```python
    python publish_view.py <ビューをpublishする宛のSlackユーザID> <ビュー含むJSONファイルへのパス>
    ```
    を実行し、Bot User OAuth Tokenを入力してください。