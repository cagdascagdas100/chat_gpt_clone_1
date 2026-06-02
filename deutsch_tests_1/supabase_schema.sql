-- Supabase schema for deutsch_tests_1
-- Run this in Supabase SQL Editor.
-- Do NOT expose your service_role key in frontend code.

create table if not exists public.deutsch_test_results (
  id uuid primary key default gen_random_uuid(),
  share_id text not null unique,
  device_id text not null,
  test_slug text not null,
  test_title text not null,
  topic text,
  length_label text,
  score integer not null,
  total integer not null,
  percent integer not null,
  wrong jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists deutsch_test_results_device_created_idx
on public.deutsch_test_results (device_id, created_at desc);

create index if not exists deutsch_test_results_share_idx
on public.deutsch_test_results (share_id);

alter table public.deutsch_test_results enable row level security;

-- Allow public anon inserts from the web app.
-- This is acceptable for a simple learning app, but it means anyone with the site can insert rows.
drop policy if exists "Allow anon insert deutsch test results" on public.deutsch_test_results;
create policy "Allow anon insert deutsch test results"
on public.deutsch_test_results
for insert
to anon
with check (
  share_id is not null
  and device_id is not null
  and test_slug is not null
  and score >= 0
  and total > 0
  and percent >= 0
  and percent <= 100
);

-- Do not allow direct table-wide select for anon.
drop policy if exists "Allow anon select deutsch test results" on public.deutsch_test_results;

-- Public function: get one result by share id for shared result links.
create or replace function public.get_deutsch_result(p_share_id text)
returns table (
  share_id text,
  test_title text,
  topic text,
  length_label text,
  score integer,
  total integer,
  percent integer,
  wrong jsonb,
  created_at timestamptz
)
language sql
security definer
set search_path = public
as $$
  select share_id, test_title, topic, length_label, score, total, percent, wrong, created_at
  from public.deutsch_test_results
  where share_id = p_share_id
  limit 1;
$$;

grant execute on function public.get_deutsch_result(text) to anon;

-- Public function: get history for the current browser/device id.
create or replace function public.get_deutsch_history(p_device_id text)
returns table (
  share_id text,
  test_title text,
  topic text,
  length_label text,
  score integer,
  total integer,
  percent integer,
  wrong jsonb,
  created_at timestamptz
)
language sql
security definer
set search_path = public
as $$
  select share_id, test_title, topic, length_label, score, total, percent, wrong, created_at
  from public.deutsch_test_results
  where device_id = p_device_id
  order by created_at desc
  limit 50;
$$;

grant execute on function public.get_deutsch_history(text) to anon;

-- Optional maintenance: delete old results manually if needed.
-- delete from public.deutsch_test_results where created_at < now() - interval '180 days';
