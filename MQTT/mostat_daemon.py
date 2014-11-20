#!/usr/bin/env python3

import os,sys,time
#import datetime
import grp
import signal
import trace

import glob
import traceback

import string
import syslog
import getopt


import mosquitto
import sqlite3
import curses


from socket import gethostname;
from datetime import date,datetime;
    

#from smap import do_main_program

MyIO=None
DBH=None
ACC=None
W=None

def sig_handler(signum, fname):
    print('Signal handler called with %d' %( signum));

class APPIO:
    DEBUG=False
    VERBOSE=False
    DoDaemon=False
    appname=""

    def __init__(self, verbose=False, debug=False):
        self.DEBUG = debug;
        self.VERBOSE = verbose;
        self.appname = "MQTTstatd"
        self.logdebug("Opening connection to syslog");
        syslog.openlog(self.appname, syslog.LOG_PERROR, syslog.LOG_LOCAL0);

    def __del__(self):
        self.logdebug("Closing connection to syslog");
        #syslog.closelog();
        try:
            os.unlink(self.pidfile)
        except Exception:
            pass

    def setup_debug(self, level):
        global sig_handler
        self.DEBUG=True
        self.VERBOSE=True
        signal.signal(signal.SIGINT, sig_handler);
        self.logdebug("ACTIVADO DEBUGGING MODE")

    def logmsg(self, msg):
        syslog.syslog(syslog.LOG_INFO, msg); 
        return 0

    def logdebug(self, msg):
        if self.DEBUG:
            syslog.syslog(syslog.LOG_DEBUG, msg); 
            sys.stderr.write("!-> %s \n" %(msg));
        return 0

    def pidfile(self):
        pid = str(os.getpid())
        self.pidfile = "/var/run/mqttstat/%s.pid" %(self.appname)

        if os.path.isfile(self.pidfile):
            self.logmsg("%s already exists, exiting" % self.pidfile)
            sys.exit()
        else:
            try: 
                open(self.pidfile, 'w').write(pid)
            except Exception as e:
                self.logmsg("Couldn't create pidfile %s" % self.pidfile)
                raise(ExceptionAPPIO(400, e))



        


class ExceptionAPPIO(Exception):
    ExStr = {
            201: "Consistency problem", \
            202: "DB access problem", \
            203: "DB connection problem", \
            204: "Data conversion problem", \
            400: "Problem with permissions", \
            300: "Extra data" \
        }
    def __init__(self, code, msg=""):
        self.code = code;
        self.msg = msg
    def __str__(self):
        return repr(self.ExStr[self.code])

class DBHandler:
    db_path=None
    conn_h=None
    
    def __init__(self, dbp="mqtt.db"):
        self.db_path = dbp;

    def db_ex_query(self, query):
        """
        |
        """
        c = self.conn_h.cursor();
        try:
            c.execute(query);
        except Exception as e:
            MyIO.logmsg("DBHandler() Exception %s"%(str(e)));
            raise(ExceptionAPPIO(203, str(e)))

        try:
            self.conn_h.commit();
        except Exception as e:
            raise(ExceptionAPPIO(203, str(e)))
            
        return 0

    def db_connect(self):
        try:
            conn = sqlite3.connect(self.db_path)
        except Exception as e:
            raise(ExceptionAPPIO(203, str(e)))
            return (-1);
        self.conn_h = conn;
        return (self.conn_h)

    def db_init(self):
        MyIO.logmsg("Opening sqlite3 database %s" %(self.db_path))
	#syslog.syslog(syslog.LOG_INFO, "Opening sqlite3 database %s" %(self.db_path)); 
        self.db_connect()
	# XXX c = self.conn_h.cursor();
        self.db_ex_query('''CREATE TABLE IF NOT EXISTS temperature (date INTEGER, desc TEXT, tval REAL)''');
        self.db_ex_query('''CREATE TABLE IF NOT EXISTS misc (date INTEGER, desc TEXT, tval REAL)''');
        self.db_ex_query('''CREATE TABLE IF NOT EXISTS light (date INTEGER, desc TEXT, tval INTEGER)''');
        self.db_ex_query('''CREATE TABLE IF NOT EXISTS humidity (date INTEGER, desc TEXT, humidity INTEGER)''');
	#conn.commit();
        return (self.conn_h);
    
    def __del__(self):
        # """
        if self.conn_h != None:
            self.conn_h.close(); # SQlite3 *

