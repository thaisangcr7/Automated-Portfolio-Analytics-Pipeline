with stock_prices as (

    select * from {{ ref('stg_stock_prices') }}

),

with_moving_averages as (

    select
        price_date,
        ticker,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,

        -- 50-day moving average
        -- ROWS BETWEEN 49 PRECEDING AND CURRENT ROW means:
        -- "look at this row plus the 49 rows before it (50 total) and average the close price"
        round(
            avg(close_price) over (
                partition by ticker
                order by price_date
                rows between 49 preceding and current row
            ), 4
        ) as ma_50d,

        -- 200-day moving average — same logic but looking back 200 rows
        round(
            avg(close_price) over (
                partition by ticker
                order by price_date
                rows between 199 preceding and current row
            ), 4
        ) as ma_200d,

        -- Daily return: how much did the price change vs yesterday (%)
        round(
            (close_price - lag(close_price) over (
                partition by ticker
                order by price_date
            ))
            / nullif(lag(close_price) over (
                partition by ticker
                order by price_date
            ), 0) * 100
        , 2) as daily_return_pct

    from stock_prices

)

select * from with_moving_averages
