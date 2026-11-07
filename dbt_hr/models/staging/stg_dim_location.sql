-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "location_id",
    "location",
    "country",
    "region",
    "time_zone",
    "latitude",
    "longitude"
from {{ source('raw_hr', 'dim_location') }}
