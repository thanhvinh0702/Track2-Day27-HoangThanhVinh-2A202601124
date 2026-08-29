-- Business invariant: monetary amounts must never be negative.
select *
from {{ ref('stg_orders') }}
where amount_usd < 0
