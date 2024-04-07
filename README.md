# Backup Server

Raspberry pi 上で動作するファイルバックアップサーバ

* rsync 使用した差分バックアップ
* 複数バックアップの区分管理機能
* 実行ステータス確認機能
* 過去世代の保持機能

## requirements

python 3.7 or hieger

## Usage

1. 依存パッケージをインストールする

    ```sh
    pip install -r requirements.txt
    ```
1. フロントエンドをビルドする

    - templates ディレクトリ内に index として表示されるモジュールがビルドされます

    ```sh
    cd frontend
    npm ci
    npm run build
    ```

1. バックアップ元、バックアップ先を　raspberry pi に mount する
1. [config.ini](#config) に設定を記載する
1. app.py を実行しサーバ起動する

    - 5000 ポートで起動されます

    ```sh
    python3 app.py
    ```

1. POST /api/\<user\>/\<target\>/  にリクエストする

以下のようにバックアップディレクトリが作成されます(dest を `/mnt/backup/foo/hoge/` にした場合)

```
/mnt/backup/foo
├─ hoge # 最新のバックアップディレクトリ
├─ hoge_YYYYMMDD # 過去世代のバックアップディレクトリ
```

自動バックアップする場合は cron でバッチ実行してください

```
# foo_hoge のバックアップを毎週日曜日の 02:00 に実行する
0   2   *   *   0   curl -X POST http://<server_address>:5000/api/foo/hoge
```

## API

| method | endpoint | description |
|------|------|-----|
| GET | / | フロントエンド表示 |
| GET | /api/status/ | [実行ステータス](#status)を取得する |
| POST | /api/clear_error/ | エラーになったタスクをクリアする |
| POST | /api/clear_finished/ | 終了したタスクをクリアする |
| POST | /api/\<user\>/\<target\>/ | 対象のユーザー,ターゲットのバックアップを実行する |

## Config

config.ini に以下のように指定する。

```ini
[foo_hoge] # バックアップ区分名 (user_target の書式で記載)
source = /mnt/data/foo/hoge/ # バックアップ元ディレクトリパス
dest = /mnt/backup/foo/hoge/ # バックアップ先ディレクトリパス
keep_count = 3 #　過去世代保持数 0 は過去を保持しない
date_last = 20200118 # 最終バックアップ実行日付(過去世代保持時の前回日付として使用する)
```

## Status

以下4種あります

| status | description |
|-----|-----|
| error | 実行エラータスク |
| finished | 実行完了タスク |
| running | 実行中タスク |
| pending | 別のバックアップが実行中なので待ちになっているタスク |

```
# /api/status のレスポンス例
{
    "error": [
        { "name": "foo_hoge", "updated_at": "YYYY-MM-DDTHH:mm:ss.SSSZ" }
    ]
    "finished": [
        { "name": "foo_fuga", "updated_at": "YYYY-MM-DDTHH:mm:ss.SSSZ" },
        { "name": "bar_hoge", "updated_at": "YYYY-MM-DDTHH:mm:ss.SSSZ" }
    ],
    "running": [
        { "name": "baz_fuga", "updated_at": "YYYY-MM-DDTHH:mm:ss.SSSZ" }
    ],
    "pending": [
        { "name": "qux_all", "updated_at": "YYYY-MM-DDTHH:mm:ss.SSSZ" }
    ]
}
```
