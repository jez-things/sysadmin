#!/usr/bin/env python2.7

import os,sys,time
import grp
import signal

import syslog
import glob
import traceback

import httplib
import string
import getopt


import mosquitto
import random

import socket
import subprocess

import pprint
#from socket import gethostname;
DEBUG=False
VERBOSE_MODE=False
POOL_TIMEOUT=1
#ar_mqtt=False;

class SensorException(Exception):
    em = {100:"Incorrect arguments", \
          101:"Internal failure!"}


class SensorError(SensorException):

    def __init__(self, value):
        sys.stderr.write(value);
        sys.exit(3);

class SensorFallback(SensorException):
    em = {200:"Failed to read data from sensor"}

    def __init__(self, value):
        self.value = value;

    def __str__(self):
        return repr(self.value)


class MQTTH:
    conn_hnd = None;
    mosquitto = None;
    user = "";
    password = "";
    timeout = 5;
    server_addr = "127.0.0.1";
    my_hostname = None;
    DOWORK= True;
    VERBOSE = False

    def __init__(self, user, password, verbose=False):
        self.connect_cb = on_connect;
        self.DOWORK = True;
        self.VERBOSE = verbose;
        self.user = user;
        self.password = password;
        self.my_hostname = socket.gethostname();
        self.mosquitto = mosquitto.Mosquitto("mqttc");
    	self.mosquitto.username_pw_set(self.user, self.password);
        self.mosquitto.on_publish = on_publish;
        self.mosquitto.on_message = on_message;
        #self.mosquitto.on_message = ArduinoMQTT.MQTT_on_message;;

    def connect(self, srv, c_cb=None):
        if c_cb != None:
            self.conn_hnd.on_connect = c_cb;

        self.server_addr = srv;
        try:
            self.conn_hnd = self.mosquitto.connect(self.server_addr);
        except Exception as e:
            print("!> couldn't connect to %s: %s" %(self.server_addr, e))
            return None
        return (self.conn_hnd);

#
    def loop(self, tm=5):
        return (ret)
