create table if not exists public.ideas (
    id uuid primary key,
    title text not null,
    category text not null,
    summary text not null,
    user_scene text not null,
    value text not null,
    detail text not null default '',
    image_path text not null default '',
    external_url text not null default '',
    status text not null default '検証前',
    created_at timestamptz not null default now()
);

create table if not exists public.events (
    id uuid primary key,
    idea_id uuid not null references public.ideas(id) on delete cascade,
    event_type text not null check (event_type in ('impression', 'click', 'like')),
    session_id text not null,
    created_at timestamptz not null default now()
);

create table if not exists public.comments (
    id uuid primary key,
    idea_id uuid not null references public.ideas(id) on delete cascade,
    comment text not null,
    concern_level integer not null check (concern_level between 1 and 5),
    created_at timestamptz not null default now()
);

create table if not exists public.ratings (
    id uuid primary key,
    idea_id uuid not null references public.ideas(id) on delete cascade,
    rating integer not null check (rating between 1 and 5),
    session_id text not null,
    created_at timestamptz not null default now()
);

create index if not exists events_idea_id_idx on public.events(idea_id);
create index if not exists events_session_like_idx on public.events(idea_id, session_id, event_type, created_at desc);
create index if not exists comments_idea_id_idx on public.comments(idea_id);
create index if not exists ratings_idea_id_idx on public.ratings(idea_id);
create index if not exists ratings_session_idx on public.ratings(idea_id, session_id, created_at desc);

alter table public.ideas enable row level security;
alter table public.events enable row level security;
alter table public.comments enable row level security;
alter table public.ratings enable row level security;

drop policy if exists "service role can manage ideas" on public.ideas;
drop policy if exists "service role can manage events" on public.events;
drop policy if exists "service role can manage comments" on public.comments;
drop policy if exists "service role can manage ratings" on public.ratings;

create policy "service role can manage ideas"
on public.ideas for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

create policy "service role can manage events"
on public.events for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

create policy "service role can manage comments"
on public.comments for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

create policy "service role can manage ratings"
on public.ratings for all
using (auth.role() = 'service_role')
with check (auth.role() = 'service_role');

insert into storage.buckets (id, name, public)
values ('idea-images', 'idea-images', true)
on conflict (id) do update set public = true;
