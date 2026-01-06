# Auto Tweet Bot using Gemini and Github Actions

このプロジェクトは、Google Gemini APIを使用してツイート内容を生成し、GitHub Actionsを使用して自動的にX ( 旧Twitter ) に投稿するBotです。

## セットアップ手順

### 1. 必要なAPIキーの取得
以下のサービスからAPIキーを取得してください。

*   **Google Gemini API**: [Google AI Studio](https://makersuite.google.com/) からAPIキーを取得。
*   **X (Twitter) API**: [X Developer Portal](https://developer.twitter.com/en/portal/dashboard) から以下のキーを取得 (Read and Write権限が必要です)。
    *   API Key (Consumer Key)
    *   API Key Secret (Consumer Secret)
    *   Access Token
    *   Access Token Secret

### 2. ローカルでの実行確認 (オプション)
ローカルでテストする場合は、`.env` ファイルを作成し、以下の形式でキーを保存してください。

```
GEMINI_API_KEY=your_gemini_key
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

依存関係をインストールして実行します。
```bash
pip install -r requirements.txt
python main.py
```

### 3. GitHub Actionsの設定
GitHubリポジトリの設定画面 (Settings) -> **Secrets and variables** -> **Actions** に移動し、以下のRepository secretsを追加してください。

*   `GEMINI_API_KEY`
*   `TWITTER_API_KEY`
*   `TWITTER_API_SECRET`
*   `TWITTER_ACCESS_TOKEN`
*   `TWITTER_ACCESS_TOKEN_SECRET`

### 4. 実行
設定が完了すると、毎日午前9時 (JST) に自動的にツイートされます。
「Actions」タブから手動で実行することも可能です。

## 設定の変更
*   `config.json`: 使用するモデルや文字数制限を設定できます。
*   `prompt.txt`: AIへの指示（プロンプト）を変更できます。
