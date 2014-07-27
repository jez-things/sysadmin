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
import lockfile
import getopt

import serial

import mosquitto

from socket import gethostname;

VERBOSE_MODE=False
POOL_TIMEOUT=1
S_PORT_PATH="/dev/ttyACM0"
S_PORT_BAUDRATE=115200

class ArduinoMQTT:
	msgbuf = [];
	def __init__(self, serial_port_path="/dev/ttyACM0", bd=115200, tmout=1):
		self.serial_port_path = serial_port_path;
		self.VERBOSE_MODE = True;
		self.serial_port = serial.Serial();
		sp = self.serial_port;
		sp.port = serial_port_path;
		sp.baudrate = bd;
		sp.timeout = tmout;
		self.MQTT_conn = False;
		return (None);

	def init_serial(self):
    		try:
        		self.serial_port.open()
    		except:
			self.vprint("Failed to open serial port %s" % (self.serial_port_path));
			self.msgbuf.append("Failed to open serial port");
        		sys.exit(3);

    		try:
        		self.serial_port.flushOutput()
    		except:
			self.vprint("Failed to flush  serial port");
			self.msgbuf.append("Failed to flush serial port");
        		sys.exit(3);
    		return self.serial_port;
	def flush_msgbuf(self):
		cnt=0;
		for ln in self.msgbuf:
			print("mbuf: %s" %(ln));
			cnt+=1;
		return (cnt);
	def MQTT_init(self, mqtt_user, mqtt_pass):
		self.hostname = socket.gethostname();
		self.MQTT_conn = mosquitto.Mosquitto(self.hostname)
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


def on_publish(mosq, obj, mid):
    print("Message "+str(mid)+" published.");

def on_connect(mosq, obj, rc):
    if rc == 0:
        print("Connected successfully");


def mqtt_init(ar2mqtt, srvaddr="127.0.0.1"):
    mos = ar2mqtt.MQTT_init("jez", "cyk");
    tmout = armqtt.timeout;
    mos.on_publish = on_publish;
    mos.on_connect = on_connect;
    try:
        mos.connect(srvaddr);
    except:
        print("Failed to connect to %s" % (srvaddr));
        sys.exit(3);
    mos.loop(timeout=5)
    return (mos);

def mqtt_bcast(mqtt_conn, topic, msg):
    try:
        mqtt_conn.publish(topic, msg, 0);
    except Exception as e:
        print("ERROR: Failed to send msg to %s %s" %(topic, e));
        raise mqttException(topic, e);
        return False;

def usage():
    print("usage: serial2mqtt -s [serial_path] -b [baudrate] -vh");
    sys.exit(64);



def proc_line(mqtt_conn, lbuf):
    #ifvprint("Processing line: "+lbuf[:-2]);
    lbufclean = filter(lambda x: x in string.printable, lbuf)
    for lf in lbufclean.split(" "):
        #print("msg \"%s\""%(lf));
        val = lf.split("=");
        if len(val) == 2:
            nam=val[0];
            v=val[1];
            #ifvprint("DEBUG: \"%s\"\t\"%s\"" % (nam, v));
            if nam == "tempC":
                mqtt_bcast(mqtt_conn, "environment/dht11/temperature", v)
            elif nam == "hum":
                mqtt_bcast(mqtt_conn, "environment/dht11/humidity", v)
            elif nam == "dewpointC":
                mqtt_bcast(mqtt_conn, "environment/dht11/devpoint", v)
            #mqtt_conn.loop(timeout=10);
        else:
            print("ERROR: Received incomplette message \"%s\" len=%s"%(lf[:-2], len(val[:-2])));

from curses.ascii import isprint

def printable(istr):
        return ''.join(char for char in istr if isprint(char))


def init_loop(ar_mqtt):
    s_port = ar_mqtt.init_serial();
    DO_LOOP = True;
    MQTT_CONN = mqtt_init(ar_mqtt, "172.17.17.9");
    line = ""
    while DO_LOOP:
        try:
            lbuf = s_port.readline();
        except Exception, msg:
            print("Read error! %s" %(msg));
            DO_LOOP = False
            break;
        else: 
            line = printable(lbuf)
            if len(line[:-2]) > 40:
                ar_mqtt.vprint("Processing message: \"%s\"" % (line[:-2]));
                proc_line(MQTT_CONN, line[:-2]);
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
        opts, args = getopt.getopt(sys.argv[1:], "hs:b:t:v", ["help", "serialpath=","baudrate=","timeout="])
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
        elif o in ("-s", "--serialpath"):
            ar_mqtt.serial_port_path = a
        elif o in ("-b", "--baudrate"):
            ar_mqtt.baudrate = int(a)
        elif o in ("-t", "--timeout"):
            ar_mqtt.timeout = int(a);
        else:
            print("ERROR: Unhandled option");
            sys.exit(9);
    # ...
    init_loop(ar_mqtt);

if __name__ == "__main__":
    main()
