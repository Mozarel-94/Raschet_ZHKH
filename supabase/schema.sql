create table if not exists public.meter_readings (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  month_key text not null,
  calculation_year integer not null check (calculation_year >= 2026),
  calculation_month integer not null check (calculation_month between 1 and 12),
  cold_water numeric not null,
  hot_water numeric not null,
  electricity_t1 numeric not null,
  electricity_t2 numeric not null,
  electricity_t3 numeric not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (user_id, month_key)
);

create index if not exists meter_readings_user_month_idx
on public.meter_readings (user_id, calculation_year, calculation_month);

create or replace function public.set_meter_readings_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists meter_readings_set_updated_at on public.meter_readings;

create trigger meter_readings_set_updated_at
before update on public.meter_readings
for each row
execute function public.set_meter_readings_updated_at();

alter table public.meter_readings enable row level security;

create policy "Users can view their own meter readings"
on public.meter_readings
for select
to authenticated
using (auth.uid() = user_id);

create policy "Users can insert their own meter readings"
on public.meter_readings
for insert
to authenticated
with check (auth.uid() = user_id);

create policy "Users can update their own meter readings"
on public.meter_readings
for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
