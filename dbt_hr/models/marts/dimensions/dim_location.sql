select
    location_id,
    location,
    country,
    region,
    time_zone,
    latitude,
    longitude
from {{ ref('stg_dim_location') }}
