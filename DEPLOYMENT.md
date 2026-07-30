# Django アプリ (`bdo_project`) の GitHub + Neon + Render オンライン公開手順書 (Deployment Guide)

本書は、`bdo_project` (Django アプリ) を GitHub にアップロードし、データベースに **Neon (Free PostgreSQL)**、Web サーバーに **Render (Free Web Service)** を使用してオンライン公開（ローンチ）するための完全手順書です。

---

## 📋 全体構成

| コンポーネント | 利用サービス / 技術 | 役割 |
|---|---|---|
| **ソースコード管理** | GitHub | リポジトリ管理・CI/CD連携 |
| **データベース (DB)** | Neon (Free Tier) | PostgreSQL クラウドデータベース |
| **Web アプリサーバー** | Render (Free Tier) | Django Web サービスのホスティング |
| **静的ファイル** | WhiteNoise | Django内でのCSS/JS等静的ファイル配信 |

---

## 🛠️ 事前準備・ローカルファイルの確認

本プロジェクトには、オンラインデプロイに必要な設定ファイルが既に準備されています。

1. **`build.sh`** （デプロイ時に自動実行されるビルドスクリプト）
   - パッケージのインストール (`pip install -r requirements.txt`)
   - 静的ファイルの集約 (`python manage.py collectstatic --no-input`)
   - DBマイグレーション (`python manage.py migrate`)
2. **`Procfile`** （Webサーバー起動コマンド）
   - `web: gunicorn config.wsgi:application`
3. **`requirements.txt`** （依存ライブラリ一覧）
   - `Django`, `gunicorn`, `psycopg2-binary`, `dj-database-url`, `whitenoise` 等が含まれています。
4. **`config/settings.py`**
   - 環境変数 `DATABASE_URL` がある場合は自動的に Neon PostgreSQL へ接続し、ない場合はローカルの SQLite を使用するハイブリッド設定となっています。

---

## Step 1: GitHub にコードをプッシュする

