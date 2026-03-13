create table if not exists public.meter_readings (
  month_key text primary key,
  calculation_year integer not null check (calculation_year >= 2026),
  calculation_month integer not null check (calculation_month between 1 and 12),
  cold_water numeric not null,
  hot_water numeric not null,
  electricity_t1 numeric not null,
  electricity_t2 numeric not null,
  electricity_t3 numeric not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

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
