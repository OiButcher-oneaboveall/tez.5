
import numpy as np
from data_config import cities, distance_matrix, hourly_speed_matrix, hourly_risk_matrix, fuel_consumption_matrix, co2_emission_factor, service_times, time_windows, START_HOUR

def get_speed(i, j, hour):
    idx = hour - START_HOUR
    return hourly_speed_matrix[i][j][idx] if 0 <= idx < 12 else 90

def get_risk(i, j, hour):
    idx = hour - START_HOUR
    return hourly_risk_matrix[i][j][idx] if 0 <= idx < 12 else 0.5

def get_fuel(i, j, hour):
    idx = hour - START_HOUR
    return fuel_consumption_matrix[i][j][idx] if 0 <= idx < 12 else 0.35

def compute_leg(i, j, hour, minute):
    distance = distance_matrix[i][j]
    speed = get_speed(i, j, hour)
    travel_min = (distance / speed) * 60
    fuel = distance * get_fuel(i, j, hour)
    risk = get_risk(i, j, hour)
    co2 = fuel * co2_emission_factor
    return travel_min, fuel, co2, risk

def route_metrics(route):
    time, fuel, co2, risk = 0, 0, 0, 0
    hour, minute = START_HOUR, 0
    log = []

    for i in range(len(route) - 1):
        a, b = route[i], route[i+1]
        leg_min, leg_fuel, leg_co2, leg_risk = compute_leg(a, b, hour, minute)
        time += leg_min
        fuel += leg_fuel
        co2 += leg_co2
        risk += leg_risk

        minute += int(leg_min)
        hour += minute // 60
        minute %= 60

        if b != 0:
            early, late = time_windows[b]
            arr_min = hour * 60 + minute
            if arr_min < early * 60:
                wait = early * 60 - arr_min
                time += wait
                minute += wait
                hour += minute // 60
                minute %= 60
            elif arr_min > late * 60:
                return float('inf'), float('inf'), float('inf'), float('inf'), []

            service = service_times.get(b, 0)
            time += service
            minute += service
            hour += minute // 60
            minute %= 60

        log.append({
            "from": cities[a], "to": cities[b],
            "travel_min": round(leg_min, 1),
            "fuel": round(leg_fuel, 2),
            "co2": round(leg_co2, 2),
            "risk": round(leg_risk, 2),
            "service": service_times.get(b, 0),
            "wait": max(0, early * 60 - (hour * 60 + minute - service_times.get(b, 0)))
        })

    return time, fuel, co2, risk, log
