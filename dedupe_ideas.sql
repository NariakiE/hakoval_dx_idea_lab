with idea_scores as (
    select
        i.id,
        i.title,
        i.created_at,
        coalesce(e.event_count, 0) as event_count,
        coalesce(c.comment_count, 0) as comment_count,
        coalesce(r.rating_count, 0) as rating_count
    from public.ideas i
    left join (
        select idea_id, count(*) as event_count
        from public.events
        group by idea_id
    ) e on e.idea_id = i.id
    left join (
        select idea_id, count(*) as comment_count
        from public.comments
        group by idea_id
    ) c on c.idea_id = i.id
    left join (
        select idea_id, count(*) as rating_count
        from public.ratings
        group by idea_id
    ) r on r.idea_id = i.id
),
ranked as (
    select
        id,
        row_number() over (
            partition by title
            order by
                event_count desc,
                comment_count desc,
                rating_count desc,
                created_at desc,
                id
        ) as keep_rank
    from idea_scores
)
delete from public.ideas
where id in (
    select id
    from ranked
    where keep_rank > 1
);
