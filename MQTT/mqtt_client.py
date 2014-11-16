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
    user = "";
    password = "";
    timeout = 5;
    mqtt_srv = "127.0.0.1";
    VERBOSE = False
    mosquitto = None;
    DOWORK= True;
    my_hostname = None;
    conn_hnd = None;

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

    def connect(self, srv, c_cb=None):
        if c_cb != None:
            self.conn_hnd.on_connect = c_cb;

        self.mqtt_srv = srv;
        try:
            self.conn_hnd = self.mosquitto.connect(self.mqtt_srv);
        except Exception as e:
            print("!> couldn't connect to %s: %s" %(self.mqtt_srv, e))
            return None
        return (self.conn_hnd);

#
    def loop(self, tm=5):
        try:
            ret = self.mosquitto.loop(timeout=self.timeout);
        except Exception as e:
            print("!> Operating problems %s: %s" %(self.mqtt_srv, e))

        '''
            Here there's the place for new sensores!
            Add them separately
        '''

        SNS = SensorSet();
        SNS.add_sensor("ds18b20", "/environment/temperature/board",read_temp, "28-0000055a8be7");
        #SNS.add_sensor("dht11", "/environment/humidity/board", get_dht11, "25");
        SNS.add_sensor("pcf8591", "/environment/light/general", get_pcf8591p, "0" );
        #SNS.collect_data();

        MQTT_CONN = self.conn_hnd;
        databuf = {};
        while self.DOWORK:
            SNS.collect_data();
            try:
                send_data(self.conn_hnd, SNS);
            except Exception as e:
                print("!> Operating problems %s: %s" %(self.mqtt_srv, e))

            if self.DOWORK:
                time.sleep(self.timeout);
        print("=> Well done! End of work");
        return (ret)
#
##################################################################
#
class ArduinoMQTT:
	msgbuf = [];
        mqtt = None
        VERBOSE = True;

	def __init__(self, muser, mpass, verbose=False, timeout=5):
            self.VERBOSE = verbose;
            self.timeout = timeout;
            self.mqtt = MQTTH(user=muser, password=mpass);

        def MQTT_init(self, srv=None):
                if srv == None:
                    srv = "127.0.0.1"
                self.vprint("Connecting to %s" %(srv));
		self.mqtt.connect(srv);
		return (self.mqtt.conn_hnd);

        def MQTT_polling(self):
            self.mqtt.loop(5)
            return (0);

        def MQTT_publish(self, topic, msg):
            '''
                Broadcasting a given message "msg" on MQTT channel
            '''
            try:
                ret = self.mqtt.publish(topic, msg);
                #ret = mqtt_conn
            except KeyboardInterrupt:
                vprint("|->\t\tKeyboard interruption!");
            except Exception as e:
                vprint("ERROR: Failed to send msg \"%s\"  to  \"%s\": %s" %(msg, topic, e));
                raise mqttException(topic, e);
                sys.exit(3);
            return (ret);

	def vprint(self, line):
            """
            | Verbose print
            """
            lbuf = "=> %s" %(line);
    	    if self.VERBOSE:
                print(lbuf);
            return (lbuf);


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

def on_publish(mosq, obj, mid):
    #print("=> Message "+str(mid)+" published.");
    print(".");

def on_connect(mosq, obj, rc):
    if rc == 0:
        print("=> Connected successfully");

#####





def read_temp_raw(device_id):
        devpath='/sys/bus/w1/devices/%s/w1_slave' %(device_id)
	try:
    		f = open(devpath , 'r')
	except IOError as e:
                raise SensorFallback("Couldn't read device file in path %s :%s" % (devpath, e.strerror));
	else:
		lines = f.readlines()
		f.close()
	return lines

# device_file = Path to device.
# fieldno = Name of URL parameter "field". Limited to number.
def read_temp(opt):
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
	f = os.popen("/usr/local/bin/pcf8591p %s" % (opt));
	vstr = f.read()[:-1]
	f.close();
	return (vstr);

def get_dht11(opt):
        binpath="/usr/local/bin/Adafruit_DHT";
        dht11str=""
        pin = opt;
        while len(dht11str) != 2:
                try:
                        f = os.popen("%s 11 %s" %(binpath, pin));
                        dht11str = f.read()[:-1]
                        f.close();
                except:
                        print "failed to get data from dht11"
        return (dht11str);


