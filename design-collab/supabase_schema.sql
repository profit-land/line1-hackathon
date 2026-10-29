-- Design Collab — Supabase 스키마 (PostgreSQL)
-- 실행: Supabase Dashboard > SQL Editor 에 붙여넣기, 또는 supabase db push
-- RLS 전략: 가입(users 테이블에 존재)한 사용자 간 완전 공유.
--   - 클라이언트는 publishable key(anon)로 접속 → authenticated 로우 수준 정책 적용
--   - '팀' 개념은 projects.team_id 로 구분할 수 있는 구조만 마련 (기본값 1 = 기본 팀)
--   - Secret key는 어디에도 사용 안 함 (서버도 URL + publishable key 만)

-- ─── users ──────────────────────────────────────────────────────────────────
create table if not exists public.users (
    id          bigint generated always as identity primary key,
    name        text not null,
    email       text not null unique,
    is_admin    boolean not null default false,
    created_at  timestamptz not null default now()
);

-- ─── projects ───────────────────────────────────────────────────────────────
create table if not exists public.projects (
    id          bigint generated always as identity primary key,
    team_id     bigint not null default 1,   -- 팀별 접근 권한 구분용 (기본 팀 1)
    name        text not null,
    created_at  timestamptz not null default now()
);

-- ─── pages ──────────────────────────────────────────────────────────────────
create table if not exists public.pages (
    id            bigint generated always as identity primary key,
    project_id    bigint not null references public.projects(id) on delete cascade,
    name          text not null,
    html_content  text not null default '',
    sort_order    integer not null default 0,
    menu_name     text,
    updated_at    timestamptz not null default now(),
    unique (project_id, sort_order)
);

-- ─── menus ──────────────────────────────────────────────────────────────────
create table if not exists public.menus (
    id          bigint generated always as identity primary key,
    project_id  bigint not null references public.projects(id) on delete cascade,
    name        text not null,
    sort_order  integer not null default 0,
    created_at  timestamptz not null default now(),
    unique (project_id, name)
);

-- ─── descriptions (페이지당 1개) ────────────────────────────────────────────
create table if not exists public.descriptions (
    id            bigint generated always as identity primary key,
    page_id       bigint not null unique references public.pages(id) on delete cascade,
    content       text not null default '',
    author_name   text not null default '',
    author_email  text not null default '',
    updated_at    timestamptz not null default now()
);

-- ─── page_tags ──────────────────────────────────────────────────────────────
-- (comments가 이 테이블을 참조하므로 comments보다 먼저 만들어야 한다)
create table if not exists public.page_tags (
    id           bigint generated always as identity primary key,
    page_id      bigint not null references public.pages(id) on delete cascade,
    tag_number   integer not null,
    x_pct        double precision not null,
    y_pct        double precision not null,
    title        text not null default '',
    description  text not null default '',
    author_name  text not null default '',
    author_email text not null default '',
    is_resolved  boolean not null default false,
    created_at   timestamptz not null default now(),
    unique (page_id, tag_number)
);

-- ─── comments (화면 코멘트 + 태그 댓글 공용) ────────────────────────────────
create table if not exists public.comments (
    id             bigint generated always as identity primary key,
    page_id        bigint not null references public.pages(id) on delete cascade,
    author_name    text not null,
    content        text not null,
    author_email   text not null default '',
    x_pct          double precision,
    y_pct          double precision,
    parent_tag_id  bigint references public.page_tags(id) on delete cascade,
    is_checked     boolean not null default false,
    hidden         boolean not null default false,
    mention_email  text not null default '',
    created_at     timestamptz not null default now()
);

-- ─── memos ──────────────────────────────────────────────────────────────────
create table if not exists public.memos (
    id           bigint generated always as identity primary key,
    page_id      bigint not null references public.pages(id) on delete cascade,
    author_name  text not null,
    author_email text not null default '',
    content      text not null,
    is_private   boolean not null default false,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

-- ─── notifications ──────────────────────────────────────────────────────────
create table if not exists public.notifications (
    id         bigint generated always as identity primary key,
    user_email text not null,
    type       text not null,
    ref_id     bigint,
    message    text not null,
    is_read    boolean not null default false,
    created_at timestamptz not null default now()
);

-- 인덱스 (자주 쓰는 조회 조건)
create index if not exists idx_pages_project   on public.pages(project_id, sort_order);
create index if not exists idx_comments_page   on public.comments(page_id, created_at, id);
create index if not exists idx_comments_parent on public.comments(parent_tag_id);
create index if not exists idx_tags_page       on public.page_tags(page_id);
create index if not exists idx_memos_page      on public.memos(page_id);
create index if not exists idx_notif_user      on public.notifications(user_email, is_read);

-- ─── Row Level Security ─────────────────────────────────────────────────────
-- 이 앱은 '워크스페이스에 가입한 사람끼리 전부 공유' 모델이다.
-- anon 키로 접속하는 요청이 합법적인지 판단할 수단이 없으므로,
-- 모든 테이블을 authenticated/anonymous에게 열람·쓰기 허용한다.
-- (Secret key 없이 publishable key만 쓴다는 전제 하에 가장 단순하고 안전한 형태.)

alter table public.users         enable row level security;
alter table public.projects      enable row level security;
alter table public.pages         enable row level security;
alter table public.menus         enable row level security;
alter table public.descriptions  enable row level security;
alter table public.comments      enable row level security;
alter table public.page_tags     enable row level security;
alter table public.memos         enable row level security;
alter table public.notifications enable row level security;

do $$
declare
    t text;
begin
    foreach t in array array['users','projects','pages','menus','descriptions',
                             'comments','page_tags','memos','notifications']
    loop
        execute format('drop policy if exists "%s_all" on public.%I', t, t);
        execute format('create policy "%s_all" on public.%I for all to anon, authenticated using (true) with check (true)', t, t);
    end loop;
end $$;

-- updated_at 자동 갱신 트리거 (SQLite datetime('now','localtime') 동작 재현)
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at := now();
    return new;
end $$;

drop trigger if exists trg_pages_updated on public.pages;
create trigger trg_pages_updated before update on public.pages
for each row execute function public.set_updated_at();

drop trigger if exists trg_desc_updated on public.descriptions;
create trigger trg_desc_updated before update on public.descriptions
for each row execute function public.set_updated_at();

drop trigger if exists trg_memo_updated on public.memos;
create trigger trg_memo_updated before update on public.memos
for each row execute function public.set_updated_at();
