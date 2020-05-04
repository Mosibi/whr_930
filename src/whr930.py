#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface with a StorkAir WHR930

Publish every 10 seconds the status on a MQTT topic
Listen on MQTT topic for commands to set the ventilation level
"""

import paho.mqtt.client as mqtt
import time
import sys
import serial


def debug_msg(message):
    if debug is True:
        print(
            "{0} DEBUG: {1}".format(
                time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
            )
        )


def warning_msg(message):
    print(
        "{0} WARNING: {1}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
        )
    )


def info_msg(message):
    print(
        "{0} INFO: {1}".format(
            time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message
        )
    )


def debug_data(serial_data):
    if debug_level > 0:
        data_len = len(serial_data)
        print("Data length   : {0}".format(len(serial_data)))
        print("Ack           : {0} {1}".format(serial_data[0], serial_data[1]))
        print("Start         : {0} {1}".format(serial_data[2], serial_data[3]))
        print("Command       : {0} {1}".format(serial_data[4], serial_data[5]))
        print(
            "Nr data bytes : {0} (integer {1})".format(
                serial_data[6], int(serial_data[6], 16)
            )
        )

        n = 1
        while n <= int(serial_data[6], 16):
            print(
                "Data byte {0}   : Hex: {1}, Int: {2}, Array #: {3}".format(
                    n, serial_data[n + 6], int(serial_data[n + 6], 16), n + 6
                )
            )
            n += 1

        print("Checksum      : {0}".format(serial_data[-2]))
        print("End           : {0} {1}".format(serial_data[-2], serial_data[-1]))

    if debug_level > 1:
        n = 0
        while n < data_len:
            print("serial_data {0}   : {1}".format(n, serial_data[n]))
            n += 1


def on_message(client, userdata, message):
    debug_msg(
        "message received: topic: {0}, payload: {1}, userdata: {2}".format(
            message.topic, message.payload, userdata
        )
    )

    if message.topic == "house/2/attic/wtw/set_ventilation_level":
        fan_level = int(float(message.payload))
        set_ventilation_level(fan_level)
    elif message.topic == "house/2/attic/wtw/set_comfort_temperature":
        temperature = float(message.payload)
        set_comfort_temperature(temperature)
    else:
        warning_msg(
            "Received a message on topic {} where we do not have a handler for at the moment".format(
                message.topic
            )
        )


def publish_message(msg, mqtt_path):
    mqttc.publish(mqtt_path, payload=msg, qos=0, retain=True)
    time.sleep(0.1)
    debug_msg(
        "published message {0} on topic {1} at {2}".format(
            msg, mqtt_path, time.asctime(time.localtime(time.time()))
        )
    )


def create_packet(command, data=[]):
    """
    Create a packet.
    Data length and checksum are automatically calculated and added to the packet.
    Start and end bits are added as well.
    """
    packet = []
    packet.append(0x07)  # default start bit
    packet.append(0xF0)  # default start bit

    for b in command:
        packet.append(b)

    packet.append(len(data))
    for b in data:
        packet.append(b)

    packet.append(calculate_checksum(packet[2:]))
    packet.append(0x07)  # default end bit
    packet.append(0x0F)  # default end bit

    return bytes(packet)


def calculate_checksum(data):
    """
    The checksum is obtained by adding all bytes (excluding start and end) plus 173.
    If the value 0x07 appears twice in the data area, only one 0x07 is used for the checksum calculation.
    If the checksum is larger than one byte, the least significant byte is used.
    """
    checksum = 173
    found_07 = False

    for b in data:
        if (b == 0x07 and found_07 == False) or b != 0x07:
            checksum += b

        if b == 0x07:
            found_07 = True

    if checksum > 0xFF:
        checksum -= 0xFF + 1

    return checksum


def validate_data(data):
    if len(data) <= 1:
        """always expect a valid ACK at least"""
        return None

    if len(data) == 2 and data[0] == "07" and data[1] == "f3":
        """
        This is a regular ACK which is received on all "setting" commands,
        such as setting ventilation level, command 0x99)
        """
        return data
    else:
        if len(data) >= 10:
            """
            A valid response should be at least 10 bytes (ACK + response with data length = 0)

            Byte 6 in the array contains the length of the dataset. This length + 10 is the total
            size of the message
            """
            dataset_len = int(data[6], 16)
            message_len = dataset_len + 10
            debug_msg("Message length is {}".format(message_len))

            """ 
            Sometimes more data is captured on the serial port then we expect. We drop those extra
            bytes to get a clean data to work on
            """
            stripped_data = data[0:message_len]
            debug_msg("Stripped message length is {}".format(len(stripped_data)))

            if (
                stripped_data[0] != "07"
                or stripped_data[1] != "f3"
                or stripped_data[2] != "07"
                or stripped_data[3] != "f0"
                or stripped_data[-2] != "07"
                or stripped_data[-1] != "0f"
            ):
                warning_msg("Received garbage data, ignored ...")
                debug_data(stripped_data)
                return None
            else:
                debug_msg("Serial data validation passed")
                """
                Since we are here, we have a clean data set. Now we need to remove
                a double 0x07 in the dataset if present. This must be done because
                according the protocol specification, when a 0x07 value appears in
                the dataset, another 0x07 is inserted, but not added to the length
                or the checksum
                """
                for i in range(7, 6 + dataset_len):
                    if stripped_data[i] == "07" and stripped_data[i + 1] == "07":
                        del stripped_data[i + 1]

                return stripped_data
        else:
            warning_msg(
                "The length of the data we recieved from the serial port is {}, it should be minimal 10 bytes".format(
                    len(data)
                )
            )
            return None


def serial_command(cmd):
    data = []
    ser.write(cmd)
    time.sleep(2)

    while ser.inWaiting() > 0:
        data.append(ser.read(1).hex())

    time.sleep(2)

    return validate_data(data)


def set_ventilation_level(fan_level):
    """
    Command: 0x00 0x99
    """
    if fan_level < 0 or fan_level > 3:
        warning_msg(
            "Ventilation level can be set to 0, 1, 2 and 4, but not {0}".format(
                fan_level
            )
        )
        return None

    packet = create_packet([0x00, 0x99], [fan_level + 1])
    data = serial_command(packet)

    if data:
        if data[0] == "07" and data[1] == "f3":
            info_msg("Changed the ventilation to {0}".format(fan_level))
        else:
            warning_msg(
                "Changing the ventilation to {0} went wrong, did not receive an ACK after the set command".format(
                    fan_level
                )
            )
    else:
        warning_msg(
            "Changing the ventilation to {0} went wrong, did not receive an ACK after the set command".format(
                fan_level
            )
        )


def set_comfort_temperature(temp):
    """
    Command: 0x00 0xD3
    """
    calculated_temp = int(temp + 20) * 2

    packet = create_packet([0x00, 0xD3], [calculated_temp])
    data = serial_command(packet)

    if data:
        if data[0] == "07" and data[1] == "f3":
            info_msg("Changed comfort temperature to {0}".format(temp))
        else:
            warning_msg(
                "Changing the comfort temperature to {0} went wrong, did not receive an ACK after the set command".format(
                    temp
                )
            )
    else:
        warning_msg(
            "Changing the comfort temperature to {0} went wrong, did not receive an ACK after the set command".format(
                temp
            )
        )


def get_temp():
    """
    Command: 0x00 0xD1
    """
    packet = create_packet([0x00, 0xD1])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_temp function could not get serial data")
    else:
        """
        The default comfort temperature of the WHR930 is 20c

        Zehnder advises to let it on 20c, but if you want you change it, to
        set it to 21c in the winter and 15c in the summer.
        """
        ComfortTemp = int(data[7], 16) / 2.0 - 20
        OutsideAirTemp = int(data[8], 16) / 2.0 - 20
        SupplyAirTemp = int(data[9], 16) / 2.0 - 20
        ReturnAirTemp = int(data[10], 16) / 2.0 - 20
        ExhaustAirTemp = int(data[11], 16) / 2.0 - 20

        publish_message(msg=ComfortTemp, mqtt_path="house/2/attic/wtw/comfort_temp")
        publish_message(
            msg=OutsideAirTemp, mqtt_path="house/2/attic/wtw/outside_air_temp"
        )
        publish_message(
            msg=SupplyAirTemp, mqtt_path="house/2/attic/wtw/supply_air_temp"
        )
        publish_message(
            msg=ReturnAirTemp, mqtt_path="house/2/attic/wtw/return_air_temp"
        )
        publish_message(
            msg=ExhaustAirTemp, mqtt_path="house/2/attic/wtw/exhaust_air_temp"
        )

        debug_msg(
            "ComfortTemp: {0}, OutsideAirTemp: {1}, SupplyAirTemp: {2}, ReturnAirTemp: {3}, ExhaustAirTemp: {4}".format(
                ComfortTemp,
                OutsideAirTemp,
                SupplyAirTemp,
                ReturnAirTemp,
                ExhaustAirTemp,
            )
        )


def get_ventilation_status():
    """
    Command: 0x00 0xCD
    """
    status_data = {"IntakeFanActive": {0: False, 1: True}}

    packet = create_packet([0x00, 0xCD])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_ventilation_status function could not get serial data")
    else:
        ReturnAirLevel = int(data[13], 16)
        SupplyAirLevel = int(data[14], 16)
        FanLevel = int(data[15], 16) - 1
        IntakeFanActive = status_data["IntakeFanActive"][int(data[16], 16)]

        publish_message(msg=FanLevel, mqtt_path="house/2/attic/wtw/ventilation_level")
        publish_message(
            msg=IntakeFanActive, mqtt_path="house/2/attic/wtw/intake_fan_active"
        )
        debug_msg(
            "ReturnAirLevel: {}, SupplyAirLevel: {}, FanLevel: {}, IntakeFanActive: {}".format(
                ReturnAirLevel, SupplyAirLevel, FanLevel, IntakeFanActive
            )
        )


def get_fan_status():
    """
    Command: 0x00 0x99
    """
    packet = create_packet([0x00, 0x0B])
    data = serial_command(packet)

    if data is None:
        warning_msg("function get_fan_status could not get serial data")
    else:
        IntakeFanSpeed = int(data[7], 16)
        ExhaustFanSpeed = int(data[8], 16)
        IntakeFanRPM = int(1875000 / (int(data[9], 16) * 256 + int(data[10], 16)))
        ExhaustFanRPM = int(1875000 / (int(data[11], 16) * 256 + int(data[12], 16)))

        publish_message(
            msg=IntakeFanSpeed, mqtt_path="house/2/attic/wtw/intake_fan_speed"
        )
        publish_message(
            msg=ExhaustFanSpeed, mqtt_path="house/2/attic/wtw/exhaust_fan_speed"
        )
        publish_message(
            msg=IntakeFanRPM, mqtt_path="house/2/attic/wtw/intake_fan_speed_rpm"
        )
        publish_message(
            msg=ExhaustFanRPM, mqtt_path="house/2/attic/wtw/exhaust_fan_speed_rpm"
        )

        debug_msg(
            "IntakeFanSpeed {0}%, ExhaustFanSpeed {1}%, IntakeAirRPM {2}, ExhaustAirRPM {3}".format(
                IntakeFanSpeed, ExhaustFanSpeed, IntakeFanRPM, ExhaustFanRPM
            )
        )


def get_filter_status():
    """
    Command: 0x00 0xD9
    """
    packet = create_packet([0x00, 0xD9])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_filter_status function could not get serial data")
    else:
        if int(data[18], 16) == 0:
            FilterStatus = "Ok"
        elif int(data[18], 16) == 1:
            FilterStatus = "Full"
        else:
            FilterStatus = "Unknown"

        publish_message(msg=FilterStatus, mqtt_path="house/2/attic/wtw/filter_status")
        debug_msg("FilterStatus: {0}".format(FilterStatus))


def get_valve_status():
    """
    Command: 0x00 0x0D
    """
    packet = create_packet([0x00, 0x0D])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_valve_status function could not get serial data")
    else:
        ByPass = int(data[7], 16)
        PreHeating = int(data[8], 16)
        ByPassMotorCurrent = int(data[9], 16)
        PreHeatingMotorCurrent = int(data[10], 16)

        publish_message(
            msg=ByPass, mqtt_path="house/2/attic/wtw/valve_bypass_percentage"
        )
        publish_message(msg=PreHeating, mqtt_path="house/2/attic/wtw/valve_preheating")
        publish_message(
            msg=ByPassMotorCurrent, mqtt_path="house/2/attic/wtw/bypass_motor_current"
        )
        publish_message(
            msg=PreHeatingMotorCurrent,
            mqtt_path="house/2/attic/wtw/preheating_motor_current",
        )

        debug_msg(
            "ByPass: {}, PreHeating: {}, ByPassMotorCurrent: {}, PreHeatingMotorCurrent: {}".format(
                ByPass, PreHeating, ByPassMotorCurrent, PreHeatingMotorCurrent
            )
        )


def get_bypass_control():
    """
    Command: 0x00 0xDF
    """
    packet = create_packet([0x00, 0xDF])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_bypass_control function could not get serial data")
    else:
        ByPassFactor = int(data[9], 16)
        ByPassStep = int(data[10], 16)
        ByPassCorrection = int(data[11], 16)

        if int(data[13], 16) == 1:
            SummerMode = True
        else:
            SummerMode = False

        publish_message(msg=ByPassFactor, mqtt_path="house/2/attic/wtw/bypass_factor")
        publish_message(msg=ByPassStep, mqtt_path="house/2/attic/wtw/bypass_step")
        publish_message(
            msg=ByPassCorrection, mqtt_path="house/2/attic/wtw/bypass_correction"
        )
        publish_message(msg=SummerMode, mqtt_path="house/2/attic/wtw/summermode")

        debug_msg(
            "ByPassFactor: {}, ByPassStep: {}, ByPassCorrection: {}, SummerMode: {}".format(
                ByPassFactor, ByPassStep, ByPassCorrection, SummerMode
            )
        )


def get_preheating_status():
    """
    Command: 0x00 0xE1
    """
    status_data = {
        "PreHeatingValveStatus": {0: "Closed", 1: "Open", "2": "Unknown"},
        "FrostProtectionActive": {0: False, 1: True},
        "PreHeatingActive": {0: False, 1: True},
    }

    packet = create_packet([0x00, 0xE1])
    data = serial_command(packet)

    if data is None:
        warning_msg("get_preheating_status function could not get serial data")
    else:
        PreHeatingValveStatus = status_data["PreHeatingValveStatus"][int(data[7], 16)]
        FrostProtectionActive = status_data["FrostProtectionActive"][int(data[8], 16)]
        PreHeatingActive = status_data["PreHeatingActive"][int(data[9], 16)]

        publish_message(
            msg=PreHeatingValveStatus, mqtt_path="house/2/attic/wtw/preheating_valve"
        )
        publish_message(
            msg=FrostProtectionActive,
            mqtt_path="house/2/attic/wtw/frost_protection_active",
        )
        publish_message(
            msg=PreHeatingActive, mqtt_path="house/2/attic/wtw/preheating_state"
        )

        debug_msg(
            "PreHeatingValveStatus: {}, FrostProtectionActive: {}, PreHeatingActive: {}".format(
                PreHeatingValveStatus, FrostProtectionActive, PreHeatingActive
            )
        )


def get_operating_hours():
    """
    Command: 0x00 0xDD
    """
    packet = create_packet([0x00, 0xDD])
    data = serial_command(packet)

    Level0Hours = int(data[7], 16) + int(data[8], 16) + int(data[9], 16)
    Level1Hours = int(data[10], 16) + int(data[11], 16) + int(data[12], 16)
    Level2Hours = int(data[13], 16) + int(data[14], 16) + int(data[15], 16)
    Level3Hours = int(data[24], 16) + int(data[25], 16) + int(data[26], 16)
    FrostProtectionHours = int(data[16], 16) + int(data[17], 16)
    PreHeatingHours = int(data[18], 16) + int(data[19], 16)
    BypassOpenHours = int(data[14], 16) + int(data[15], 16)
    FilterHours = int(data[22], 16) + int(data[23], 16)

    publish_message(msg=Level0Hours, mqtt_path="house/2/attic/wtw/level0_hours")
    publish_message(msg=Level1Hours, mqtt_path="house/2/attic/wtw/level1_hours")
    publish_message(msg=Level2Hours, mqtt_path="house/2/attic/wtw/level2_hours")
    publish_message(msg=Level3Hours, mqtt_path="house/2/attic/wtw/level3_hours")
    publish_message(
        msg=FrostProtectionHours, mqtt_path="house/2/attic/wtw/frost_protection_hours"
    )
    publish_message(msg=PreHeatingHours, mqtt_path="house/2/attic/wtw/preheating_hours")
    publish_message(
        msg=BypassOpenHours, mqtt_path="house/2/attic/wtw/bypass_open_hours"
    )
    publish_message(msg=FilterHours, mqtt_path="house/2/attic/wtw/filter_hours")

    debug_msg(
        "Level0Hours: {}, Level1Hours: {}, Level2Hours: {}, Level3Hours: {}, FrostProtectionHours: {}, PreHeatingHours: {}, BypassOpenHours: {}, FilterHours: {}".format(
            Level0Hours,
            Level1Hours,
            Level2Hours,
            Level3Hours,
            FrostProtectionHours,
            PreHeatingHours,
            BypassOpenHours,
            FilterHours,
        )
    )


def get_status():
    """
    Command: 0x00 0xD5
    """
    status_data = {
        "PreHeatingPresent": {0: False, 1: True},
        "ByPassPresent": {0: False, 1: True},
        "Type": {0: "Right", 1: "Left"},
        "Size": {1: "Large", 2: "Small"},
        "OptionsPresent": {0: False, 1: True},
        "EnthalpyPresent": {0: False, 1: True, 2: "PresentWithoutSensor"},
        "EWTPresent": {0: False, 1: "Managed", 2: "Unmanaged"},
    }

    packet = create_packet([0x00, 0xD5])
    data = serial_command(packet)

    PreHeatingPresent = status_data["PreHeatingPresent"][int(data[7])]
    ByPassPresent = status_data["ByPassPresent"][int(data[8])]
    Type = status_data["Type"][int(data[9])]
    Size = status_data["Size"][int(data[10])]
    OptionsPresent = status_data["OptionsPresent"][int(data[11])]
    ActiveStatus1 = int(
        data[13]
    )  # (0x01 = P10 ... 0x80 = P17) Info about this?, please share it with me (richard@mosibi.nl)
    ActiveStatus2 = int(
        data[14]
    )  # (0x01 = P18 / 0x02 = P19) Info about this?, please share it with me (richard@mosibi.nl)
    ActiveStatus3 = int(
        data[15]
    )  # (0x01 = P90 ... 0x40 = P96) Info about this?, please share it with me (richard@mosibi.nl)
    EnthalpyPresent = status_data["EnthalpyPresent"][int(data[16])]
    EWTPresent = status_data["EWTPresent"][int(data[17])]

    debug_msg(
        "PreHeatingPresent: {}, ByPassPresent: {}, Type: {}, Size: {}, OptionsPresent: {}, ActiveStatus1: {}, ActiveStatus2: {}, ActiveStatus3: {}, EnthalpyPresent: {}, EWTPresent: {}".format(
            PreHeatingPresent,
            ByPassPresent,
            Type,
            Size,
            OptionsPresent,
            ActiveStatus1,
            ActiveStatus2,
            ActiveStatus3,
            EnthalpyPresent,
            EWTPresent,
        )
    )

    publish_message(
        msg=PreHeatingPresent, mqtt_path="house/2/attic/wtw/preheating_present"
    )
    publish_message(msg=ByPassPresent, mqtt_path="house/2/attic/wtw/bypass_present")
    publish_message(msg=Type, mqtt_path="house/2/attic/wtw/type")
    publish_message(msg=Size, mqtt_path="house/2/attic/wtw/size")
    publish_message(msg=OptionsPresent, mqtt_path="house/2/attic/wtw/options_present")
    publish_message(msg=ActiveStatus1, mqtt_path="house/2/attic/wtw/activestatus1")
    publish_message(msg=ActiveStatus2, mqtt_path="house/2/attic/wtw/activestatus2")
    publish_message(msg=ActiveStatus3, mqtt_path="house/2/attic/wtw/activestatus3")
    publish_message(msg=EnthalpyPresent, mqtt_path="house/2/attic/wtw/enthalpy_present")
    publish_message(msg=EWTPresent, mqtt_path="house/2/attic/wtw/ewt_present")


def recon():
    try:
        mqttc.reconnect()
        info_msg("Successfull reconnected to the MQTT server")
        topic_subscribe()
    except:
        warning_msg(
            "Could not reconnect to the MQTT server. Trying again in 10 seconds"
        )
        time.sleep(10)
        recon()


def topic_subscribe():
    try:
        mqttc.subscribe(
            [
                ("house/2/attic/wtw/set_ventilation_level", 0),
                ("house/2/attic/wtw/set_comfort_temperature", 0),
            ]
        )
        info_msg("Successfull subscribed to the MQTT topics")
    except:
        warning_msg(
            "There was an error while subscribing to the MQTT topic(s), trying again in 10 seconds"
        )
        time.sleep(10)
        topic_subscribe()


def on_connect(client, userdata, flags, rc):
    topic_subscribe()


def on_disconnect(client, userdata, rc):
    if rc != 0:
        warning_msg("Unexpected disconnection from MQTT, trying to reconnect")
        recon()


def main():
    global debug
    global debug_level
    global mqttc
    global ser

    debug = False
    debug_level = 0

    """Connect to the MQTT broker"""
    mqttc = mqtt.Client("whr930")
    mqttc.username_pw_set(username="myuser", password="mypass")

    """Define the mqtt callbacks"""
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_disconnect = on_disconnect

    """Connect to the MQTT server"""
    mqttc.connect("myhost/ip", port=1883, keepalive=45)

    """Open the serial port"""
    ser = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )

    mqttc.loop_start()

    while True:
        try:
            get_temp()
            get_ventilation_status()
            get_filter_status()
            get_fan_status()
            get_bypass_control()
            get_valve_status()
            get_status()
            get_operating_hours()
            get_preheating_status()

            time.sleep(8)
            pass
        except KeyboardInterrupt:
            mqttc.loop_stop()
            ser.close()
            break


if __name__ == "__main__":
    sys.exit(main())

"""End of program"""
