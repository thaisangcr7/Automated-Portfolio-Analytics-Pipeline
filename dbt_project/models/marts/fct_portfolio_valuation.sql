with prices as (

    select * from {{ ref('int_stock_prices_enriched') }}

),

holdings as (

    select * from {{ ref('stg_portfolio_holdings') }}

),

companies as (

    select * from {{ ref('dim_companies') }}

),

joined as (

    select
        p.price_date,
        p.ticker,
        c.company_name,
        c.sector,
        c.exchange,

        -- Price data
        p.open_price,
        p.high_price,
        p.low_price,
        p.close_price,
        p.volume,

        -- Moving averages
        p.ma_50d,
        p.ma_200d,
        p.daily_return_pct,

        -- Holdings data
        h.shares,
        h.cost_basis_per_share,
        h.purchase_date,

        -- Portfolio calculations
        round(h.shares * p.close_price, 2)                                            as market_value,
        round(h.shares * h.cost_basis_per_share, 2)                                   as total_cost,
        round((h.shares * p.close_price) - (h.shares * h.cost_basis_per_share), 2)   as unrealized_pnl,
        round(
            ((h.shares * p.close_price) - (h.shares * h.cost_basis_per_share))
            / nullif(h.shares * h.cost_basis_per_share, 0) * 100
        , 2)                                                                           as unrealized_pnl_pct

    from prices          p
    inner join holdings  h on p.ticker = h.ticker
    inner join companies c on p.ticker = c.ticker

)

select * from joined
