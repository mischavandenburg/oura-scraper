"""Database schema definitions for Oura API data.

This module provides SQL schema for all Oura API v2 endpoints and
functions to initialize the database schema.
"""

import logging

import psycopg

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
-- Personal Info (single record, updated on each sync)
CREATE TABLE IF NOT EXISTS oura_personal_info (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255),
    age INTEGER,
    weight NUMERIC(5,2),
    height NUMERIC(5,2),
    biological_sex VARCHAR(20),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Activity
CREATE TABLE IF NOT EXISTS oura_daily_activity (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    score INTEGER,
    active_calories INTEGER,
    average_met_minutes NUMERIC(10,5),
    contributors JSONB,
    equivalent_walking_distance INTEGER,
    high_activity_met_minutes INTEGER,
    high_activity_time INTEGER,
    inactivity_alerts INTEGER,
    low_activity_met_minutes INTEGER,
    low_activity_time INTEGER,
    medium_activity_met_minutes INTEGER,
    medium_activity_time INTEGER,
    met JSONB,
    meters_to_target INTEGER,
    non_wear_time INTEGER,
    resting_time INTEGER,
    sedentary_met_minutes INTEGER,
    sedentary_time INTEGER,
    steps INTEGER,
    target_calories INTEGER,
    target_meters INTEGER,
    total_calories INTEGER,
    class_5_min TEXT,
    timestamp TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_activity_day ON oura_daily_activity(day);
CREATE INDEX IF NOT EXISTS idx_oura_daily_activity_score ON oura_daily_activity(score);
CREATE INDEX IF NOT EXISTS idx_oura_daily_activity_steps ON oura_daily_activity(steps);
CREATE INDEX IF NOT EXISTS idx_oura_daily_activity_timestamp ON oura_daily_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_daily_activity_contributors
    ON oura_daily_activity USING GIN(contributors);
CREATE INDEX IF NOT EXISTS idx_daily_activity_met ON oura_daily_activity USING GIN(met);

-- Daily Sleep
CREATE TABLE IF NOT EXISTS oura_daily_sleep (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    score INTEGER,
    contributors JSONB,
    timestamp TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_sleep_day ON oura_daily_sleep(day);
CREATE INDEX IF NOT EXISTS idx_oura_daily_sleep_score ON oura_daily_sleep(score);

-- Daily Readiness
CREATE TABLE IF NOT EXISTS oura_daily_readiness (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    score INTEGER,
    contributors JSONB,
    temperature_deviation NUMERIC(10,5),
    temperature_trend_deviation NUMERIC(10,5),
    timestamp TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_readiness_day ON oura_daily_readiness(day);
CREATE INDEX IF NOT EXISTS idx_oura_daily_readiness_score ON oura_daily_readiness(score);
CREATE INDEX IF NOT EXISTS idx_oura_daily_readiness_timestamp ON oura_daily_readiness(timestamp);
CREATE INDEX IF NOT EXISTS idx_daily_readiness_contributors
    ON oura_daily_readiness USING GIN(contributors);

-- Daily Stress
CREATE TABLE IF NOT EXISTS oura_daily_stress (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    stress_high INTEGER,
    recovery_high INTEGER,
    day_summary VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_stress_day ON oura_daily_stress(day);

-- Daily SpO2
CREATE TABLE IF NOT EXISTS oura_daily_spo2 (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    spo2_percentage JSONB,
    breathing_disturbance_index NUMERIC(10,5)
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_spo2_day ON oura_daily_spo2(day);

-- Daily Cardiovascular Age
CREATE TABLE IF NOT EXISTS oura_daily_cardiovascular_age (
    id VARCHAR(255),
    day DATE PRIMARY KEY,
    vascular_age INTEGER
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_cardiovascular_age_vascular_age
    ON oura_daily_cardiovascular_age(vascular_age);

-- Daily Resilience
CREATE TABLE IF NOT EXISTS oura_daily_resilience (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    level VARCHAR(50),
    contributors JSONB
);

CREATE INDEX IF NOT EXISTS idx_oura_daily_resilience_day ON oura_daily_resilience(day);
CREATE INDEX IF NOT EXISTS idx_oura_daily_resilience_level ON oura_daily_resilience(level);

-- Sleep (detailed sleep periods)
CREATE TABLE IF NOT EXISTS oura_sleep_data (
    id UUID PRIMARY KEY,
    day DATE,
    bedtime_start TIMESTAMP WITH TIME ZONE,
    bedtime_end TIMESTAMP WITH TIME ZONE,
    average_breath DOUBLE PRECISION,
    average_heart_rate DOUBLE PRECISION,
    average_hrv INTEGER,
    awake_time INTEGER,
    deep_sleep_duration INTEGER,
    efficiency INTEGER,
    heart_rate JSONB,
    hrv JSONB,
    latency INTEGER,
    light_sleep_duration INTEGER,
    low_battery_alert BOOLEAN,
    lowest_heart_rate INTEGER,
    movement_30_sec TEXT,
    period INTEGER,
    readiness JSONB,
    readiness_score_delta INTEGER,
    rem_sleep_duration INTEGER,
    restless_periods INTEGER,
    sleep_phase_5_min TEXT,
    sleep_score_delta INTEGER,
    sleep_algorithm_version VARCHAR(10),
    time_in_bed INTEGER,
    total_sleep_duration INTEGER,
    type VARCHAR(20),
    ring_id VARCHAR(255),
    sleep_analysis_reason VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_oura_sleep_data_day ON oura_sleep_data(day);
CREATE INDEX IF NOT EXISTS idx_oura_sleep_data_bedtime_start ON oura_sleep_data(bedtime_start);

-- Sleep Time (optimal bedtime recommendations)
CREATE TABLE IF NOT EXISTS oura_sleep_time (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    optimal_bedtime JSONB,
    recommendation VARCHAR(50),
    status VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_oura_sleep_time_day ON oura_sleep_time(day);

-- Heart Rate (5-minute intervals)
CREATE TABLE IF NOT EXISTS oura_heart_rate (
    timestamp TIMESTAMP WITH TIME ZONE PRIMARY KEY,
    bpm INTEGER NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_oura_heart_rate_bpm ON oura_heart_rate(bpm);
CREATE INDEX IF NOT EXISTS idx_oura_heart_rate_source ON oura_heart_rate(source);

-- VO2 Max
CREATE TABLE IF NOT EXISTS oura_vo2_max (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    vo2_max NUMERIC(10,5),
    timestamp TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_oura_vo2_max_day ON oura_vo2_max(day);

-- Workouts
CREATE TABLE IF NOT EXISTS oura_workout (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    activity VARCHAR(100),
    calories NUMERIC(10,2),
    distance NUMERIC(10,2),
    start_datetime TIMESTAMP WITH TIME ZONE,
    end_datetime TIMESTAMP WITH TIME ZONE,
    intensity VARCHAR(50),
    label VARCHAR(255),
    source VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_oura_workout_day ON oura_workout(day);
CREATE INDEX IF NOT EXISTS idx_oura_workout_activity ON oura_workout(activity);
CREATE INDEX IF NOT EXISTS idx_oura_workout_start_datetime ON oura_workout(start_datetime);

-- Sessions (meditation, breathing, naps)
CREATE TABLE IF NOT EXISTS oura_session (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    start_datetime TIMESTAMP WITH TIME ZONE,
    end_datetime TIMESTAMP WITH TIME ZONE,
    type VARCHAR(50),
    mood VARCHAR(50),
    heart_rate JSONB,
    hrv JSONB,
    motion_count JSONB
);

CREATE INDEX IF NOT EXISTS idx_oura_session_day ON oura_session(day);
CREATE INDEX IF NOT EXISTS idx_oura_session_type ON oura_session(type);
CREATE INDEX IF NOT EXISTS idx_oura_session_start_datetime ON oura_session(start_datetime);

-- Enhanced Tags
CREATE TABLE IF NOT EXISTS oura_enhanced_tag (
    id UUID PRIMARY KEY,
    day DATE NOT NULL,
    tag_type_code VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    start_day DATE,
    end_day DATE,
    comment TEXT
);

CREATE INDEX IF NOT EXISTS idx_oura_enhanced_tag_day ON oura_enhanced_tag(day);
CREATE INDEX IF NOT EXISTS idx_oura_enhanced_tag_tag_type_code ON oura_enhanced_tag(tag_type_code);

-- Ring Configuration
CREATE TABLE IF NOT EXISTS oura_ring_configuration (
    id UUID PRIMARY KEY,
    color VARCHAR(50),
    design VARCHAR(50),
    firmware_version VARCHAR(50),
    hardware_type VARCHAR(50),
    set_up_at TIMESTAMP WITH TIME ZONE,
    size INTEGER
);

-- Rest Mode Period
CREATE TABLE IF NOT EXISTS oura_rest_mode_period (
    id UUID PRIMARY KEY,
    start_day DATE,
    end_day DATE,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    episodes JSONB
);

CREATE INDEX IF NOT EXISTS idx_oura_rest_mode_period_start_day ON oura_rest_mode_period(start_day);
"""


def init_schema(conn: psycopg.Connection[tuple[object, ...]]) -> None:
    """Initialize the database schema.

    Creates all tables and indexes if they don't exist.
    Safe to run multiple times (idempotent).

    Args:
        conn: PostgreSQL database connection
    """
    logger.info("Initializing database schema...")
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
    logger.info("Database schema initialized successfully")


def get_schema_sql() -> str:
    """Return the raw SQL schema for inspection or manual execution.

    Returns:
        The complete SQL schema as a string
    """
    return SCHEMA_SQL
