with source as (

    select * from {{ source('raw', 'stock_prices') }}

),

deduplicated as (

    select
        date::date                as price_date,
        ticker,
        open::numeric(12, 4)     as open_price,
        high::numeric(12, 4)     as high_price,
        low::numeric(12, 4)      as low_price,
        close::numeric(12, 4)    as close_price,
        volume::bigint           as volume,
        extracted_at,

        -- If the script ran twice on the same day, keep only the latest row
        row_number() over (
            partition by date::date, ticker
            order by extracted_at desc
        ) as row_num

    from source
    where date    is not null
      and ticker  is not null
      and close   is not null

)

select
    -- Surrogate key: unique identifier for each price_date + ticker row
    price_date::text || '-' || ticker  as stock_id,
    price_date,
    ticker,
    open_price,
    high_price,
    low_price,
    close_price,
    volume

from deduplicated
where row_num = 1
