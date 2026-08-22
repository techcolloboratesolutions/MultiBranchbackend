# Deploy Django backend to Vercel + Supabase Postgres

Vercel is serverless. Django can run, but you must set env vars and use the **transaction pooler**.

## 1. Vercel project settings

- Root Directory: leave empty if this **backend** repo is what you import
- Framework preset: Other
- After pushing `vercel.json` and `api/index.py`, Redeploy

## 2. Environment variables (Vercel → Settings → Environment Variables)

```
SECRET_KEY=<long random string>
DEBUG=False
ALLOWED_HOSTS=.vercel.app,localhost

DB_NAME=postgres
DB_USER=postgres.wozkhxrdaecpuhgccyfq
DB_PASSWORD=<Supabase database password>
DB_HOST=aws-0-ap-northeast-2.pooler.supabase.com
DB_PORT=6543
```

In Supabase: **Project Settings → Database → Connection string → Transaction pooler** (port **6543**).  
Do not use Session mode port 5432 on Vercel.

## 3. Create tables (run once on your PC)

Vercel will not run migrations for you. From this backend folder, with the same DB env vars:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
```

## 4. Check

- https://multi-branchbackend.vercel.app/ → `{"status":"ok"}`
- https://multi-branchbackend.vercel.app/api/health/ → `{"status":"ok"}`

If it is still 500, open Vercel → Project → Logs (or Deployment → Functions) and read the Python traceback.

## 5. Frontend

Set `VITE_API_BASE_URL=https://multi-branchbackend.vercel.app/api`
