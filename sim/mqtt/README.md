# MQTT industrial data simulator

Publishes simulated industrial telemetry (temperature, pressure, flow, vibration, motor, tank level, humidity) as JSON.

## Run

```bash
docker build -t mqtt-sim sim/mqtt
docker run --rm \
  -e MQTT_BROKER_HOST=broker.example.com \
  -e MQTT_USERNAME=user -e MQTT_PASSWORD=pass \
  mqtt-sim
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER_HOST` | required | Broker host |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | – | Broker credentials |
| `MQTT_BROKER_PORT` | `1883` | Broker port |
| `MQTT_TLS` | `false` | Enable TLS |
| `DEVICE_ID` | `sim-001` | Device identifier |
| `MQTT_TOPIC` | `factory/<DEVICE_ID>/telemetry` | Telemetry topic |
| `METRICS` | all | Comma-separated subset of metrics |
| `PUBLISH_INTERVAL_S` | `1` | Publish interval (s) |
| `MQTT_QOS` | `0` | QoS |

Status (`online`/`offline`, retained, with LWT) is published to `factory/<DEVICE_ID>/status`.

Payload: `{"ts":<epoch_ms>,"device_id":"sim-001","units":{...},"temperature":65.2,...}`