# XXX TODO
#
#def update_temperature(connhnd, tname, tstr):
#	"""
#	"""
#	try:
#	    temp = float(tstr);
#	except Exception as e:
#	    MyIO.logmsg("==> Type conversion failure during DB update:\t%s" %(e));
#	    MyIO.logmsg("==> \"%s\" "  %(tstr));
#	    return (-1);
#        else:
#	curtime = int(time.time());
#	c = connhnd.cursor();
#	c.execute("INSERT INTO temperature VALUES (%d, '%s', '%2.2f')" % (curtime, tname, temp));
#	connhnd.commit();


class Accounting:
    totalmsg = 0;
    pertopic = {}
    rbytes = 0;
    sbytes = 0;

    def __init__(self):
        self.totalmsg = 0;
        self.pertopic = {};
        self.last_message = time.time()

    def new_msg(self, topic):
        self.totalmsg+=1
        self.last_message = time.time();
        if topic not in self.pertopic:
            self.pertopic[topic] = 0
        else:
            self.pertopic[topic]+=1;
        return (self.totalmsg);

    def __str__(self):
        ct = time.time()
        cur_dt = datetime.fromtimestamp(ct)
        cDTfm = cur_dt.strftime("%T")           
        DT = datetime.fromtimestamp(self.last_message)
        DTf = DT.strftime("%T")
        
        timepas = ct-self.last_message;     # time offset below
        acline = []
        acline.append("Messages: last %s/cur %s,\t\t\tPassed %ds" %(cDTfm, DT, int(timepas)));
        acline.append("Total msg counter=%d\trb %d/sb %d" %(self.totalmsg, self.rbytes,self.sbytes));
        separator=" ";
        return (separator.join(acline))


#from APPIO import MyIO.logmsg, MyIO.logdebug;

def on_subscribe(mosq, obj, b, mid):
        MyIO.logmsg("Subscribe with mid "+str(mid)+" received.")

def on_connect(mosq, obj, rc):
    if rc == 0:
        MyIO.logmsg("Connected successfully.")


# XXX to remove
#def init_sqlite3_db(dbpath='mqtt.db'):
#    """
#    XXX - possibly to remove 
#    """
#    MyIO.logmsg("Opening sqlite3 database %s" %(dbpath))
#    syslog.syslog(syslog.LOG_INFO, "Opening sqlite3 database %s" %(dbpath)); 
#    conn = sqlite3.connect(dbpath)
#    c = conn.cursor();
#    c.execute('''CREATE TABLE IF NOT EXISTS temperature
#                (date integer, desc text, tval real)''');
#    c.execute('''CREATE TABLE IF NOT EXISTS misc
#                (date integer, desc text, tval real)''');
#    c.execute('''CREATE TABLE IF NOT EXISTS light
#                (date integer, desc text, tval integer)''');
#    c.execute('''CREATE TABLE IF NOT EXISTS humidity
#                (date integer, desc text, humidity integer)''');
#    conn.commit();
#    return (conn);


def update_temperature(DBH_p, tname, tstr):
    """
    """
    ret = False;
    try:
        temp = float(tstr);
    except Exception as e:
        raise(ExceptionAPPIO(204, "float(\"%s\"): %s"%(tstr,str(e)) ));
    else:
        curtime = int(time.time());
        DBH_p.db_ex_query("INSERT INTO temperature VALUES (%d, '%s', '%f')" % (curtime, tname, temp));
        ret=True;
    return (ret);

def update_light(DBH_p, lstr, lname="general"):
    try:
        light = int(lstr);
    except Exception as e:
        MyIO.logmsg("Type conversion failure@update_light() : %s"%(e));
        raise(ExceptionAPPIO(204, str(e)));
    curtime = int(time.time());
    DBH_p.db_ex_query("INSERT INTO light VALUES (%d, '%s', '%d')" % (curtime, lname, light));
    return (0);

def update_humidity(DBH_p, hname, hstr):
    try:
        humidity = int(hstr);
    except Exception as e:
        MyIO.logmsg("conversion failure@update_humidity() : %s"%(e));
        return (0);
    curtime = int(time.time());
    DBH_p.db_ex_query("INSERT INTO humidity VALUES (%d, '%s', '%d')" % (curtime, hname, humidity));
    return (0);


