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
import rrdtool

from socket import gethostname;

VERBOSE_MODE=False
POOL_TIMEOUT=1
S_PORT_PATH="/dev/ttyACM0"
S_PORT_BAUDRATE="115200"

class mqttException(Exception):
    def __init__(self, topic, msg):
        self.topic = topic;
        self.msg = msg;
    def __str__(self):
        return (self.topic);

def ifvprint(line):
    global VERBOSE_MODE;
    if VERBOSE_MODE > 0:
        print("> %s" %(line[:-1]));

def on_publish(mosq, obj, mid):
    print("Message "+str(mid)+" published.");

def on_connect(mosq, obj, rc):
    if rc == 0:
        print("Connected successfully");


def mqtt_init(srvaddr="127.0.0.1", tmout=-1):
    name=gethostname();
    mos = mosquitto.Mosquitto(name)
    mos.username_pw_set("jez", "cyk");
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
    ifvprint("\nSending \"%s\" to \"%s\"\n" % (msg, topic));
    try:
        mqtt_conn.publish(topic, msg, 0);
    except Exception as e:
        print("ERROR: Failed to send msg to %s %s" %(topic, e));
        raise mqttException(topic, e);
        return False;

def usage():
    print("usage: serial2mqtt -s [serial_path] -b [baudrate] -vh");
    sys.exit(64);

def init_serial(sp_path, sp_baudrate):
    serial_port = serial.Serial();
    serial_port.port = sp_path;
    serial_port.baudrate = sp_baudrate;
    serial_port.timeout=0;
    return serial_port;


def proc_line(mqtt_conn, lbuf):
    ifvprint("Processing line: "+lbuf[:-2]);
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


def read_loop(s_port, pool_timeout=1):
    try:
        s_port.open()
    except:
        print("Failed to open serial port");
        sys.exit(3);

    try:
        s_port.flushOutput()
    except:
        print("Failed to flush serial port");
        sys.exit(3);
    ch = '';
    tempbuf = "";
    DO_LOOP = True;
    MQTT_CONN = mqtt_init("172.17.17.9", -1);
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
                ifvprint("Processing message: \"%s\"" % (line[:-2]));
                proc_line(MQTT_CONN, line[:-2]);
        time.sleep(int(pool_timeout));
    print("Well done! End of work");
#
############################################################################
# main
###
#
def main():
    global VERBOSE_MODE;
    global S_PORT_BAUDRATE;
    global S_PORT_PATH;
    global POOL_TIMEOUT;

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:b:t:v", ["help", "serialpath=","baudrate=","timeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    VERBOSE_MODE = False
    for o, a in opts:
        if o == "-v":
            VERBOSE_MODE = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--serialpath"):
            S_PORT_PATH = a
        elif o in ("-b", "--baudrate"):
            S_PORT_BAUDRATE = a
        elif o in ("-t", "--timeout"):
            POOL_TIMEOUT = a;
        else:
            print("ERROR: Unhandled option");
            sys.exit(9);
    # ...
    sprt = init_serial(S_PORT_PATH, S_PORT_BAUDRATE)
    read_loop(sprt, POOL_TIMEOUT);

if __name__ == "__main__":
    main()
