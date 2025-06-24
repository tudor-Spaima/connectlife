# Python library for ConnectLife API 

Used by devices from Hisense, Gorenje, ASKO & ATAG and ETNA Connect.

The goal of this library is to support a native [Home Assistant](https://www.home-assistant.io/) integration for devices
that uses the ConnectLife API.

The code is based on [Connectlife API proxy / MQTT Home Assistant integration](https://github.com/bilan/connectlife-api-connector)
([MIT license](https://github.com/bilan/connectlife-api-connector/blob/51c6b8e4562205e1c343d0cba19354f411bd5e77/composer.json#L2-L6)).

Software is provided as is - use at your own risk. There is probably no way to harm your physical devices, but
there is no guarantee that you don't experience other problems, for instance locking your ConnectLife account. 

Licensed under [GPLv3](LICENSE).

To test out the library:
```bash
pip install connectlife
python -m connectlife.dump --username <username> --password <password>
```

This will log in to the ConnectLife API using the provided username and password, and print the list of all fields
for all appliances that is registered with the account.

The Home Assistant integration is currently in discovery phase. Please contribute your device dumps to help
the development.

# Development environment

## Prerequisites:

- [pyenv](https://github.com/pyenv/pyenv)

## Install environment

```bash
pyenv install
python -m venv venv
source venv/bin/activate
pip install .
```

## Test server

Test server that mocks the ConnectLife API. Runs on `http://localhost:8080`.

The server reads all JSON files in the current directory, and serves them as appliances. Properties can be updated,
but is not persisted. The only validation is that the `puid` and `property` exists, it assumes that all properties
are writable and that any value is legal.

```bash
cd dumps
python -m test_server
```

To use the test server, provide the URL to the test server:  
```python
from connectlife.api import ConnectLifeApi
api = ConnectLifeApi(username="user@example.com", password="password", test_server="http://localhost:8080")
```

Control Commands

| Key                   | Description                | Value Type    | Notes                           |
| --------------------- | -------------------------- | ------------- | ------------------------------- |
| `t_power`           | Power ON/OFF               | `"0"/"1"`   | `1 = on`, `0 = off`        |
| `t_temp`            | Target temperature (°C)   | `"16"-"30"` | Usually 16–30                  |
| `t_work_mode`       | Operating mode             | `"1"-"5"`   | See `Work Mode Values` below  |
| `t_fan_speed`       | Fan speed                  | `"1"-"7"`   | May vary by model               |
| `t_up_down`         | Swing vertical             | `"0"/"1"`   | `1 = on`, `0 = off`         |
| `t_swing_direction` | Swing horizontal           | `"0"/"1"`   | `1 = on`, `0 = off`         |
| `t_sleep`           | Sleep mode                 | `"0"/"1"`   | `1 = enabled`                 |
| `t_eco`             | Eco mode                   | `"0"/"1"`   |                                 |
| `t_super`           | Turbo mode                 | `"0"/"1"`   |                                 |
| `t_swing_angle`     | Swing angle control        | `"0"/"1"`   | Interpretation may vary         |
| `t_temp_type`       | Temperature unit (°C/°F) | `"0"/"1"`   | Likely `0 = °C`, `1 = °F` |

Work Mode Values for `t_work_mode`

| Value | Mode     |
| ----- | -------- |
| `1` | Auto     |
| `2` | Cool     |
| `3` | Dry      |
| `4` | Fan-only |
| `5` | Heat     |

Feedback / Status-Only Fields

| Key                  | Description                    | Type   | Notes                                  |
| -------------------- | ------------------------------ | ------ | -------------------------------------- |
| `f_temp_in`        | Indoor temperature             | Number | Read-only                              |
| `f_electricity`    | Power consumption (W)          | Number | Read-only                              |
| `daily_energy_kwh` | Daily energy usage (kWh)       | Number | Read-only                              |
| `f_votage`         | Voltage                        | Number | Read-only (likely typo of “voltage”) |
| `f_humidity`       | Humidity (%)                   | Number |                                        |
| `f_e_*`            | Internal error/state/flag bits | String | Diagnostic only                        |
