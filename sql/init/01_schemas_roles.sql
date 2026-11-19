-- Bootstrap: schemas and local least-privilege roles (TAD 3.4, 19.2).
-- Executed automatically when the postgres container initializes
-- (mounted into docker-entrypoint-initdb.d) or manually via psql.

create schema if not exists raw;
create schema if not exists staging;
create schema if not exists intermediate;
create schema if not exists core;
create schema if not exists marts;

-- Roles (idempotent)
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'warehouse_admin') then
    create role warehouse_admin login password 'warehouse_admin';
  end if;
  if not exists (select 1 from pg_roles where rolname = 'warehouse_loader') then
    create role warehouse_loader login password 'warehouse_loader';
  end if;
  if not exists (select 1 from pg_roles where rolname = 'warehouse_transformer') then
    create role warehouse_transformer login password 'warehouse_transformer';
  end if;
  if not exists (select 1 from pg_roles where rolname = 'metabase_reader') then
    create role metabase_reader login password 'metabase_reader';
  end if;
end $$;

grant all on schema raw to warehouse_admin;
grant usage, create on schema staging, intermediate, core, marts to warehouse_admin;
grant usage, select, insert on all tables in schema raw to warehouse_loader;
grant usage on schema raw to warehouse_transformer;
grant usage, create on schema staging, intermediate, core, marts to warehouse_transformer;
grant usage on schema marts to metabase_reader;
grant select on all tables in schema marts to metabase_reader;

alter default privileges in schema raw grant select, insert on tables to warehouse_loader;
alter default privileges in schema staging, intermediate, core, marts
  grant all on tables to warehouse_transformer;
alter default privileges in schema marts grant select on tables to metabase_reader;
