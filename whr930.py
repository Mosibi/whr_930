#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Interface with a StorkAir WHR930

Publish every 10 seconds the status on a MQTT topic
Listen on MQTT topic for commands to set the ventilation level
"""

import paho.mqtt.client as mqtt
import time
import serial

def debug_msg(message):
    if debug == True:
        print '{0} DEBUG: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message)

def warning_msg(message):
    print '{0} WARNING: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message)

def info_msg(message):
    print '{0} INFO: {1}'.format(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime()), message)

def debug_data(serial_data):
    print 'Ack           : {0} {1}'.format(serial_data[0], serial_data[1])
    print 'Start         : {0} {1}'.format(serial_data[2], serial_data[3])
    print 'Command       : {0} {1}'.format(serial_data[4], serial_data[5])
    print 'Nr data bytes : {0} (integer {1})'.format(serial_data[6], int(serial_data[6], 16))

    n = 1
    while n <= int(serial_data[6], 16):
        print 'Data byte {0}   : Hex: {1}, Int: {2}, Array #: {3}'.format(n, serial_data[n+6], int(serial_data[n + 6], 16), n + 6)

        n += 1
    
    print 'Checksum      : {0}'.format(serial_data[-2])
    print 'End           : {0} {1}'.format(serial_data[-1], serial_data[-0])        

def on_message(client, userdata, message):
    if message.topic == 'house/2/attic/wtw/set_ventilation_level':
        if int(message.payload) >= 0 and int(message.payload) <= 3:
            set_ventilation_level(message.payload)
        else:
            warning_msg('Received a message on topic {0} with a wrong payload: {1}'.format(message.topic, message.payload))
    else:
        debug_msg("message received: topic: {0}, payload: {1}, userdata: {2}".format(message.topic, message.payload, userdata))

def publish_message(msg, mqtt_path):                                                                      
    mqttc.publish(mqtt_path, payload=msg, qos=0, retain=False)
    time.sleep(0.1)
    debug_msg('published message {0} on topic {1} at {2}'.format(msg, mqtt_path, time.asctime(time.localtime(time.time()))))

def serial_command(cmd):
    data = []
    ser.write(cmd)
    time.sleep(1)

    while ser.inWaiting() > 0:
        data.append(ser.read(1).encode('hex'))

    if len(data) > 0:
        return data
    else:
        return None

def set_ventilation_level(nr):
    if nr == '0':
        data = serial_command("\x07\xF0\x00\x99\x01\x01\x48\x07\x0F")
    elif nr == '1':
        data = serial_command("\x07\xF0\x00\x99\x01\x02\x49\x07\x0F")
    elif nr == '2':
        data = serial_command("\x07\xF0\x00\x99\x01\x03\x4A\x07\x0F")
    elif nr == '3':
        data = serial_command("\x07\xF0\x00\x99\x01\x04\x4B\x07\x0F")

    if data:
        if ( data[0] == '07' and data[1] == 'f3' ):
            info_msg('Changed the ventilation to {0}'.format(nr))
        else:
            warning_msg('Changing the ventilation to {0} went wrong, did not receive an ACK after the set command'.format(nr))
    else:
        warning_msg('Changing the ventilation to {0} went wrong, did not receive an ACK after the set command'.format(nr))

def get_temp():
    data = serial_command("\x07\xF0\x00\x0F\x00\xBC\x07\x0F")

    if data == None:
        warning_msg('get_temp function could not get serial data')
    else:
        OutsideAirTemp = int(data[7], 16) / 2.0 - 20
        SupplyAirTemp = int(data[8], 16) / 2.0 - 20
        ReturnAirTemp = int(data[9], 16) / 2.0 - 20
        ExhaustAirTemp = int(data[10], 16) / 2.0 - 20

        publish_message(msg=OutsideAirTemp, mqtt_path='house/2/attic/wtw/outside_air_temp')
        publish_message(msg=SupplyAirTemp, mqtt_path='house/2/attic/wtw/supply_air_temp')
        publish_message(msg=ReturnAirTemp, mqtt_path='house/2/attic/wtw/return_air_temp')
        publish_message(msg=ExhaustAirTemp, mqtt_path='house/2/attic/wtw/exhaust_air_temp')

        debug_msg('OutsideAirTemp: {0}, SupplyAirTemp: {1}, ReturnAirTemp: {2}, ExhaustAirTemp: {3}'.format(OutsideAirTemp, SupplyAirTemp, ReturnAirTemp, ExhaustAirTemp))

def get_ventilation_status():
    data = serial_command("\x07\xF0\x00\xCD\x00\x7A\x07\x0F")

    if data == None:
        warning_msg('get_ventilation_status function could not get serial data')
    else:
        ReturnAirLevel = int(data[13], 16)
        SupplyAirLevel = int(data[14], 16)
        FanLevel = int(data[15], 16) - 1
        IntakeFanActive = int(data[16], 16)

        if IntakeFanActive == 1:
            StrIntakeFanActive = 'Yes'
        elif IntakeFanActive == 0:
            StrIntakeFanActive = 'No'
        else:
            StrIntakeFanActive = 'Unknown'
            
        publish_message(msg=FanLevel, mqtt_path='house/2/attic/wtw/ventilation_level')
        publish_message(msg=StrIntakeFanActive, mqtt_path='house/2/attic/wtw/intake_fan_active')
        debug_msg('ReturnAirLevel: {}, SupplyAirLevel: {}, FanLevel: {}, IntakeFanActive: {}'.format(ReturnAirLevel, SupplyAirLevel, FanLevel, StrIntakeFanActive))

def get_fan_status():
    # 0x07 0xF0 0x00 0x0B 0x00 0xB8 0x07 0x0F 
    # Checksum: 0xB8 (0x00 0x0B) = 0 + 11 + 0 + 173 = 184
    # End: 0x07 0x0F

    data = serial_command("\x07\xF0\x00\x0B\x00\xB8\x07\x0F")

    if data == None:
        warning_msg('function get_fan_status could not get serial data')
    else:
        IntakeFanSpeed = int(data[7], 16)
        ExhaustFanSpeed = int(data[8], 16)  
        IntakeFanRPM = int(1875000 / int(''.join([str(int(data[9], 16)), str(int(data[10], 16))])))
        ExhaustFanRPM = int(1875000 / int(''.join([str(int(data[11], 16)), str(int(data[12], 16))])))

        publish_message(msg=IntakeFanSpeed, mqtt_path='house/2/attic/wtw/intake_fan_speed')
        publish_message(msg=ExhaustFanSpeed, mqtt_path='house/2/attic/wtw/exhaust_fan_speed')
        publish_message(msg=IntakeFanRPM, mqtt_path='house/2/attic/wtw/intake_fan_speed_rpm')
        publish_message(msg=ExhaustFanRPM, mqtt_path='house/2/attic/wtw/exhaust_fan_speed_rpm')

        debug_msg('IntakeFanSpeed {0}%, ExhaustFanSpeed {1}%, IntakeAirRPM {2}, ExhaustAirRPM {3}'.format(IntakeFanSpeed,ExhaustFanSpeed,IntakeFanRPM,ExhaustFanRPM))
    
def get_filter_status():
    # 0x07 0xF0 0x00 0xD9 0x00 0x86 0x07 0x0F 
    # Start: 0x07 0xF0
    # Command: 0x00 0xD9
    # Number data bytes: 0x00
    # Checksum: 0x86 (0x00 0xD9) = 0 + 217 + 0 + 173 = 390
    # End: 0x07 0x0F

    data = serial_command("\x07\xF0\x00\xD9\x00\x86\x07\x0F")

    if data == None:
        warning_msg('get_filter_status function could not get serial data')
    else:
        if int(data[18], 16) == 0:
            FilterStatus = 'Ok'
        elif int(data[18], 16) == 1:
            FilterStatus = 'Full'
        else:
            FilterStatus = 'Unknown'
        
        publish_message(msg=FilterStatus, mqtt_path='house/2/attic/wtw/filter_status')
        debug_msg('FilterStatus: {0}'.format(FilterStatus))
    
def recon():
    try:
        mqttc.reconnect()
        info_msg('Successfull reconnected to the MQTT server')
        topic_subscribe()
    except:
        warning_msg('Could not reconnect to the MQTT server. Trying again in 10 seconds')
        time.sleep(10)
        recon()
        
def topic_subscribe():
    try:
        mqttc.subscribe("house/2/attic/wtw/set_ventilation_level", 0)
        info_msg('Successfull subscribed to the MQTT topics')
    except:
        warning_msg('There was an error while subscribing to the MQTT topic(s), trying again in 10 seconds')
        time.sleep(10)
        topic_subscribe()

def on_connect(client, userdata, flags, rc):
    topic_subscribe()
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        warning_msg('Unexpected disconnection from MQTT, trying to reconnect')
        recon()

### 
# Main
###
debug = False

# Connect to the MQTT broker
mqttc = mqtt.Client('whr930')
mqttc.username_pw_set(username="myuser",password="mypass")

# Define the mqtt callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_disconnect = on_disconnect

# Connect to the MQTT server
mqttc.connect('myhost/ip', port=1883, keepalive=45)

# Open the serial port
ser = serial.Serial(port = '/dev/ttyUSB0', baudrate = 9600, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE)

mqttc.loop_start()
while True:
    try:
        get_temp()
        get_ventilation_status()
        get_filter_status()
        get_fan_status()

        time.sleep(10)
        pass
    except KeyboardInterrupt:
        mqttc.loop_stop()
        ser.close()
        break
    
# End of program
