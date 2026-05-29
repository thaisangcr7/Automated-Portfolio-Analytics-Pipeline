with holdings as (

    select distinct ticker, sector
    from {{ ref('stg_portfolio_holdings') }}

)

select
    ticker,

    case ticker
        when 'AAPL' then 'Apple Inc.'
        when 'MSFT' then 'Microsoft Corporation'
        when 'GOOG' then 'Alphabet Inc.'
        when 'JPM'  then 'JPMorgan Chase & Co.'
        when 'C'    then 'Citigroup Inc.'
        else ticker
    end as company_name,

    sector,

    case ticker
        when 'AAPL' then 'NASDAQ'
        when 'MSFT' then 'NASDAQ'
        when 'GOOG' then 'NASDAQ'
        when 'JPM'  then 'NYSE'
        when 'C'    then 'NYSE'
        else 'Unknown'
    end as exchange

from holdings
