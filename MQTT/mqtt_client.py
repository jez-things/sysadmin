#!/usr/bin/env python2.7

import os,sys,time
import grp
import signal

import syslog
import glob
import traceback

import httplib
import string
import daemon
import getopt


import mosquitto
import random

import socket
import subprocess
#from socket import gethostname;

VERBOSE_MODE=False
POOL_TIMEOUT=1
#ar_mqtt=False;

class ArduinoMQTT:
	msgbuf = [];
        timeout = 2;
	def __init__(self):
		self.VERBOSE_MODE = True;
		self.MQTT_conn = False;
		return (None);

	def MQTT_init(self, mqtt_user, mqtt_pass):
		self.hostname = socket.gethostname();
		self.MQTT_conn = mosquitto.Mosquitto("mqttc")
    		self.MQTT_conn.username_pw_set(mqtt_user, mqtt_pass);
		return (self.MQTT_conn);
	def vprint(self, line):
    		if self.VERBOSE_MODE > 0:
        		print("> %s" %(line));


class mqttException(Exception):
    def __init__(self, topic, msg):
        self.topic = topic;
        self.msg = msg;
    def __str__(self):
        return (self.topic);


def on_publish(mosq, mid):
    print("Message "+str(mid)+" published.");

def on_connect(mosq, rc):
    if rc == 0:
        print("Connected successfully");


def mqtt_init(ar2mqtt, srvaddr="127.0.0.1"):
    mos = ar2mqtt.MQTT_init("jez", "cyk");
    tmout = ar2mqtt.timeout;
    mos.on_publish = on_publish;
    mos.on_connect = on_connect;
    try:
        mos.connect(srvaddr);
    except:
        print("Failed to connect to %s" % (srvaddr));
        sys.exit(3);
    mos.loop(timeout=tmout)
    return (mos);

def mqtt_bcast(mqtt_conn, topic, msg):
    try:
        mqtt_conn.publish(topic, msg);
    except Exception as e:
        print("ERROR: Failed to send msg to %s %s" %(topic, e));
        raise mqttException(topic, e);
        return False;

def usage():
    print("usage: mqttc -vh");
    sys.exit(64);


def read_temp_raw(device_file):
	try:
		f = open(device_file, 'r')
	except IOError as e:
		logit("Couldn't read device file in path \"%s\":%s" % (device_file, e.strerror))
		return None;
	else:
		lines = f.readlines()
		f.close()
	return lines

# device_file = Path to device.
# fieldno = Name of URL parameter "field". Limited to number.
def read_temp(device_file):
	lines = read_temp_raw(device_file)
	if lines == None:
		return None;
	temp_c = False;
	while lines[1].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw(device_file)
		equals_pos = lines[1].find('t=')
		if equals_pos != -1:
			temp_string = lines[1][equals_pos+2:]
			try:
				temp_c = float(temp_string) / 1000.0
			except Exception:
				logit("conversion failure!")
			return temp_c
		else:
			return "failure"




def get_data():
    return [1];

def send_data(mqttconn, datbuf = []):
    
    t_board = read_temp('/sys/bus/w1/devices/28-0000055a8be7/w1_slave');
    mqtt_bcast(mqttconn, "/environment/temperature/board", str(t_board));
    return 0;

def init_loop(ar_mqtt):
    DO_LOOP = True;
    MQTT_CONN = mqtt_init(ar_mqtt, "172.17.17.9");
    
    while DO_LOOP:
        try:
            datbuf = get_data();
        except Exception, msg:
            print("Read error! %s" %(msg));
            DO_LOOP = False
            break;
        else: 
            send_data(MQTT_CONN, datbuf);
        time.sleep(ar_mqtt.timeout);
    print("Well done! End of work");
#
############################################################################
# main
###
#
def main():
    ar_mqtt = ArduinoMQTT();

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:b:t:v", ["help", "timeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    ar_mqtt.VERBOSE_MODE = False
    for o, a in opts:
        if o == "-v":
            ar_mqtt.VERBOSE_MODE = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-t", "--timeout"):
            ar_mqtt.timeout = int(a);
        else:
            print("ERROR: Unhandled option");
            sys.exit(9);
    # ...
    init_loop(ar_mqtt);

if __name__ == "__main__":
    main()
