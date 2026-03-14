alter table public.meter_readings
add column if not exists user_id uuid references auth.users (id) on delete cascade;

update public.meter_readings
set user_id = (
  select id
  from auth.users
  order by created_at
  limit 1
)
where user_id is null;

alter table public.meter_readings
alter column user_id set not null;

alter table public.meter_readings
drop constraint if exists meter_readings_pkey;

alter table public.meter_readings
add column if not exists id bigint generated always as identity;

alter table public.meter_readings
add constraint meter_readings_pkey primary key (id);

drop index if exists meter_readings_user_month_idx;
create index if not exists meter_readings_user_month_idx
on public.meter_readings (user_id, calculation_year, calculation_month);

alter table public.meter_readings
drop constraint if exists meter_readings_user_id_month_key_key;

alter table public.meter_readings
add constraint meter_readings_user_id_month_key_key unique (user_id, month_key);

alter table public.meter_readings enable row level security;

drop policy if exists "Users can view their own meter readings" on public.meter_readings;
create policy "Users can view their own meter readings"
on public.meter_readings
for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can insert their own meter readings" on public.meter_readings;
create policy "Users can insert their own meter readings"
on public.meter_readings
for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can update their own meter readings" on public.meter_readings;
create policy "Users can update their own meter readings"
on public.meter_readings
for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
