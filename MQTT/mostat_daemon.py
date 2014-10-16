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
#import rrdtool

from socket import gethostname;
#from rrdtool import update as rrd_update

VERBOSE_MODE=False
POOL_TIMEOUT=1
brecv = 0;
bsent = 0;

def on_subscribe(mosq, obj, mid):
        print("Subscribe with mid "+str(mid)+" received.")


def on_connect(mosq, obj, b, rc):
    if rc == 0:
        print("Connected successfully.")

#class mqtt_stat:
#    brecv = 0;
#    bsend = 0;
#    mqtt_conn = False;
#    def __init__(self, mqttc):
#        self.brecv = 0;
#        self.bsend = 0;
#        self.mqtt_conn = mqttc



def update_rrd_db(rrdpath):
    global brecv, bsent;
    ret = -1;
    if brecv > 0 and bsent > 0:
        ret = rrd_update(rrdpath, 'N:%s:%s' %(brecv, bsent));
    return (ret);



def on_message(mosq, obj, b, msg):
    global brecv, bsent;
    if msg.topic == "$SYS/broker/bytes/received":
        brecv = float(msg.payload);
    elif msg.topic == "$SYS/broker/bytes/sent":
        bsent = float(msg.payload);
    else:
        print("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)
        

#    ret = rrd_update('/root/mqtt_msg_stat.rrd', 'N:%d:%s' %(msg.payload, metric2));


def mqtt_init(srvaddr="172.17.17.9", tmout=-1):
    name=gethostname();
    mos = mosquitto.Mosquitto(name)
    mos.username_pw_set("mosq", "dziki");
    mos.on_connect = on_connect;
    mos.on_message = on_message;
    mos.on_subscribe = on_subscribe;
    try:
        mos.connect(srvaddr);
    except:
        print("Failed to connect to %s" % (srvaddr));
        sys.exit(3);
    mos.loop(timeout=tmout)
    mos.publish("system/status", "GRAPH_ON", 1)
    return (mos);


def mqtt_sub(mos):
    mos.subscribe("$SYS/broker/load/connections/5min", 0);
    mos.subscribe("$SYS/broker/bytes/received", 0);
    mos.subscribe("$SYS/broker/bytes/sent", 0);
    mos.subscribe("$SYS/broker/heap/current", 0);
    mos.subscribe("/environment/#", 0);



def mqtt_recvloop(mos):
    global brecv, bsent;
    mos.on_message = on_message;
    doloop = True;
    while doloop:
        mos.on_message = on_message;
        mos.loop();
        try:
            time.sleep(5);
        except KeyboardInterrupt:
            doloop = False;
        print("bytes: %d/%d" %(brecv, bsent));
        #mos.unsubscribe("environment/temperature");
        update_rrd_db("/root/mqtt-msg-stat.rrd");

    mos.disconnect();




def main():
    global VERBOSE_MODE;
    mos = mqtt_init('172.17.17.9', 30);
    mqtt_sub(mos);
    mqtt_recvloop(mos);
    print("bye");
    sys.exit(0);


if __name__ == "__main__":
    main()
