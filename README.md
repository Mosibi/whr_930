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
```
