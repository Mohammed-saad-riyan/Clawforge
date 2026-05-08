-- ClawForge Supabase Schema
-- Run this in your Supabase SQL Editor

-- ======================
-- User Profiles Extension
-- ======================
-- Extends Supabase Auth users with additional profile data

create table if not exists public.user_profiles (
    id uuid references auth.users on delete cascade primary key,
    email text,
    full_name text,
    avatar_url text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- ======================
-- Projects Table
-- ======================
-- Stores generated Flutter app projects

create table if not exists public.projects (
    id text primary key,
    user_id uuid references auth.users on delete cascade,
    app_name text not null,
    app_idea text,
    target_users text,
    features text,
    ui_design text,
    full_spec jsonb default '{}'::jsonb,
    github_repo text,
    total_cost_cents integer default 0,
    iteration_count integer default 0,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Index for faster user queries
create index if not exists idx_projects_user_id on public.projects(user_id);
create index if not exists idx_projects_github_repo on public.projects(github_repo);

-- ======================
-- Project Files Table
-- ======================
-- Stores generated code files for each project

create table if not exists public.project_files (
    id uuid default gen_random_uuid() primary key,
    project_id text references public.projects on delete cascade,
    path text not null,
    content text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now()),
    unique(project_id, path)
);

-- Index for faster file queries
create index if not exists idx_project_files_project_id on public.project_files(project_id);

-- ======================
-- Chat Messages Table
-- ======================
-- Stores conversation history for iterative development

create table if not exists public.chat_messages (
    id uuid default gen_random_uuid() primary key,
    project_id text references public.projects on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    files_changed text[] default '{}',
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Index for faster message queries
create index if not exists idx_chat_messages_project_id on public.chat_messages(project_id);

-- ======================
-- Enable Row Level Security
-- ======================

alter table public.user_profiles enable row level security;
alter table public.projects enable row level security;
alter table public.project_files enable row level security;
alter table public.chat_messages enable row level security;

-- ======================
-- RLS Policies
-- ======================

-- User Profiles
create policy "Users can view own profile" on public.user_profiles
    for select using (auth.uid() = id);

create policy "Users can update own profile" on public.user_profiles
    for update using (auth.uid() = id);

create policy "Users can insert own profile" on public.user_profiles
    for insert with check (auth.uid() = id);

-- Projects
create policy "Users can view own projects" on public.projects
    for select using (auth.uid() = user_id);

create policy "Users can insert own projects" on public.projects
    for insert with check (auth.uid() = user_id);

create policy "Users can update own projects" on public.projects
    for update using (auth.uid() = user_id);

create policy "Users can delete own projects" on public.projects
    for delete using (auth.uid() = user_id);

-- Project Files (access via project ownership)
create policy "Users can view own project files" on public.project_files
    for select using (
        exists (
            select 1 from public.projects
            where projects.id = project_files.project_id
            and projects.user_id = auth.uid()
        )
    );

create policy "Users can insert own project files" on public.project_files
    for insert with check (
        exists (
            select 1 from public.projects
            where projects.id = project_files.project_id
            and projects.user_id = auth.uid()
        )
    );

create policy "Users can update own project files" on public.project_files
    for update using (
        exists (
            select 1 from public.projects
            where projects.id = project_files.project_id
            and projects.user_id = auth.uid()
        )
    );

create policy "Users can delete own project files" on public.project_files
    for delete using (
        exists (
            select 1 from public.projects
            where projects.id = project_files.project_id
            and projects.user_id = auth.uid()
        )
    );

-- Chat Messages (access via project ownership)
create policy "Users can view own chat messages" on public.chat_messages
    for select using (
        exists (
            select 1 from public.projects
            where projects.id = chat_messages.project_id
            and projects.user_id = auth.uid()
        )
    );

create policy "Users can insert own chat messages" on public.chat_messages
    for insert with check (
        exists (
            select 1 from public.projects
            where projects.id = chat_messages.project_id
            and projects.user_id = auth.uid()
        )
    );

-- ======================
-- Functions
-- ======================

-- Auto-create user profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.user_profiles (id, email)
    values (new.id, new.email);
    return new;
end;
$$ language plpgsql security definer;

-- Trigger to create profile on user signup
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- Auto-update updated_at timestamp
create or replace function public.update_updated_at()
returns trigger as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$ language plpgsql;

-- Triggers for updated_at
drop trigger if exists update_user_profiles_updated_at on public.user_profiles;
create trigger update_user_profiles_updated_at
    before update on public.user_profiles
    for each row execute procedure public.update_updated_at();

drop trigger if exists update_projects_updated_at on public.projects;
create trigger update_projects_updated_at
    before update on public.projects
    for each row execute procedure public.update_updated_at();

drop trigger if exists update_project_files_updated_at on public.project_files;
create trigger update_project_files_updated_at
    before update on public.project_files
    for each row execute procedure public.update_updated_at();

-- ======================
-- Service Role Bypass (for server-side operations)
-- ======================
-- Note: The service role key bypasses RLS automatically.
-- These policies allow the service role to access all data.

create policy "Service role can do anything on user_profiles" on public.user_profiles
    for all using (auth.jwt()->>'role' = 'service_role');

create policy "Service role can do anything on projects" on public.projects
    for all using (auth.jwt()->>'role' = 'service_role');

create policy "Service role can do anything on project_files" on public.project_files
    for all using (auth.jwt()->>'role' = 'service_role');

create policy "Service role can do anything on chat_messages" on public.chat_messages
    for all using (auth.jwt()->>'role' = 'service_role');