def on_message(mosq, obj, msg):
    global DBH, W, ACC, MyIO;

    val = str(msg.payload)[2:-1]
    topic = msg.topic;
    ACC.new_msg(topic)

    #if topic == "$SYS/broker/bytes/received":
    #    brecv = float(val);
    #elif topic == "$SYS/broker/bytes/sent":
    #    bsent = float(val);
    if topic == "/environment/temperature/board":
        try:
            update_temperature(DBH, "board", val);
        except ExceptionAPPIO as e:
            MyIO.logdebug("Failed to update_temperature() %s. temerature=%s" %(topic, val))
        else:
            MyIO.logdebug("Message update_temperature() on %s. temerature=%s" %(topic, val))
    elif topic == "/environment/humidity/board":
        try:
            update_humidity(DBH, "board", val);
        except ExceptionAPPIO as e:
            MyIO.logdebug("ERROR: update_humidity() %s on %s. humidity=%s" %(topic, val))
        else:
            MyIO.logdebug("Message update_humidity() on %s. humidity=%s" %(topic, val))
    elif topic == "/environment/light/general":
        try:
            update_light(DBH, val);
        except ExceptionAPPIO as e:
            MyIO.logdebug("ERROR update_light() %s on light=%s" %(topic, val))
        else:
            MyIO.logdebug("Message %s on light=%s" %(topic, val))
    else:
        MyIO.logmsg("Unknown message on topic=\"topic\"("+str(msg.qos)+") - "+val)
        raise(ExceptionAPPIO(300, val+" "+topic))
    return 0;

def mqtt_init(srvaddr="172.17.17.9", tmout=-1):
    """
        Initialisation of MQTT connection



    """
    name=gethostname();
    mos = mosquitto.Mosquitto("mqttc_%s" % (name))
    mos.username_pw_set("mosq", "dziki");
    mos.on_connect = on_connect;
    mos.on_message = on_message;
    #mos.on_subscribe = on_subscribe;
    try:
        MyIO.logmsg("Connecting to %s" %(srvaddr));
        mos.connect(srvaddr);
    except Exception as e:
        MyIO.logmsg("Failed to connect to %s" % (srvaddr));
        raise(ExceptionAPPIO(203, str(e)))
    MyIO.logmsg("Connected to broker");
    mos.loop(timeout=tmout)
    mos.publish("/system/status", "GRAPH_ON", 1)
    return (mos);

def mqtt_sub(mos, topic):
    mos.subscribe(topic, 0);

def mqtt_sub_all(mos):
    """
        Subscribing to topics
    """
    #mos.subscribe("$SYS/broker/load/connections/5min", 0);
    #mos.subscribe("$SYS/broker/bytes/received", 0);
    #mos.subscribe("$SYS/broker/bytes/sent", 0);
    #mos.subscribe("$SYS/broker/heap/current", 0);
    mqtt_sub(mos, "/environment/temperature/#");
    mqtt_sub(mos, "/environment/light/#");
    mqtt_sub(mos, "/environment/humidity/#");


def mqtt_recvloop(mos, tm=2):
    global ACC, MyIO;
    mos.on_message = on_message;
    DOLOOP = True;
    n=1000;
    while DOLOOP:
        mos.on_message = on_message;
        try:
            mos.loop(timeout=tm);
        except KeyboardInterrupt:
            MyIO.logmsg("!> Interrupted via keyboard in mqtt_recvloop()");
            DOLOOP=False
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            MyIO.logmsg("Error occured: %s" %(str(e)));
            DOLOOP=False
        else:
            if MyIO.DEBUG and n <= 0:
                n = 1000;
                print(ACC);
        n-=1;
    MyIO.logmsg("!> Disconnected with broker");
    mos.disconnect();



def main():
    global DBH, ACC, MyIO;

    DBH = DBHandler("./mqtt.db");

    MyIO.VERBOSE=False
    MyIO.DEBUG=False
    MyIO.pidfile();

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:vdD", ["help", "db path=", "db=", "verbose", "debug", "daemon"])
    except getopt.GetoptError as err:
        #print str(err) # will print something like "option -a not recognized"
        print("usage: %s -d -v -D -p [dbpath]" %(sys.argv[0])) 
        sys.exit(64)
    # Some opts which we need to accomplish getopt
    for o, a in opts:
        if o == "-v":
            MyIO.VERBOSE = True
        elif o == "-D":
            MyIO.DoDaemon = True;
        elif o == "-d":
            MyIO.DEBUG = True
        elif o in ("-h", "--help"):
            print("usage: %s -dv -D" %(sys.argv[0])) 
            sys.exit()
        elif o in ("-p", "--db-path"):
            DBH.db_path = a;
        else:
            assert False, "unhandled option"

    if MyIO.DEBUG:
        MyIO.setup_debug("DEBUG")
    
    DBH.db_init();
    #DBH = init_sqlite3_db("mqtt.db");
    mos = mqtt_init('172.17.17.9', 2);
    mqtt_sub_all(mos);
    mqtt_recvloop(mos);
    #DBH.close(); # SQlite3 *
    del MyIO
    return 0


###################
# Main
##
MyIO = APPIO()
ACC = Accounting()
main()
