# Daily Huddle

Daily Huddle is a Vercel-ready web app for Zodiac HRC's morning data entry flow. The frontend is static, and the backend uses Python Vercel Functions under `api/` to read and write entries in Supabase.

## Features

- Employee-facing morning huddle form
- Dedicated Supabase columns for each input parameter
- Recent submission history
- CSV export endpoint at `/api/export`
- No secrets committed to GitHub

## Environment variables

Set these in Vercel Project Settings before deploying:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

For local development, copy `.env.example` to `.env.local` and fill in the real values.

## Supabase table

Run the SQL below in your Supabase SQL editor:

```sql
create table if not exists public.daily_huddle_entries (
  id text primary key,
  employee_name text not null,
  entry_date date not null,
  notes text default '',
  submitted_at timestamptz not null,
  workbook_name text not null,
  sheet_name text not null,
  monthly_revenue_value_target numeric,
  monthly_revenue_value_achieved_pipeline numeric,
  monthly_revenue_number_target numeric,
  monthly_revenue_number_achieved_pipeline numeric,
  monthly_revenue_achieved_percent_target numeric,
  monthly_revenue_achieved_percent_actual numeric,
  monthly_booking_value_high numeric,
  monthly_booking_value_medium numeric,
  monthly_booking_number_high numeric,
  monthly_booking_number_medium numeric,
  monthly_booking_total_value numeric,
  monthly_booking_total_number numeric,
  yesterdays_poa_target numeric,
  yesterdays_poa_achieved numeric,
  mtd_poa_target numeric,
  mtd_poa_achieved numeric,
  yesterdays_initial_interview_target numeric,
  yesterdays_initial_interview_achieved numeric,
  yesterdays_final_interview_target numeric,
  yesterdays_final_interview_achieved numeric,
  mtd_initial_interview_target numeric,
  mtd_initial_interview_achieved numeric,
  mtd_final_interview_target numeric,
  mtd_final_interview_achieved numeric,
  total_interviews_target numeric,
  total_interviews_achieved numeric,
  values jsonb not null default '{}'::jsonb
);

create index if not exists daily_huddle_entries_submitted_at_idx
  on public.daily_huddle_entries (submitted_at desc);
```

## Deployment notes

- Vercel serves `index.html`, `app.js`, and `styles.css` as static assets
- `api/template.py`, `api/submissions.py`, and `api/export.py` handle the backend endpoints
- Secrets should be added only in Vercel environment variables, not in committed files
