# ra-timecard-recorder: Slack Bot that enables RAs to easily record and retrieve timecard.

[![Fly Deploy](https://github.com/NSL-Admin/ra-timecard-recorder/actions/workflows/fly.yml/badge.svg)](https://github.com/NSL-Admin/ra-timecard-recorder/actions/workflows/fly.yml)

## 概要

RAが勤務を記録し管理する作業を支援するBotです。Slackへの勤務報告メッセージの送信によって勤務がデータベースに記録され、月末にCSV形式でダウンロードすることができます。また、別途提供している[Chrome拡張機能](https://github.com/NSL-Admin/ra-timecard-autofiller)を利用することによって、このCSVファイルをもとにMyWasedaの業務従事内容報告画面で出勤簿を自動入力することが可能です。

## Botの使用方法

> [!TIP]
> Slack上でこのBotとのDMを開いたときの「ホーム」タブに表示される使い方ガイドも参照してください。

### 初期設定

1. `/init <氏名>` を実行し、ユーザとして登録を行ってください。
2. `/register_ra <RA区分名>` を実行し、RAの登録を行ってください。
   - :warning: `<RA区分名>` は、Slack上で勤務報告を行う際に記載しているものと同じである必要があります。（例: NTTコム, 基盤A）

### 勤務の記録と削除

**勤務の記録**

Botが参加しているチャンネルにおいて、このBotをメンションしてください。その際に送るメッセージは以下のフォーマットを**厳密に**守る形にしてください。フォーマットが正しければ、勤務がデータベースに記録されたタイミングでBotが返信します。

```
@RA timecard recorder [任意のコメント(省略可)]
• 氏名 (例: NameOfRA)
• RA区分名 (例: 研究予算A)
• 勤務時間 (例: 2024/12/30 09:00-18:00 R01:00)
• 勤務内容 (例: データセットの作成と評価)
```

<img src="https://github.com/user-attachments/assets/780c6990-a721-47a1-8c7c-6bf916fff034" height=60% width=60%>

注意:
- 勤務時間の行の時刻情報は、時・分ともに2桁ずつ記入してください。
  - :o: 09:04   :x: 9:04
- 勤務中に休憩をしたときは、勤務時間の後ろに半角スペースを空け、それに続けて `R01:00` のように記入してください。"R"という文字もこの通りに入力してください。全体で `2023/11/18 21:00-22:00 R01:00` のようになります。

**勤務記録の更新**

上記で送信した勤務記録のメッセージを編集すると、それに対応する勤務記録がBotのデータベースにおいても更新されます。

**勤務記録の削除**

上記で送信した勤務記録のメッセージを削除すると、それに対応する勤務記録がBotのデータベースからも削除されます。

### 勤務時間の確認とCSVファイルのダウンロード

1. `/get_working_hours [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務時間を確認することができます。年月を省略した場合、今月の勤務時間が表示されます。
2. `/download_csv [yyyy/mm]` を実行すると yyyy/mm (例: 2023/11)の勤務記録をCSVファイル形式でダウンロードすることができます。年月を省略した場合、今月の勤務記録がダウンロードされます。

## Botを本番環境で運用するには

> [!TIP]
> あなたが開発者で、ローカル環境でこのBotの開発を始めようとしている場合は、[`/dev`](/dev) のREADMEを読んでください。

### コマンドラインから起動する場合

Botの動作に必要な情報を設定する方法は2通りあります。

1. [`/config`](/config) 内の各設定ファイルを用いて設定する
   - [`/config`](/config) のREADMEを参考にしながら、各設定ファイルに情報を書き込んでください。
2. 環境変数に設定する
   - 以下の表の通りに環境変数を設定してください。

   | 変数名             | 説明                                               |
   | :-:               | :-:                                                |
   | `DB_USERNAME`     | PostgreSQLデータベースへアクセスする際のユーザ名   |
   | `DB_PASSWORD`     | PostgreSQLデータベースへアクセスする際のパスワード |
   | `DB_HOST`         | PostgreSQLデータベースのホスト名                   |
   | `DB_NAME`         | PostgreSQLデータベース内のデータベース名           |
   | `SLACK_APP_TOKEN` | SlackアプリのApp-Level Token                       |
   | `SLACK_BOT_TOKEN` | SlackアプリのBot User OAuth Token                  |

設定が終わったら必要なPythonパッケージをインストールします。

1. Pythonのプロジェクト管理ツールである[uv](https://docs.astral.sh/uv)をインストールしてください。
2. リポジトリルートで `uv sync` を実行して、Botを動かすための仮想環境を準備してください。

最後に以下のコマンドを実行してBotを起動します。情報を設定ファイルに記入したか環境変数に設定したかに応じて指定する引数を変更してください。

```bash
uv run run.py --botconfig <path-to-bot_config.json> --dbconfig [path-to-db_secret_config.json] --slackconfig [path-to-slack_secret_config.json]
```

| 引数名          | 説明                              | 必須    | 備考                          |
| :-:             | :-:                               | :-:     | :-:                           |
| `--botconfig`   | Botの設定ファイルへのパス         |  はい   |                               |
| `--dbconfig`    | DB接続情報設定ファイルへのパス    |  いいえ | 省略時は環境変数が参照される |
| `--slackconfig` | Slack資格情報設定ファイルへのパス |  いいえ | 省略時は環境変数が参照される |

### PaaSにデプロイする場合

このリポジトリ内のコードはすぐに[fly.io](https://fly.io)にデプロイ出来るようになっています。
また、mainブランチにPull Requestをマージすることでfly.ioへのデプロイが自動的に行われます。

1. セキュリティ事故を防ぐため、各種情報は環境変数として設定してください。各種PaaSのコントロールパネルにて、[コマンドラインから起動する場合](#コマンドラインから起動する場合)の表で示した環境変数を設定してください。

2. このリポジトリのルートに置かれているDockerfileを用いてコンテナイメージをビルドし、デプロイしてください。必要に応じてDockerfile末尾のCMDを変更してください。

### (Optional) 本番環境においてSentryによるモニタリングを有効化する

Sentryを使うとBotの実行時に発生したエラーをモニタリングすることができます。[fly.io上のアプリケーションはSentryとシームレスに連携することが可能](https://fly.io/docs/monitoring/sentry/)ですので、運用の効率化のためにも使用することをおすすめします。

Sentry上でProjectを作成し（上のガイドに従いfly.ioと連携させている場合は不要）、`SENTRY_DSN` という環境変数にDSNを書き込んでください。その後、コマンドライン引数に `--use-sentry` を加えてBotを起動してください。