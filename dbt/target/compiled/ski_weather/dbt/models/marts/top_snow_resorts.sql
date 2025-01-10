WITH combined_reports AS (
    SELECT *
    FROM "postgres"."public_staging"."stg_snotel"
    UNION ALL
    SELECT *
    FROM "postgres"."public_staging"."stg_weather_unlocked"
),

weekly_snow AS (
    SELECT
        resort_name,
        state,
        MAX(timestamp) as last_updated,
        MAX(new_snow_7d) as snow_last_7d,
        MAX(snow_depth) as current_snow_depth
    FROM combined_reports
    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
    GROUP BY resort_name, state
)

SELECT
    resort_name,
    state,
    snow_last_7d,
    current_snow_depth,
    last_updated
FROM weekly_snow
ORDER BY snow_last_7d DESC
LIMIT 10