1. **GitHub に新しいリポジトリを作成**
   - [GitHub](https://github.com/) にログインし、「**New repository**」をクリックします。
   - Repository name: `bdo-project` (任意)
   - Public または Private を選択。
   - ※ `Initialize this repository with a README` などのチェックは外したまま「**Create repository**」をクリックします。

2. **ローカルから GitHub への初回プッシュ**
   - PowerShell または ターミナルを開き、`bdo_project` フォルダに移動します。
   ```powershell
   cd "c:\★大学院留学に向けて\01_On-site\01_Study\04_Trimester 2\MBUA532\App\bdo_project"
   ```
   - 以下のコマンドを実行して GitHub にプッシュします：
   ```powershell
   git init
   git add .
   git commit -m "Initial commit for production deployment on Render and Neon"
   git branch -M main
   git remote add origin https://github.com/<あなたのGitHubユーザー名>/bdo-project.git
   git push -u origin main
   ```

---

## Step 2: Neon で PostgreSQL データベースを作成する

1. [Neon.tech](https://neon.tech/) にアクセスし、無料アカウントを作成・ログインします。
2. 「**Create Project**」をクリックします。
   - **Project Name**: `bdo-db` （任意の名前）
   - **Database Name**: `neondb` （デフォルトのままでOK）
   - **Region**: `ap-southeast-1 (Singapore)` （日本に最も近いリージョンを推奨）
3. プロジェクト作成完了後、ダッシュボードに表示される **Connection String (接続文字列)** をコピーします。
   - 形式例: `postgresql://username:password@ep-xyz-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
   - ※ この URL は Step 4 の環境変数設定で使用します。

---

## Step 3: Render で Web サービスをデプロイする

1. [Render.com](https://render.com/) にアクセスし、無料アカウントを作成・ログインします。
2. ダッシュボード右上の「**New +**」→「**Web Service**」を選択します。
3. **GitHub と連携**し、先ほど作成した `bdo-project` リポジトリを選択して「**Connect**」をクリックします。
4. 設定項目を以下のように入力します：

| 設定項目 | 入力値 |
|---|---|
| **Name** | `bdo-project` (アプリのドメイン名 `https://bdo-project.onrender.com` になります) |
| **Region** | `Singapore` (Neon DB と同じリージョンを推奨) |
| **Branch** | `main` |
| **Root Directory** | 空欄 (リポジトリ直下の場合) |
| **Runtime** | `Python 3` |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn config.wsgi:application` |
| **Instance Type** | **Free** |

5. 画面下の「**Environment Variables (環境変数)**」を開き、以下の Key と Value を追加します：

| Key | Value (設定値) | 備考 |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` | Step 2 でコピーした Neon の接続文字列 |
| `SECRET_KEY` | *(ランダムな長い文字列)* | 例: `django-insecure-prod-key-9876543210-xyz` |
| `DEBUG` | `False` | 本番環境では False に設定 |
| `ALLOWED_HOSTS` | `.onrender.com` | Render のドメインを許可 |
| `PYTHON_VERSION` | `3.12.8` | Django 6.x に必要な Python 3.12 以降を指定 |
| `APP_EDIT_PASSWORD` | *(閲覧・編集モード切替パスワード)* | 任意の設定パスワード |

6. 「**Create Web Service**」をクリックします。
   - Render がコードを取得し、`build.sh` (ライブラリインストール、静的ファイル集約、Neon DBへのマイグレーション) を自動実行した上でアプリを起動します。

---

## Step 4: 動作確認と管理者 (Superuser) の作成

1. **Web サイトへのアクセス確認**
   - デプロイログの最後に表示される URL (`https://bdo-project.onrender.com`) にアクセスし、アプリが正常に表示されるか確認します。

2. **Django 管理者アカウント (Superuser) の作成方法 (無料プラン)**
   - Render の無料プランでは Shell タブが使えないため、以下の **いずれかの方法** で作成します：

   - **方法 A (最も簡単: Render の環境変数で作成)**:
     Render の **Environment** タブで以下の環境変数を追加します：
     - `DJANGO_SUPERUSER_USERNAME`: `admin` (または希望のユーザー名)
     - `DJANGO_SUPERUSER_PASSWORD`: *(設定したい管理者パスワード)*
     - `DJANGO_SUPERUSER_EMAIL`: `admin@example.com`
     保存して再デプロイすると、`build.sh` が自動的に管理者ユーザーを作成します！

   - **方法 B (手元の PC から Neon DB へ直接接続して作成)**:
     手元の PowerShell で Neon の `DATABASE_URL` を指定してコマンドを実行します：
     ```powershell
     $env:DATABASE_URL="postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
     .\venv\Scripts\python.exe manage.py createsuperuser
     ```

---

## Step 5: 今後の更新手順 (Update Workflow)

ローカルでコードを修正・アップデートした場合は、GitHub に Push するだけで Render が自動検出して再デプロイを行います。

```powershell
# 1. 変更のコミットとプッシュ
git add .
git commit -m "新機能の追加・バグ修正"
git push origin main
```
Push 完了後、Render 上で自動的にビルドおよびデータベースマイグレーションが実行され、数分で本番環境に反映されます。

---

## ❓ トラブルシューティング

- **静的ファイル (CSS / JS) が反映されない場合**:
  - `config/settings.py` 内に `whitenoise.middleware.WhiteNoiseMiddleware` が有効になっているか、および `STATIC_ROOT` が設定されているか確認してください。
- **データベース接続エラー (OperationalError)**:
  - Render の `DATABASE_URL` に `?sslmode=require` が付与されているか、またパスワードやホスト名に誤りがないか確認してください。
- **Render の無料プランの仕様（スリープ機能）**:
  - Render の無料プランは、15分間アクセスがないと自動的にスリープ状態になります。次回アクセス時に起動するまで50秒程度かかる場合がありますが、故障ではなく仕様です。