#
##################################################################
#
class ArduinoMQTT:
        totalmsg=0;
        mqtth = None
	msgbuf = [];
        VERBOSE = True;

	def __init__(self, muser, mpass, verbose=False, timeout=5):
            self.VERBOSE = verbose;
            self.timeout = timeout;
            self.mqtth = MQTTH(user=muser, password=mpass);

        def MQTT_init(self, srv=None):
                if srv == None:
                    srv = "127.0.0.1"
                self.vprint("Connecting to %s" %(srv));
		self.mqtth.connect(srv);
		return (self.mqtth.conn_hnd);
        def MQTT_on_message(self, mosq, obj, msg):
            self.msgbuf.append("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)
            return (msg);

        def MQTT_polling(self):
            try:
                ret = self.mqtth.mosquitto.loop(timeout=self.mqtth.timeout);
            except Exception as e:
                err_print("!> Operating problems %s: %s" %(self.mqtth.server_addr, e))

            #self.mqtth.loop(5)
            return (0);

        def MQTT_publish(self, topic, msg):
            '''
                Broadcasting a given message "msg" on MQTT channel
            '''
            dprint("Sending message \"%s\" to \"%s\"" %(msg, topic))
            try:
                ret = self.mqtth.mosquitto.publish(topic, msg);
            except KeyboardInterrupt:
                print("|->\t\tKeyboard interruption!");
            except Exception as e:
                self.vprint("ERROR: Failed to send msg \"%s\"  to  \"%s\": %s" %(msg, topic, e));
                raise mqttException(topic, msg);
                return None
            self.totalmsg+=1;
            return (ret);

	def vprint(self, line):
            """
            | Verbose print
            """
            lbuf = "=> %s" %(line);
            self.msgbuf.append(lbuf)
    	    if self.VERBOSE:
                print(lbuf);
            return (lbuf);
	
        def err_print(self, line):
            """
            | Error print
            """
            lbuf = "!> %s" %(line);
            self.msgbuf.append(lbuf)
    	    if self.VERBOSE:
                print(lbuf);
            return (lbuf);
        #def flush_msgbuf(self):
        #    self.open("msgbuf.log", 'a') :




class mqttException(Exception):
    def __init__(self, topic, msg):
        self.topic = topic;
        self.msg = msg;
    def __str__(self):
        return (self.topic);

###########################################
# Callbacks:
#

def dprint(msg):
    global DEBUG
    if DEBUG:
        print("=> %s" %(msg));
    return (msg);

def on_message(mosq, obj, msg):
    dprint("Message received on topic "+msg.topic+" with QoS "+str(msg.qos)+" and payload "+msg.payload)


def on_publish(mosq, obj, mid):
    sys.stderr.write('.');
    dprint("=> Message \""+str(mid)+"\" published.");

def on_connect(mosq, obj, rc):
    if rc == 0:
        dprint("=> Connected successfully");

#####





def read_temp_raw(device_id):
        devpath='/sys/bus/w1/devices/%s/w1_slave' %(device_id)
	try:
    		f = open(devpath , 'r')
	except IOError as e:
                raise SensorFallback("Couldn't open device file in path %s :%s" % (devpath, e.strerror));
	else:
            try:
		lines = f.readlines()
            except KeyboardInterrupt:
                f.close()
                return None
            except Exception as e:
                raise SensorFallback("Couldn't read device file in path %s :%s" % (devpath, e.strerror));
            finally:
		f.close()
	return lines


def read_temp(opt):
        """
        # device_file = Path to device.
        # fieldno = Name of URL parameter "field". Limited to number.
        # DS18B20 
        """
	lines = read_temp_raw(opt)
	if lines == None:
		return None;
	temp_c = False;
	while lines[1].strip()[-3:] != 'YES':
		time.sleep(0.2)
                try:
		    lines = read_temp_raw(opt)
                except SensorFallback:
                    return None
		equals_pos = lines[1].find('t=')
		if equals_pos != -1:
			temp_string = lines[1][equals_pos+2:]
			try:
				temp_c = float(temp_string) / 1000.0
			except Exception:
				print("conversion failure!")
			return temp_c
		else:
			return "failure"


def get_pcf8591p(opt):
        '''
        | Read data from ADC PCF8591 with photoresistor hooked
        '''
	f = os.popen("/usr/local/bin/pcf8591p %s" % (opt));
	vstr = f.read()[:-1]
	f.close();
	return (vstr);

def get_dht11(opt):
        '''
            Get data from DHT11
        '''
        binpath="/usr/local/bin/Adafruit_DHT";
        dht11str=""
        pin = opt;
        while len(dht11str) != 2:
                try:
                        f = os.popen("%s 11 %s" %(binpath, pin));
                        dht11str = f.read()[:-1]
                        f.close();
                except Exception as e:
                        dprint("failed to get data from dht11")
                        return None
        return (dht11str);



class Sensor:
    '''
        Main classe to describe activity of sensors
    '''
    getdata_cb = None;
    senddata_cb = None;
    arg_cb = ""
    ret_cb = ""
    name = ""
    mqtt_topic = ""
    errbuf = []
    exec_ok=0
    
    def __init__(self, s_getdata_cb, s_name, s_mqtt_topic, arg_cb):
        self.getdata_cb = s_getdata_cb;
        self.name = s_name;
        self.mqtt_topic = s_mqtt_topic;
        self.errbuf = []
        self.arg_cb = arg_cb;
        self.ret_cb = None;

    def set_cb(self, arg):
        for a in arg.keys():
            if a == "opt":
                self.opt = arg[a];
            elif a == "snd_cb":
                self.senddata_cb = arg[a];
            elif a == "get_cb":
                self.getdata_cb = arg[a];
            else:
                raise SensorException(100);
        
        return 0

    def call_dataget(self, opt=None):
        try:
            self.ret_cb = self.getdata_cb(self.arg_cb)
        except KeyboardInterrupt:
            self.dprint("keyboard interruption");
        except Exception as e:
            self.dprint("While getting data from sensor \"%s\"! %s" %(self.name,e));
        else:
            self.exec_ok+=1;
        return (self.ret_cb);


    def call_datasend(self, opt=None):
        self.ret_cb = self.senddata_cb(self.arg_cb)
        return (self.ret_cb);

    def send_via_mqtt(self, mos):
        print("Sending");
        return (0);

    def log_error(self, errmsg): 
        print("ERROR: %s" % (errmsg));
        return (errmsg);

    def __str__(self):
        strbuf=" | %s@%s | " % (self.name, self.mqtt_topic)
        if self.ret_cb ==  None:
            strbuf+=self.ret_cb+" | ";


        return (strbuf)

    def dprint(self, msg):
        msgbuf = ("==> %s | " %(msg));
        self.errbuf.append(msgbuf);
        print msgbuf;
        return (msgbuf);


class SensorSet:
    
    ss_list = {}
    ss_cb_get_data = {}
    ss_cb_send_data = {}
    ss_cnt  = 0
    DEBUG  = False
    ss_debug_buf = []

    def __init__(self):
        self.ss_list = {}
        self.s_cnt = 0;

    def add_sensor(self, s_name, s_mqtt_topic, s_getdata_cb, arg_cb):
        sen = Sensor(s_getdata_cb, s_name, s_mqtt_topic, arg_cb)
        self.ss_list[s_name] = sen;
        self.ss_cb_get_data[s_name] = s_getdata_cb;
        self.ss_cnt+=1;
        return(sen);

    def collect_data(self):
        for sens in self.ss_list.keys():
            self.ss_list[sens].call_dataget(None);
            #str(self.ss_list[sens])
            sens = self.ss_list[sens];
            #sens.call_dataget(None);
            #sens.call_dataget(None);
            
    def send_data(self):
        for sens in self.ss_list.keys():
            self.ss_list[sens].call_datasend(None);
            #str(self.ss_list[sens])
            sens = self.ss_list[sens];



    def get_datas(self):
        for fsen in self.ss_list.keys():
            cb_a = self.ss_list[fsen].arg_cb;
            cb_a = self.ss_list[fsen].arg_cb;
            ret_cb = self.ss_list[fsen].ret_cb;

            ret_cb = self.ss_list[fsen].getdata_cb(cb_a);


## End of SensorSet  ######################
###########################################


def Send2MQTT(armqtt, sns):
    '''
        Send the data obtained from sensores to MQTT broker
    '''
    sens_lst = sns.ss_list
    for s in sens_lst.keys():
        topic = sens_lst[s].mqtt_topic
        msg = sens_lst[s].ret_cb
        armqtt.vprint("\t=> Sending message (\"%s\") to %s" %(msg, topic))
        try:
            armqtt.MQTT_publish(topic, msg)
        except Exception as e:
            armqtt.vprint("Failed to publish msg (%s) on topic \"%s\": %s" %(msg, topic, e));

    return (0);

#
############################################################################
# main
###
#
def main():
    '''
        Here we start
    '''
    VERBOSE=False
    timeout=5
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:b:t:v", ["help", "timeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o == "-v":
            VERBOSE = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-t", "--timeout"):
            timeout = int(a);
        else:
            print("ERROR: Unhandled option");
            sys.exit(9);
    # ...
    ar_mqtt = ArduinoMQTT("jez", "cyk", verbose=VERBOSE);
    mqtt_conn_hnd = ar_mqtt.mqtth.mosquitto;
    mqtth = ar_mqtt.mqtth;
    
    '''
    | - connection loop
    '''
    ar_mqtt.MQTT_init("172.17.17.9");
    ar_mqtt.MQTT_polling();
    
    '''
    Here there's the place for new sensores!
    Add them separately
    '''

    SNS = SensorSet();
    SNS.add_sensor("ds18b20", "/environment/temperature/board",read_temp, "28-0000055a8be7");
    SNS.add_sensor("dht11", "/environment/humidity/board", get_dht11, "25");
    SNS.add_sensor("pcf8591", "/environment/light/general", get_pcf8591p, "0" );
    #SNS.collect_data();
    
    print("=> Waiting in loop %dseconds" %(mqtth.timeout))
    while mqtth.DOWORK:
#        if len(ar_mqtt.msgbuf) > 10:
#            for l in ar_mqtt.msgbuf:
#                print("MBUF> %s " %(l));
#                ar_mqtt.msgbuf.pop()
        ##################
        SNS.collect_data();
        ##################
        try:
            Send2MQTT(ar_mqtt, SNS);
        except Exception as e:
            print("!> Operating problems %s: %s" %(mqtth.server_addr, e))
        if mqtth.DOWORK:
            try:
                time.sleep(mqtth.timeout);
            except KeyboardInterrupt:
                mqtth.DOWORK=False
    print("=> Statistics: sent %d messages" %(ar_mqtt.totalmsg));

# NOT REACHED

if __name__ == "__main__":
    main()



def usage():
    print("usage: mqttc -vh");
    sys.exit(64);