#def get_data(sname):
#    dta_ret = None;
#    if sname == "light":
#        dta_ret = get_pcf8591p("0");
#    elif sname == "hum":
#        dta_ret  = get_dht11("25")
#    elif sname == "t_board":
#        dta_ret = read_temp("28-0000055a8be7");
#    else:
#        print("!!!> Error unknown data type \"%s\"" %(sname));
#        return None
#    return (str(dta_ret));

class Sensor:
    getdata_cb = None;
    senddata_cb = None;
    arg_cb = ""
    ret_cb = ""
    name = ""
    mqtt_topic = "/misc"
    errbuf = []
    dbgbuf = []
    
    def __init__(self, s_getdata_cb, s_mqtt_topic, s_name, arg_cb):
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
        ret = self.getdata_cb(self.arg_cb)
        self.ret_cb = ret;
        return (self.ret_cb);


    def call_datasend(self, opt=None):
        self.ret_cb = self.senddata_cb(self.arg_cb)
        return (self.ret_cb);

    def send_via_mqtt(self, mos):
        print("Sending");
        return (0);


    def __str__(self):
        strbuf=" | %s@%s | " % (self.name, self.mqtt_topic)
        if self.ret_cb ==  None:
            strbuf+=self.ret_cb+" | ";


        return (strbuf)

    def dprint(self, msg):
        msgbuf = ("==> %s | " %(msg));
        self.dbgbuf.append(msgbuf);
        print msgbuf;
        return (msgbuf);


class SensorSet:
    
    ss_list = {}
    ss_cb_get_data = {}
    ss_cb_send_data = {}
    ss_cnt  = 0
    DEBUG  = False

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
            print("Calling %s %s" % (str(sens), self.ss_list[sens].name) ) 
            self.ss_list[sens].call_dataget(None);
            #str(self.ss_list[sens])
            sens = self.ss_list[sens];
            #sens.call_dataget(None);
            #sens.call_dataget(None);
            
    def send_data(self):
        for sens in self.ss_list.keys():
            print("Calling %s %s" % (str(sens), self.ss_list[sens].name) ) 
            self.ss_list[sens].call_datasend(None);
            #str(self.ss_list[sens])
            sens = self.ss_list[sens];



    def get_datas(self):
        for fsen in self.ss_list.keys():
            cb_a = self.ss_list[fsen].arg_cb;
            cb_a = self.ss_list[fsen].arg_cb;
            ret_cb = self.ss_list[fsen].ret_cb;

            ret_cb = self.ss_list[fsen].getdata_cb(cb_a);
            

def send_data(mqttconn, sns):
    '''
        Send obtained data via MQTT
    '''
    dprinter = pprint.PrettyPrinter(indent=8, depth=4);

    dprinter.pprint(mqttconn)
    sens_lst = sns.ss_list
    for s in sens_lst.keys():
        topic = sens_lst[s].mqtt_topic
        msg = sens_lst[s].ret_cb
        print("\t=> %s is sending to \"%s\" values:" %(s, topic))
        print("\t==> %s" %(msg))

        mqttconn.publish(topic, msg);

        
    return (0);


    try:
        t_board = get_data("t_board");
    except Exception as e:
        dprint("===> !!! couldn't get temperature of the board:  %s" %(e));
    else:
        #print("==> Sending temperature")
        mqtt_bcast(mqttconn, "/environment/temperature/board", t_board);


    try:
        v_hum = get_data("hum");
    except Exception as e:
        print("===> !!! couldn't get humidity of the board: %s" %(e));
    else:
        #print("==> Sending humidity")
        mqtt_bcast(mqttconn, "/environment/humidity/board", v_hum);

    try:
        v_light = get_data("light");
    except Exception as e:
        print("===> !!! couldn't obtain light value: %s" %(e));
    else:
        #print("==> Sending light")
        mqtt_bcast(mqttconn, "/environment/light/general", v_light);

    return 0;

#
############################################################################
# main
###
#
def main():
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

    
    ar_mqtt.MQTT_init("172.17.17.9");
    ar_mqtt.MQTT_polling();
    '''
    | - connection loop
    '''


# NOT REACHED

if __name__ == "__main__":
    main()



def usage():
    print("usage: mqttc -vh");
    sys.exit(64);
