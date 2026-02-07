# lab-kiosk
## clone後(ブランチ新規作成後)に必要な操作
- .envの作成
```
SECRET_KEY=""
# DEBUG=True
DISCORD_WEBHOOK_URL=""
# Django
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=1

# PostgreSQL
POSTGRES_DB=labstore
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

- CLIでの操作
```powershell
# nodemoduleのインストール
docker compose run --rm frontend npm install
docker compose up
# マイグレーション
docker compose exec backend python manage.py showmigrations store
docker compose exec backend python manage.py migrate 
# 初期データの入力とスーパーユーザーの作成
docker compose exec backend python manage.py migrate 
docker compose run --rm backend python manage.py createsuperuser
```