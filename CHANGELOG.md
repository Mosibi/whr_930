# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2024-03-30

### Fixed

- Bypass open hours in function `get_operating_hours` used the wrong entries from the dataset.

## [1.1.0] - 2023-08-06

### Added

- Add function get_delay_timers.
- Extend wtw.yaml with delay timer MQTT topics.

### Fixed

- Function get_fan_status had the wrong command in the documentation part.
- Reformatted the code using Black.

## [1.0.1] - 2023-08-05

### Added

- Add CHANGELOG.md.
- Start releasing this project.

### Fixed

- MQTT entity naming according new requirement from Home Assistant (#28).

## [1.0.0]


### Added

- Small interface change. When WTW is set to off, the level is changed to 0, which by default is a speed of 15%.
- Save energy. Lower the ventilation speed when nobody is home.
- Support Docker and configuration from file (#23).
- Use a pull down menu to set the ventilation instead of using a slider.
- Use debug_msg instead of print in function debug_data.
- Incoming command queue (#13).
- Validate incoming checksum (#14).
- Update values for temperature and fan levels after update.
- Check for incoming commands between each remote call.
- Add incoming mqtt messages to queue to be handled in main loop.
- Add information about voice integration.
- Add exception handling for the sitation where incomple data is received.
- Function set_comfort_temperature: limit the temperature range to the specification from Stork.
- Set measurement units.
- New screenshot.
- Add the P# states in a folded menu.
- Add P# state sensors.
- Show all P# states.
- Lovelace plugin lovelace-fold-entity-row added.
- Always call debug_data and only show the debug data when debug_level is 1 or higher.
- New home-assistant layout.
- Set sleep timer to 5 seconds, since all the steps are taking longer then I like.
- Publish return and supply air level.
- Document how a packet is build up and do not expose the pre heating valve status from get_valve_status since it is also exposed by get_preheating_status.
- Add frost protection information.
- Using booleans for 'yes', 'no', 'present', 'not present', 'active', 'not active'.
- Add function get_preheating_status.
- Add function get_status.
- removed debug code.
- Add function create_packet: create a serial_command packet based on input.
- Add function calculate_checksum: used by funcion create_packet, calculates the checksum for the serial data command.
- Every `get_` and `_set` function uses create_packet.
- Function set_comfort_temperature added. Sent a message on MQTT topic house/2/attic/wtw/set_comfort_temperature with a temperature in celsius to the Comfort Temperature.
- Function get_temp now also shows the current comfort temperature.
- Code formatting done using Black.
- Publish data in from functions get_valve_status and get_bypass_control.
- Add extra funtions to get data from the WHR930.
- Make the stdout unbufferd.
- Function set_ventilation_level: check if an ACK is received from the WHR930 and return an 'INFO' message if we did, else return a WARNING message.
- Add installation and configuration info.
- Add Makefile and systemd service file.
- Move whr930 to src dir and did a rewrite from python2 to python3.
- Convert the input to an integer and use integers in the set_ventilation_level function.
- Add IntakeFanActive (this is the house 'button' on the unit self) and moved the function debug_data up in the code (style).
- Add more home-assistant integration examples and added a new screenshot.
- Add function get_fan_status: get fan speed in RPM and percent.
- Add function debug_data: Use this function to debug the returned data from a serial command.
- Add function get_filter_status: get the filter status (Ok/Full).
- Cleaned up some code.

### Fixed

- Re-add logic to set the comfort temperature. This logic was accidentally removed in the previous change.
- Adopt configuration to MQTT changes in Home Assistant.
- Fix debug data function for out of index if debug >1 (#22).
- Change MQTT fan setup to be compatible with latest HomeAssistant (#20).
- Formatted using Black.
- Testing revealed that automation to update the slider (input_number) value could trigger a loop, there I disable it until a fix is available.
- Do not try to debug an empty serial packet, detect an Ack and code reformating using Black.
- Function get_status ValueError and KeyError exception handling added, (#9).
- Warning messages are not shown anymore by default. Add exception handlers (#8).
- Warning text in get_fan_status is now in line with the other same type warning messages (#6).
- Function get_status type fix (#7).
- Fix loop with slider updating automation.
- Fix get_filter_status, the filter status is in data byte 9 (array nr: 15) instead of data byte 12 (array nr: 18) (#4).
- Add slider to set the comfort temperature and moved the ventilition slider together with the temp slider in it's own card (#5).
- Add input_number to set the WTW comfort temperature and Add 2 automations to set the sliders to the current value (#5).
- Rename summermode -> summer_mode.
- Fix image url.
- Fix indenting in functions get_valve_status and get_bypass_control.
- Bug fix/added serial data validation.
- Python style fix.
- Fix issues reported by Dick-W.
- Function set_ventilation_level: Fetch the None if we do not get data back from the serial command.
- Function set_ventilation_level: fix for the WARNING message.
- Function get_fan_status: Checksum comment was wrong.
- Function get_fan_status: Act only when data is received.
- Function debug_data: Also print the number in the data array for data packets.
- Move screenshot above the HA examples.
- Rename function get_fan_status to get_ventilation_status.
