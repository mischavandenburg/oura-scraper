"""Database operations for storing Oura API data."""

import logging
from typing import Any

import psycopg
from psycopg.types.json import Json

logger = logging.getLogger(__name__)


def upsert_personal_info(conn: psycopg.Connection[tuple[object, ...]], data: dict[str, Any]) -> None:
    """Upsert personal info record.

    Args:
        conn: Database connection
        data: Personal info data from Oura API
    """
    sql = """
        INSERT INTO oura_personal_info (
            id, email, age, weight, height, biological_sex, updated_at
        ) VALUES (
            %(id)s, %(email)s, %(age)s, %(weight)s, %(height)s, %(biological_sex)s, NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            age = EXCLUDED.age,
            weight = EXCLUDED.weight,
            height = EXCLUDED.height,
            biological_sex = EXCLUDED.biological_sex,
            updated_at = NOW()
    """

    with conn.cursor() as cur:
        cur.execute(sql, data)

    conn.commit()
    logger.info("Upserted personal info for user %s", data.get("id"))


def upsert_daily_activity(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert daily activity records.

    Extracts contributor fields from JSONB into individual columns for Grafana.

    Args:
        conn: Database connection
        records: List of daily activity records from Oura API

    Returns:
        Number of records upserted
    """
    if not records:
        return 0

    sql = """
        INSERT INTO oura_daily_activity (
            id, day, score, active_calories, average_met_minutes,
            stay_active, move_every_hour, meet_daily_targets,
            training_frequency, training_volume, recovery_time,
            equivalent_walking_distance, high_activity_met_minutes, high_activity_time,
            inactivity_alerts, low_activity_met_minutes, low_activity_time,
            medium_activity_met_minutes, medium_activity_time, met, meters_to_target,
            non_wear_time, resting_time, sedentary_met_minutes, sedentary_time,
            steps, target_calories, target_meters, total_calories, class_5_min, timestamp
        ) VALUES (
            %(id)s, %(day)s, %(score)s, %(active_calories)s, %(average_met_minutes)s,
            %(stay_active)s, %(move_every_hour)s, %(meet_daily_targets)s,
            %(training_frequency)s, %(training_volume)s, %(recovery_time)s,
            %(equivalent_walking_distance)s, %(high_activity_met_minutes)s,
            %(high_activity_time)s, %(inactivity_alerts)s, %(low_activity_met_minutes)s,
            %(low_activity_time)s, %(medium_activity_met_minutes)s, %(medium_activity_time)s,
            %(met)s, %(meters_to_target)s, %(non_wear_time)s, %(resting_time)s,
            %(sedentary_met_minutes)s, %(sedentary_time)s, %(steps)s, %(target_calories)s,
            %(target_meters)s, %(total_calories)s, %(class_5_min)s, %(timestamp)s
        )
        ON CONFLICT (id) DO UPDATE SET
            score = EXCLUDED.score,
            active_calories = EXCLUDED.active_calories,
            average_met_minutes = EXCLUDED.average_met_minutes,
            stay_active = EXCLUDED.stay_active,
            move_every_hour = EXCLUDED.move_every_hour,
            meet_daily_targets = EXCLUDED.meet_daily_targets,
            training_frequency = EXCLUDED.training_frequency,
            training_volume = EXCLUDED.training_volume,
            recovery_time = EXCLUDED.recovery_time,
            equivalent_walking_distance = EXCLUDED.equivalent_walking_distance,
            high_activity_met_minutes = EXCLUDED.high_activity_met_minutes,
            high_activity_time = EXCLUDED.high_activity_time,
            inactivity_alerts = EXCLUDED.inactivity_alerts,
            low_activity_met_minutes = EXCLUDED.low_activity_met_minutes,
            low_activity_time = EXCLUDED.low_activity_time,
            medium_activity_met_minutes = EXCLUDED.medium_activity_met_minutes,
            medium_activity_time = EXCLUDED.medium_activity_time,
            met = EXCLUDED.met,
            meters_to_target = EXCLUDED.meters_to_target,
            non_wear_time = EXCLUDED.non_wear_time,
            resting_time = EXCLUDED.resting_time,
            sedentary_met_minutes = EXCLUDED.sedentary_met_minutes,
            sedentary_time = EXCLUDED.sedentary_time,
            steps = EXCLUDED.steps,
            target_calories = EXCLUDED.target_calories,
            target_meters = EXCLUDED.target_meters,
            total_calories = EXCLUDED.total_calories,
            class_5_min = EXCLUDED.class_5_min,
            timestamp = EXCLUDED.timestamp
    """

    with conn.cursor() as cur:
        for record in records:
            # Extract contributor fields from nested JSONB
            contributors = record.get("contributors") or {}
            params = {
                **record,
                "stay_active": contributors.get("stay_active"),
                "move_every_hour": contributors.get("move_every_hour"),
                "meet_daily_targets": contributors.get("meet_daily_targets"),
                "training_frequency": contributors.get("training_frequency"),
                "training_volume": contributors.get("training_volume"),
                "recovery_time": contributors.get("recovery_time"),
                "met": Json(record.get("met")) if record.get("met") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d daily activity records", len(records))
    return len(records)


def upsert_daily_sleep(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert daily sleep records.

    Extracts contributor fields from JSONB into individual columns for Grafana.
    """
    if not records:
        return 0

    sql = """
        INSERT INTO oura_daily_sleep (
            id, day, score, deep_sleep, efficiency, latency,
            rem_sleep, restfulness, timing, total_sleep, timestamp
        )
        VALUES (
            %(id)s, %(day)s, %(score)s, %(deep_sleep)s, %(efficiency)s, %(latency)s,
            %(rem_sleep)s, %(restfulness)s, %(timing)s, %(total_sleep)s, %(timestamp)s
        )
        ON CONFLICT (id) DO UPDATE SET
            score = EXCLUDED.score,
            deep_sleep = EXCLUDED.deep_sleep,
            efficiency = EXCLUDED.efficiency,
            latency = EXCLUDED.latency,
            rem_sleep = EXCLUDED.rem_sleep,
            restfulness = EXCLUDED.restfulness,
            timing = EXCLUDED.timing,
            total_sleep = EXCLUDED.total_sleep,
            timestamp = EXCLUDED.timestamp
    """

    with conn.cursor() as cur:
        for record in records:
            # Extract contributor fields from nested JSONB
            contributors = record.get("contributors") or {}
            params = {
                **record,
                "deep_sleep": contributors.get("deep_sleep"),
                "efficiency": contributors.get("efficiency"),
                "latency": contributors.get("latency"),
                "rem_sleep": contributors.get("rem_sleep"),
                "restfulness": contributors.get("restfulness"),
                "timing": contributors.get("timing"),
                "total_sleep": contributors.get("total_sleep"),
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d daily sleep records", len(records))
    return len(records)


def upsert_daily_readiness(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert daily readiness records.

    Extracts contributor fields from JSONB into individual columns for Grafana.
    """
    if not records:
        return 0

    sql = """
        INSERT INTO oura_daily_readiness (
            id, day, score, activity_balance, body_temperature, hrv_balance,
            previous_day_activity, previous_night, recovery_index,
            resting_heart_rate, sleep_balance, sleep_regularity,
            temperature_deviation, temperature_trend_deviation, timestamp
        )
        VALUES (
            %(id)s, %(day)s, %(score)s, %(activity_balance)s, %(body_temperature)s,
            %(hrv_balance)s, %(previous_day_activity)s, %(previous_night)s,
            %(recovery_index)s, %(resting_heart_rate)s, %(sleep_balance)s,
            %(sleep_regularity)s, %(temperature_deviation)s,
            %(temperature_trend_deviation)s, %(timestamp)s
        )
        ON CONFLICT (id) DO UPDATE SET
            score = EXCLUDED.score,
            activity_balance = EXCLUDED.activity_balance,
            body_temperature = EXCLUDED.body_temperature,
            hrv_balance = EXCLUDED.hrv_balance,
            previous_day_activity = EXCLUDED.previous_day_activity,
            previous_night = EXCLUDED.previous_night,
            recovery_index = EXCLUDED.recovery_index,
            resting_heart_rate = EXCLUDED.resting_heart_rate,
            sleep_balance = EXCLUDED.sleep_balance,
            sleep_regularity = EXCLUDED.sleep_regularity,
            temperature_deviation = EXCLUDED.temperature_deviation,
            temperature_trend_deviation = EXCLUDED.temperature_trend_deviation,
            timestamp = EXCLUDED.timestamp
    """

    with conn.cursor() as cur:
        for record in records:
            # Extract contributor fields from nested JSONB
            contributors = record.get("contributors") or {}
            params = {
                **record,
                "activity_balance": contributors.get("activity_balance"),
                "body_temperature": contributors.get("body_temperature"),
                "hrv_balance": contributors.get("hrv_balance"),
                "previous_day_activity": contributors.get("previous_day_activity"),
                "previous_night": contributors.get("previous_night"),
                "recovery_index": contributors.get("recovery_index"),
                "resting_heart_rate": contributors.get("resting_heart_rate"),
                "sleep_balance": contributors.get("sleep_balance"),
                "sleep_regularity": contributors.get("sleep_regularity"),
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d daily readiness records", len(records))
    return len(records)


def upsert_daily_stress(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert daily stress records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_daily_stress (id, day, stress_high, recovery_high, day_summary)
        VALUES (%(id)s, %(day)s, %(stress_high)s, %(recovery_high)s, %(day_summary)s)
        ON CONFLICT (id) DO UPDATE SET
            stress_high = EXCLUDED.stress_high,
            recovery_high = EXCLUDED.recovery_high,
            day_summary = EXCLUDED.day_summary
    """

    with conn.cursor() as cur:
        for record in records:
            cur.execute(sql, record)

    conn.commit()
    logger.info("Upserted %d daily stress records", len(records))
    return len(records)


def upsert_daily_spo2(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert daily SpO2 records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_daily_spo2 (id, day, spo2_percentage, breathing_disturbance_index)
        VALUES (%(id)s, %(day)s, %(spo2_percentage)s, %(breathing_disturbance_index)s)
        ON CONFLICT (id) DO UPDATE SET
            spo2_percentage = EXCLUDED.spo2_percentage,
            breathing_disturbance_index = EXCLUDED.breathing_disturbance_index
    """

    with conn.cursor() as cur:
        for record in records:
            params = {
                **record,
                "spo2_percentage": Json(record.get("spo2_percentage")) if record.get("spo2_percentage") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d daily SpO2 records", len(records))
    return len(records)


def upsert_sleep_data(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert sleep data (detailed sleep periods) records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_sleep_data (
            id, day, bedtime_start, bedtime_end, average_breath, average_heart_rate,
            average_hrv, awake_time, deep_sleep_duration, efficiency, heart_rate, hrv,
            latency, light_sleep_duration, low_battery_alert, lowest_heart_rate,
            movement_30_sec, period, readiness, readiness_score_delta, rem_sleep_duration,
            restless_periods, sleep_phase_5_min, sleep_score_delta, sleep_algorithm_version,
            time_in_bed, total_sleep_duration, type, ring_id, sleep_analysis_reason
        )
        VALUES (
            %(id)s, %(day)s, %(bedtime_start)s, %(bedtime_end)s, %(average_breath)s,
            %(average_heart_rate)s, %(average_hrv)s, %(awake_time)s, %(deep_sleep_duration)s,
            %(efficiency)s, %(heart_rate)s, %(hrv)s, %(latency)s, %(light_sleep_duration)s,
            %(low_battery_alert)s, %(lowest_heart_rate)s, %(movement_30_sec)s, %(period)s,
            %(readiness)s, %(readiness_score_delta)s, %(rem_sleep_duration)s,
            %(restless_periods)s, %(sleep_phase_5_min)s, %(sleep_score_delta)s,
            %(sleep_algorithm_version)s, %(time_in_bed)s, %(total_sleep_duration)s,
            %(type)s, %(ring_id)s, %(sleep_analysis_reason)s
        )
        ON CONFLICT (id) DO UPDATE SET
            average_breath = EXCLUDED.average_breath,
            average_heart_rate = EXCLUDED.average_heart_rate,
            average_hrv = EXCLUDED.average_hrv,
            efficiency = EXCLUDED.efficiency,
            heart_rate = EXCLUDED.heart_rate,
            hrv = EXCLUDED.hrv,
            sleep_phase_5_min = EXCLUDED.sleep_phase_5_min
    """

    with conn.cursor() as cur:
        for record in records:
            params = {
                **record,
                "heart_rate": Json(record.get("heart_rate")) if record.get("heart_rate") else None,
                "hrv": Json(record.get("hrv")) if record.get("hrv") else None,
                "readiness": Json(record.get("readiness")) if record.get("readiness") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d sleep data records", len(records))
    return len(records)


def upsert_sleep_time(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert sleep time (optimal bedtime) records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_sleep_time (id, day, optimal_bedtime, recommendation, status)
        VALUES (%(id)s, %(day)s, %(optimal_bedtime)s, %(recommendation)s, %(status)s)
        ON CONFLICT (id) DO UPDATE SET
            optimal_bedtime = EXCLUDED.optimal_bedtime,
            recommendation = EXCLUDED.recommendation,
            status = EXCLUDED.status
    """

    with conn.cursor() as cur:
        for record in records:
            params = {
                **record,
                "optimal_bedtime": Json(record.get("optimal_bedtime")) if record.get("optimal_bedtime") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d sleep time records", len(records))
    return len(records)


def upsert_heart_rate(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert heart rate records (5-minute intervals)."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_heart_rate (timestamp, bpm, source)
        VALUES (%(timestamp)s, %(bpm)s, %(source)s)
        ON CONFLICT (timestamp) DO UPDATE SET
            bpm = EXCLUDED.bpm,
            source = EXCLUDED.source
    """

    with conn.cursor() as cur:
        for record in records:
            cur.execute(sql, record)

    conn.commit()
    logger.info("Upserted %d heart rate records", len(records))
    return len(records)


def upsert_workout(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert workout records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_workout (
            id, day, activity, calories, distance, start_datetime,
            end_datetime, intensity, label, source
        )
        VALUES (
            %(id)s, %(day)s, %(activity)s, %(calories)s, %(distance)s,
            %(start_datetime)s, %(end_datetime)s, %(intensity)s, %(label)s, %(source)s
        )
        ON CONFLICT (id) DO UPDATE SET
            activity = EXCLUDED.activity,
            calories = EXCLUDED.calories,
            distance = EXCLUDED.distance,
            intensity = EXCLUDED.intensity,
            label = EXCLUDED.label
    """

    with conn.cursor() as cur:
        for record in records:
            cur.execute(sql, record)

    conn.commit()
    logger.info("Upserted %d workout records", len(records))
    return len(records)


def upsert_session(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert session records (meditation, breathing, naps)."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_session (
            id, day, start_datetime, end_datetime, type, mood,
            heart_rate, hrv, motion_count
        )
        VALUES (
            %(id)s, %(day)s, %(start_datetime)s, %(end_datetime)s, %(type)s,
            %(mood)s, %(heart_rate)s, %(hrv)s, %(motion_count)s
        )
        ON CONFLICT (id) DO UPDATE SET
            type = EXCLUDED.type,
            mood = EXCLUDED.mood,
            heart_rate = EXCLUDED.heart_rate,
            hrv = EXCLUDED.hrv,
            motion_count = EXCLUDED.motion_count
    """

    with conn.cursor() as cur:
        for record in records:
            params = {
                **record,
                "heart_rate": Json(record.get("heart_rate")) if record.get("heart_rate") else None,
                "hrv": Json(record.get("hrv")) if record.get("hrv") else None,
                "motion_count": Json(record.get("motion_count")) if record.get("motion_count") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d session records", len(records))
    return len(records)


def upsert_enhanced_tag(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert enhanced tag records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_enhanced_tag (
            id, day, tag_type_code, start_time, end_time,
            start_day, end_day, comment
        )
        VALUES (
            %(id)s, %(day)s, %(tag_type_code)s, %(start_time)s, %(end_time)s,
            %(start_day)s, %(end_day)s, %(comment)s
        )
        ON CONFLICT (id) DO UPDATE SET
            tag_type_code = EXCLUDED.tag_type_code,
            comment = EXCLUDED.comment
    """

    with conn.cursor() as cur:
        for record in records:
            cur.execute(sql, record)

    conn.commit()
    logger.info("Upserted %d enhanced tag records", len(records))
    return len(records)


def upsert_rest_mode_period(
    conn: psycopg.Connection[tuple[object, ...]], records: list[dict[str, Any]]
) -> int:
    """Upsert rest mode period records."""
    if not records:
        return 0

    sql = """
        INSERT INTO oura_rest_mode_period (
            id, start_day, end_day, start_time, end_time, episodes
        )
        VALUES (
            %(id)s, %(start_day)s, %(end_day)s, %(start_time)s, %(end_time)s, %(episodes)s
        )
        ON CONFLICT (id) DO UPDATE SET
            end_day = EXCLUDED.end_day,
            end_time = EXCLUDED.end_time,
            episodes = EXCLUDED.episodes
    """

    with conn.cursor() as cur:
        for record in records:
            params = {
                **record,
                "episodes": Json(record.get("episodes")) if record.get("episodes") else None,
            }
            cur.execute(sql, params)

    conn.commit()
    logger.info("Upserted %d rest mode period records", len(records))
    return len(records)
