alter table public.meter_readings
add column if not exists cold_water_tariff numeric,
add column if not exists hot_water_tariff numeric,
add column if not exists wastewater_tariff numeric,
add column if not exists electricity_t1_tariff numeric,
add column if not exists electricity_t2_tariff numeric,
add column if not exists electricity_t3_tariff numeric,
add column if not exists delta_cold_water numeric,
add column if not exists delta_hot_water numeric,
add column if not exists delta_electricity_t1 numeric,
add column if not exists delta_electricity_t2 numeric,
add column if not exists delta_electricity_t3 numeric,
add column if not exists water_bill numeric,
add column if not exists electricity_bill numeric,
add column if not exists total_bill numeric;

update public.meter_readings
set
  cold_water_tariff = coalesce(cold_water_tariff, 65.77),
  hot_water_tariff = coalesce(hot_water_tariff, 312.50),
  wastewater_tariff = coalesce(wastewater_tariff, 51.62),
  electricity_t1_tariff = coalesce(electricity_t1_tariff, 10.23),
  electricity_t2_tariff = coalesce(electricity_t2_tariff, 3.71),
  electricity_t3_tariff = coalesce(electricity_t3_tariff, 7.16);

alter table public.meter_readings
alter column cold_water_tariff set not null,
alter column hot_water_tariff set not null,
alter column wastewater_tariff set not null,
alter column electricity_t1_tariff set not null,
alter column electricity_t2_tariff set not null,
alter column electricity_t3_tariff set not null;
