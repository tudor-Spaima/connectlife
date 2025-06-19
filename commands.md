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
