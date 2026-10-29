#!/usr/bin/env python3
"""Simple MQTT simulator publishing industrial sensor data."""
import json
import logging
import math
import os
import random
import signal
import sys
import time

import paho.mqtt.client as mqtt

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("mqtt-sim")

# name: (unit, base, noise fraction, min, max, sine period seconds)
METRICS = {
    "temperature": ("C", 65.0, 0.05, -20.0, 150.0, 60.0),
    "pressure": ("kPa", 450.0, 0.03, 0.0, 1000.0, 45.0),
    "flow_rate": ("m3/h", 120.0, 0.08, 0.0, 400.0, 90.0),
    "vibration": ("mm/s", 4.5, 0.15, 0.0, 30.0, 20.0),
    "motor_speed": ("rpm", 1450.0, 0.02, 0.0, 3000.0, 120.0),
    "motor_current": ("A", 12.0, 0.06, 0.0, 50.0, 75.0),
    "tank_level": ("%", 60.0, 0.10, 0.0, 100.0, 300.0),
    "humidity": ("%", 45.0, 0.05, 0.0, 100.0, 180.0),
}


def env_bool(name, default):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes")


def main():
    host = os.environ.get("MQTT_BROKER_HOST")
    username = os.environ.get("MQTT_USERNAME")
    password = os.environ.get("MQTT_PASSWORD")
    if not host:
        sys.exit("MQTT_BROKER_HOST is required")

    port = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
    device_id = os.environ.get("DEVICE_ID", "sim-001")
    topic = os.environ.get("MQTT_TOPIC", f"factory/{device_id}/telemetry")
    interval = float(os.environ.get("PUBLISH_INTERVAL_S", "1"))
    qos = int(os.environ.get("MQTT_QOS", "0"))
    metrics = [m.strip() for m in os.environ.get("METRICS", ",".join(METRICS)).split(",") if m.strip()]
    unknown = [m for m in metrics if m not in METRICS]
    if unknown:
        sys.exit(f"Unknown metrics: {unknown}. Available: {list(METRICS)}")

    client = mqtt.Client(client_id=f"{device_id}-{random.randint(0, 9999):04d}")
    if username:
        client.username_pw_set(username, password)
    if env_bool("MQTT_TLS", False):
        client.tls_set()
    status_topic = f"factory/{device_id}/status"
    client.will_set(status_topic, "offline", qos=1, retain=True)

    def on_connect(c, _u, _f, rc):
        if rc == 0:
            log.info("Connected to %s:%s", host, port)
            c.publish(status_topic, "online", qos=1, retain=True)
        else:
            log.error("Connect failed rc=%s", rc)

    client.on_connect = on_connect
    client.on_disconnect = lambda c, u, rc: log.warning("Disconnected rc=%s", rc)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect_async(host, port, keepalive=60)
    client.loop_start()

    log.info("Publishing %s to %s every %ss", metrics, topic, interval)
    try:
        while running:
            t = time.time()
            payload = {"ts": int(t * 1000), "device_id": device_id, "units": {}}
            for name in metrics:
                unit, base, noise, lo, hi, period = METRICS[name]
                swing = base * noise
                value = base + math.sin(2 * math.pi * t / period) * swing + random.uniform(-swing, swing)
                payload[name] = round(min(hi, max(lo, value)), 3)
                payload["units"][name] = unit
            client.publish(topic, json.dumps(payload, separators=(",", ":")), qos=qos)
            time.sleep(interval)
    finally:
        client.publish(status_topic, "offline", qos=1, retain=True).wait_for_publish(timeout=2)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
