with source as (

    select * from {{ ref('portfolio_holdings') }}

)

select
    ticker,
    shares::numeric(10, 2)      as shares,
    cost_basis::numeric(10, 2)  as cost_basis_per_share,
    purchase_date::date         as purchase_date,
    sector

from source
