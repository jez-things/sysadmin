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
import sqlite3
#import rrdtool

from socket import gethostname;
#from rrdtool import update as rrd_update
DBH=None;
VERBOSE_MODE=False
POOL_TIMEOUT=1
brecv = 0;
bsent = 0;

def on_subscribe(mosq, obj, b, mid):
        print("Subscribe with mid "+str(mid)+" received.")


def on_connect(mosq, obj, rc):
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


def init_sqlite3_db(dbpath='mqtt.db'):
    conn = sqlite3.connect(dbpath)
    c = conn.cursor();
    c.execute('''CREATE TABLE IF NOT EXISTS temperature
                (date integer, desc text, tval real)''');
    c.execute('''CREATE TABLE IF NOT EXISTS misc
                (date integer, desc text, tval real)''');
    c.execute('''CREATE TABLE IF NOT EXISTS light
                (date integer, desc text, tval integer)''');
    c.execute('''CREATE TABLE IF NOT EXISTS humidity
                (date integer, desc text, humidity integer)''');
    conn.commit();
    return (conn);


def update_temperature(connhnd, tname, tstr):
    """
    """
    curtime = int(time.time());
    c = connhnd.cursor();
    temp = float(tstr);
    c.execute("INSERT INTO temperature VALUES (%d, '%s', '%f')" % (curtime, tname, temp));
    connhnd.commit();

def update_light(connhnd, lstr, lname="general"):
    curtime = int(time.time());
    c = connhnd.cursor();
    light = int(lstr);
    c.execute("INSERT INTO light VALUES (%d, '%s', '%d')" % (curtime, lname, light));
    connhnd.commit();

def update_humidity(connhnd, hname, hstr):
    curtime = int(time.time());
    c = connhnd.cursor();
    humidity = int(hstr);
    c.execute("INSERT INTO humidity VALUES (%d, '%s', '%d')" % (curtime, hname, humidity));
    connhnd.commit();

def update_rrd_db(rrdpath):
    global brecv, bsent;
    ret = -1;
    if brecv > 0 and bsent > 0:
        ret = rrd_update(rrdpath, 'N:%s:%s' %(brecv, bsent));
    return (ret);



def on_message(mosq, obj, msg):
    global brecv, bsent, DBH;
    if msg.topic == "$SYS/broker/bytes/received":
        brecv = float(msg.payload);
    elif msg.topic == "$SYS/broker/bytes/sent":
        bsent = float(msg.payload);
    elif msg.topic == "/environment/temperature/board":
        update_temperature(DBH, "board", msg.payload);
        print("TEMPERATURE %s" %(msg.payload));
    elif msg.topic == "/environment/humidity/board":
        update_humidity(DBH, "board", msg.payload);
        print("HUMIDITY %s" %(msg.payload));
    elif msg.topic == "/environment/light/general":
        print("LIGHT %s" %(msg.payload));
        update_light(DBH, msg.payload);
    else:
        print("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)
        



def mqtt_init(srvaddr="172.17.17.9", tmout=-1):
    name=gethostname();
    mos = mosquitto.Mosquitto("mqttc_%s" % (name))
    mos.username_pw_set("mosq", "dziki");
    #mos.on_connect = on_connect;
    mos.on_message = on_message;
    #mos.on_subscribe = on_subscribe;
    try:
        mos.connect(srvaddr);
    except:
        print("Failed to connect to %s" % (srvaddr));
        sys.exit(3);
    mos.loop(timeout=tmout)
    mos.publish("system/status", "GRAPH_ON", 1)
    return (mos);


def mqtt_sub(mos):
    #mos.subscribe("$SYS/broker/load/connections/5min", 0);
    #mos.subscribe("$SYS/broker/bytes/received", 0);
    #mos.subscribe("$SYS/broker/bytes/sent", 0);
    #mos.subscribe("$SYS/broker/heap/current", 0);
    mos.subscribe("environment/temperature/#", 0);
    mos.subscribe("environment/light/#", 0);
    mos.subscribe("environment/humidity/#", 0);



def mqtt_recvloop(mos):
    global brecv, bsent;
    mos.on_message = on_message;
    doloop = True;
    while doloop:
        mos.on_message = on_message;
        mos.loop();
        try:
            time.sleep(1);
        except KeyboardInterrupt:
            doloop = False;
        #print("bytes: %d/%d" %(brecv, bsent));
        #mos.unsubscribe("environment/temperature");

    mos.disconnect();




def main():
    global VERBOSE_MODE, DBH;
    DBH = init_sqlite3_db("mqtt.db");
    mos = mqtt_init('172.17.17.9', 30);
    mqtt_sub(mos);
    mqtt_recvloop(mos);
    print("bye");
    sys.exit(0);


if __name__ == "__main__":
    main()
