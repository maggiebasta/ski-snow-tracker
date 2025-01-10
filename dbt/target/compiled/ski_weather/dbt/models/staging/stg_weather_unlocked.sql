WITH source AS (
    SELECT *
    FROM "postgres"."public"."snow_reports"
    WHERE data_source = 'WeatherUnlocked'
)

SELECT
    id,
    resort_name,
    state,
    timestamp,
    snow_depth,
    new_snow_24h,
    new_snow_72h,
    new_snow_7d,
    elevation,
    temperature
FROM source