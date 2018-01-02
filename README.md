See http://blog.mosibi.nl/?p=736 for more info about this script.

## Home Assistant configuration

```
input_number:
  set_wtw_ventilation_level:
    name: Set ventilation level
    initial: 2
    min: 0
    max: 3
    step: 1
    mode: box

automation:
  - alias: Ventilation level slider moved in GUI
    trigger:
      platform: state
      entity_id: input_number.set_wtw_ventilation_level
    action:
      service: mqtt.publish
      data_template:
        topic: house/2/attic/wtw/set_ventilation_level
        retain: false
        payload: "{{ states('input_number.set_wtw_ventilation_level') | int }}"

customize:
  sensor.wtw_intake_fan_speed:
    icon: mdi:fan
  sensor.wtw_exhaust_fan_speed:
    icon: mdi:fan

sensor:
  - platform: mqtt
    state_topic: "house/2/attic/wtw/outside_air_temp"
    name: "WTW Outside Temperature"
    qos: 0
    unit_of_measurement: '°C'
  - platform: mqtt
    state_topic: "house/2/attic/wtw/supply_air_temp"
    name: "WTW Supply Temperature"
    qos: 0
    unit_of_measurement: '°C'
  - platform: mqtt
    state_topic: "house/2/attic/wtw/return_air_temp"
    name: "WTW Return Temperature"
    qos: 0
    unit_of_measurement: '°C'
  - platform: mqtt
    state_topic: "house/2/attic/wtw/exhaust_air_temp"
    name: "WTW Exhaust Temperature"
    qos: 0
    unit_of_measurement: '°C'
  - platform: mqtt
    state_topic: "house/2/attic/wtw/ventilation_level"
    name: "WTW Ventilation Level"
    qos: 0
  - platform: mqtt
    state_topic: "house/2/attic/wtw/filter_status"
    name: "WTW Filter Status"
    qos: 0
  - platform: mqtt
    state_topic: "house/2/attic/wtw/intake_fan_speed"
    name: "WTW Intake Fan Speed"
    qos: 0
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: "house/2/attic/wtw/exhaust_fan_speed"
    name: "WTW Exhaust Fan Speed"
    qos: 0
    unit_of_measurement: '%'
```

![Image](http://blog.mosibi.nl/wp-content/uploads/2018/01/whr930_homeassistant_2.png)

