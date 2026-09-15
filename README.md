# モーニング・ビルド — 自動ポッドキャスト配信

毎朝4時（JST）に Claude が書いた台本を、音声化して Spotify に自動配信するための仕組みです。
**月額費用ゼロ。TTS の API キーも不要です。**

---

## 全体の流れ

```
毎朝4時  Claude のスケジュールタスク（クラウド）
   ├ COROS からデータ取得 → 取材 → 台本執筆
   ├ Notion にアーカイブ
   └ このリポジトリの episodes/ に台本を push
              │
              ▼  push をトリガーに自動起動
        GitHub Actions
   ├ Edge TTS で日本語女性音声（ja-JP-Nanami）の MP3 を生成
   ├ MP3 を Releases にアップロード
   └ RSS を再生成 → GitHub Pages で公開
              │
              ▼  最初の1回だけ手動
        Spotify for Creators に RSS を登録
              │
              ▼
        以降、毎朝あたらしいエピソードが自動で並ぶ
```

---

## セットアップ（初回のみ・所要30分ほど）

### 1. リポジトリを作る

GitHub で新しいリポジトリを作り、この一式をアップロードします。

- 名前：`morning-build-podcast`（任意）
- 公開設定：**Public**（GitHub Pages と Releases を無料で使うため）

### 2. `show.json` を書き換える

3か所だけ、ご自身の情報に置き換えてください。

| 項目 | 書き換える内容 |
|---|---|
| `repo` | `あなたのGitHub名/morning-build-podcast` |
| `pages_url` | `https://あなたのGitHub名.github.io/morning-build-podcast` |
| `email` | Spotify の所有者確認メールを受け取るアドレス |

`email` は RSS に記載され、**一般に公開されます**。普段お使いのアドレスを載せたくない場合は、この番組専用のアドレスを用意してください。

### 3. GitHub Pages を有効にする

リポジトリの **Settings → Pages** で、Source を **GitHub Actions** に設定します。

### 4. Actions に書き込み権限を与える

**Settings → Actions → General → Workflow permissions** で
**Read and write permissions** を選んで保存します。

### 5. 最初のエピソードを走らせる

`episodes/2026-09-15.md`（匿名化済みの第1話）が入った状態で push すると、
Actions が動きます。**Actions** タブで進行が見られます。10〜15分ほどで完了します。

終わったら、次のURLが開けるか確認してください。

```
https://あなたのGitHub名.github.io/morning-build-podcast/index.xml
```

RSS が表示されれば成功です。

### 6. Spotify for Creators に登録する

1. <https://creators.spotify.com/> にアクセスしてサインイン
2. 「Add your podcast」→ 上のRSS URLを貼り付け
3. `show.json` の `email` 宛に届く確認コードを入力
4. カテゴリなどを設定して送信

審査に数時間から数日かかります。通れば、以降の新エピソードは**RSSを読みに来るだけで自動的に並びます**。登録作業はこの1回きりです。

### 7. Claude 側にリポジトリを教える

セットアップが終わったら、GitHubのユーザー名とリポジトリ名を私に伝えてください。
毎朝4時のスケジュールタスクに「台本を push する」手順を追加します。

書き込み用のトークン（Personal Access Token、`contents: write` 権限）も必要になります。
**チャットに貼るとこの会話の記録に残ります**ので、有効期限を短めに設定し、
この用途専用のトークンを発行することをおすすめします。

---

## 音声の設定

`.github/workflows/publish.yml` の環境変数、または `scripts/synthesize.py` の先頭で調整できます。

| 変数 | 初期値 | 意味 |
|---|---|---|
| `TTS_VOICE` | `ja-JP-NanamiNeural` | 日本語・女性・標準音声 |
| `TTS_RATE` | `-5%` | 話速。`-10%` でさらにゆっくり |
| `TTS_PAUSE_SEC` | `1.6` | 章の切れ目に入る無音の長さ（秒） |

他の日本語音声も使えます。`ja-JP-KeitaNeural` が男性、`ja-JP-NanamiNeural` が女性です。

---

## 台本の書式ルール

`scripts/synthesize.py` は、次のルールで読み上げ範囲を判定します。

- **読み上げる**：本文の地の文
- **読み上げない**：「音声合成ディレクション」「構成と尺の目安」「出典」「本人向けメモ」の各見出し以下、すべての見出し行、表、リンクURL
- **`―――` の行**：ここで区切って、あいだに無音を挿入します

つまり、個人的なメモを台本に残したいときは `## 本人向けメモ` という見出しの下に書けば、音声には入りません。

---

## 運用上の注意

**内容は一般公開されます。** Spotify のポッドキャストに非公開配信の仕組みはなく、
GitHub Pages と Releases も公開です。第1話は氏名・勤務先・居住地を除き、
睡眠やHRVなどの詳細な身体データを抽象化した匿名化版になっています。
今後の台本も同じ方針で生成されます。

**容量について。** 40分のMP3が1本あたり約19MBです。音声は Releases に置くため
リポジトリ本体は膨らみません。RSS に載るのは `show.json` の `max_items`（初期値60本）
までで、それより古いエピソードは自動的にフィードから外れます（Releases には残ります）。

**Actions の無料枠。** Publicリポジトリでは GitHub Actions は無料・無制限です。
1エピソードあたり10〜15分ほど使います。
