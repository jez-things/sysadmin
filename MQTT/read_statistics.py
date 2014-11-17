#!/usr/bin/env /usr/bin/python2.7
import os,sys,time
import grp
import signal

import string
import getopt
import glob
import random
import sqlite3
import datetime

import rrdtool

class GrapherFault(Exception):
    em = {301: "Incorrect programmer's input", \
          302: "Problem with RRD database" }

class ProbeFault(Exception):
    em = {201: "Database connection problem", \
          102: "Programming error", \
          103: "Incorrect data given", \
          104: "Incorrect data received", \
          202: "Database data corrupted" }

class ProbeError(ProbeFault):
    pass

class ProbeWarning(ProbeFault):
    pass


class ProbeDateTime:
    timdat = None;
    epoch = 0;
    timdat_str = ""
    timdat_fmt = '%H:%M:%S  %d-%b-%Y(%Z)'

    def __init__(self, epocht, fmt=None):
        self.epoch = epocht;
        self.timdat = time.localtime(epocht);
        if fmt == None:
            fmt = self.timdat_fmt;
        self.timdat_str = time.strftime(fmt, self.timdat);

    def __str__(self):
        return (self.timdat_str);

    def fprint(self, fmt):
        return (time.strftime(fmt, self.timdat));
        
    def reformat(self, fmt):
        self.timdat_fmt = fmt;
        self.timdat_str = time.strftime(fmt, self.timdat);
        return (self.timdat_str);

def epoch2str(estr, fmt=None):
    return (ProbeDateTime(int(estr), fmt))
    #return (rstr)


class SimpleProbe:
    sp_data = 0.00; # Data 
    sp_timdat = None # Class for expressing date and time
    sp_cnt = 0;      # counter

    def __init__(self, pdata, epocht):
        self.sp_timdat = ProbeDateTime(epocht);
        self.sp_data = pdata;
        self.sp_cnt+=1;

    def __str__(self):
        pr = self.sp_timdat.fprint('%H:%M %d-%b');
        retstr = "%.2f - %s" %(self.sp_data, pr);
        return (retstr)

    def toRRD(self):
        retstr = "%d:%.2f" % (self.sp_timdat.epoch, self.sp_data);
        return (retstr);


class ProbeMadre:
    DEBUG=False
    DEBUG_LEVEL=0
    VERBOSE=False

    def __init__(self, dbg, dbg_lvl, verbose):
        self.DEBUG=dbg;
        self.DEBUG_LEVEL=dbg_lvl;
        self_VERBOSE=verbose


    def dprint(self, msg):
        msgbuf="=> %s "%(msg)
        if self.DEBUG:
            print msgbuf
        return (msgbuf);


class ProbeSet(ProbeMadre):
    ps_type = ""
    ps_cnt = 0;
    ps_sensorset = {};
    ps_cur_sensor = "";
    ps_sensor_names = [];
    ps_DEBUG=False;
    

    def __init__(self, ptype, snames, debug=False):
        self.ps_type = ptype;
        self.index = 0;
        self.ps_cnt = 0;
        self.ps_DEBUG=debug;
        self.ps_sensor_names = snames;
        self.ps_sensorset[ptype] = {};
        for sn in snames:
            self.ps_sensorset[ptype][sn] = [];
            self.ps_cur_sensor = sn;

    def add_sensor(self, sname, sdata):
        """
        """
        datas = False
        # lookup name of the sensor
        hit = False
        for snam in self.ps_sensor_names:
            if sname == snam:
                hit = True
                break;
        if hit != True:
            raise(ProbeFault(104));
            return None;

        self.ps_cur_sensor = sname;
        try:
            datas = self.ps_sensorset[self.ps_type][sname].append(sdata);
        except Exception as e:
            print("!-> add_sensor() failure for \"%s\"" %(self.ps_type));
            return (None);
        self.dprint("add_sensor(self, %s, [%s])" %(sname, sdata))
        self.ps_cnt += 1;
        return (datas);
    
    def dprint(self, msg):
        '''
            Debugging output
        '''
        toprint = "%d) %s ~> %s" %(self.ps_cnt, self.ps_type, msg)
        if self.ps_DEBUG == True:
            print(toprint)
        return (toprint);


class HumiditySensor(ProbeSet):
    HS_sensors = None;
    HS_cnt = 0;
    HS_db_rows = 0;
    HS_DEBUG = False;

    def __init__(self, sensor_lst, Hdebug=False):
        self.HS_sensors = ProbeSet("HUMIDITY", sensor_lst, debug=Hdebug);
        self.HS_cnt = 0;
        self.HS_DEBUG = Hdebug;

    def add_probe(self, hum, epocht, s_name):
        """
            Add entry
            returns probe
        """
        sp = SimpleProbe(hum, epocht)
        self.HS_sensors.add_sensor(s_name, sp);
        self.HS_sensors.dprint("Adding probe %s:%f %s" %(s_name, hum, sp.sp_timdat))
        self.HS_cnt+=1
        return (sp);


    def proc_db_row(self, row):
        """
            Function to process DB entries to internal structures
        """
        hum = 0; epocht = 0; sensor = ""; probe = None;
        self.HS_db_rows+=1;
        if (len(row) == 3):
            hum = float(row[2]);
            sensor = row[1];
            epocht = int(row[0]);
            probe = self.add_probe(hum, epocht, sensor);
        else:
            print("!!!> Incorrect database schema! Expected 3 entries found %d" %(len(row)));
            raise ProbeFault(103);
        return(probe);


    
class TempSensor(ProbeSet):
    TS_lastrec = None
    TS_sensors = None;
    TS_cnt = 0;
    TS_DEBUG = False;
    
    def __init__(self, sensor_lst, debug=False):
        self.TS_lastrec = None;
        self.TS_DEBUG = debug;
        self.TS_sensors = ProbeSet("TEMPERATURE", sensor_lst, debug=False);
        self.TS_cnt = 0;
        self.TS_db_rows = 0;

    def add_probe(self, temp, epocht, s_name):
        """
            Add entry
            returns probe
        """
        sp = SimpleProbe(temp, epocht)
        self.TS_sensors.add_sensor(s_name, sp);
        self.TS_cnt+=1
        self.TS_sensors.dprint("Adding probe: \"%s\" [%s]" %(s_name, sp))
        return (sp);

    def proc_db_row(self, row):
        """
            Function to process DB entries to internal structures
        """
        temp = 0.0; epocht = 0; sensor = ""; probe = None;
        self.TS_db_rows+=1;
        if (len(row) == 3):
            temp = float(row[2]);
            sensor = row[1];
            epocht = int(row[0]);
            probe = self.add_probe(temp, epocht, sensor);
        else:
            print("!!!> Incorrect database schema! Expected 3 entries found %d" %(len(row)));
            raise ProbeFault(103);
        return(probe);



class LightSensor(ProbeSet):
    LP_sensors = None;
    LP_cnt = 0;
    LP_db_rows=0;
    LP_DEBUG=False;

    def __init__(self, sensor_lst):
        self.LP_sensors = ProbeSet("LIGHT", sensor_lst, debug=False);
        self.LP_cnt = 0;
        self.LP_db_rows=0;
        #self.LP_DEBUG=debug;

    def add_probe(self, light, epocht, s_name):
        """
            Add entry
            returns probe
        """

        Lsensor = self.LP_sensors.add_sensor(s_name, SimpleProbe(light, epocht));
        self.LP_cnt+=1
        return (Lsensor);

    def proc_db_row(self, row):
        """
            Function to process DB entries to internal structures
        """
        probe = None;
        self.LP_db_rows+=1;
        if (len(row) == 3):
            light = float(row[2]);
            sensor = row[1];
            epocht = int(row[0]);

            if self.LP_DEBUG == True:
                print("%d) -> adding Lprobe ('%s', %d, %d)" %(self.LP_cnt, sensor, int(row[2]),epocht))
            probe = self.add_probe(light, epocht, sensor);
        else:
            print("!!!> Incorrect database schema! Expected 3 entries found %d" %(len(row)));
            raise ProbeFault(103);
        return(probe);

#################
#
##
from distutils.util import strtobool
def AskUser(question):
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

def ProbeRRD_Create_temp(g_path, rrddef=None, rrdrra=None):
    DS_str = '''DS:mtemp:GAUGE:600:U:50'''
    RRA_avg_str = '''RRA:AVERAGE:0.5:1:24'''
    RRA_max_str = '''RRA:MAX:0.5:1:228'''
    rrdh = rrdtool.create(g_path, '--start', 'now-1d', '--step','60', DS_str, RRA_avg_str, RRA_max_str);
    return (rrdh);

def ProbeRRD_Create_light(g_path, rrddef=None, rrdrra=None):
    DS_str = '''DS:light:GAUGE:600:U:50'''
    RRA_avg_str = '''RRA:AVERAGE:0.5:1:24'''
    RRA_max_str = '''RRA:MAX:0.5:1:228'''
    rrdh = rrdtool.create(g_path, '--start', 'now-10800s', '--step','60', DS_str, RRA_avg_str, RRA_max_str);
    return (rrdh);

def ProbeRRD_Create_hum(g_path, rrddef=None, rrdrra=None):
    DS_str = '''DS:hum:GAUGE:600:U:50'''
    RRA_avg_str = '''RRA:AVERAGE:0.5:1:24'''
    RRA_max_str = '''RRA:MAX:0.5:1:228'''
    rrdh = rrdtool.create(g_path, '--start', 'now-1d', '--step','60', DS_str, RRA_avg_str, RRA_max_str);
    return (rrdh);

def ProbeRRD_Update(g_path, SP):
    ret = None;
    errbuf = []
    cnt = 0;

    try:
        ret = rrdtool.update(g_path, str(SP.toRRD()));
    except Exception as e:
        errbuf.append("rrdtool.update(%s) failed to update %s: %s | %s\n" %(g_path, SP, e, str(e)));
        if cnt > 3:
            print("=>Done with %d errors" %(len(errbuf)))
            errlog = open("errlog", "w+")
            print("==> Writing %d lines to \"errorlog\"" %(cnt));
            for ln in errbuf:
                errlog.write(ln);
            errlog.close();
    finally:
        cnt+=1;
    return (ret);

def ProbeRRD_Graph_temp(f_name):
    DEF='''DEF:mytemp=temperature.rrd:mtemp:AVERAGE'''
    LINE2='''LINE2:mytemp#FF0000'''
    graph_f=(f_name[:-3]+"png");
    ret = None;
    try:
        ret = rrdtool.graph(graph_f, '--start', 'now-4h', '--step','60', '--width', '600', '--height', '300', '--title', 'Weather - Temperature', '--vertical-label', 'C', '--color=BACK#CCCCCC', '--color=CANVAS#CCFFFF', "--color=SHADEB#9999CC", '--x-grid', 'SECOND:1:SECOND:4:SECOND:10:0:%X', DEF, LINE2);


    except Exception as e:
        print("=!> Failed to graph \"%s\":%s" %(graph_f, e));
        try:
            os.stat(f_name)
        except:
            pass;
        else:
            print("==> File \"%s\" still exists but rrdgraph failed!" %(f_name));
#    finally:
#        if AskUser("####> Found stale file \"%s\". Removing?"%(f_name)) == "y":
#            os.unlink(f_name);
    return(ret)

def ProbeRRD_Graph_light(f_name):
    '''
        plotting light
    '''
    DEF='''DEF:mylight=light.rrd:light:AVERAGE'''
    LINE2='''LINE2:mylight#FFF000'''

    graph_f=(f_name[:-3]+"png");
    ret = None;
    try:
        ret = rrdtool.graph(graph_f, '--start', 'now-10800s', '--step','300', '--width', '500', '--height', '300', '--title', 'Weather - light', DEF, LINE2);
    except Exception as e:
        print("=!> Failed to graph \"%s\":%s" %(graph_f, e));
        try:
            os.stat(f_name)
        except:
            pass;
        else:
            print("==> File \"%s\" still exists but rrdgraph failed!" %(f_name));
#    finally:
#        if AskUser("####> Found stale file \"%s\". Removing?"%(f_name)) == "y":
#            os.unlink(f_name);
    return(ret)

def ProbeRRD_Graph_humidity(f_name):

    DEF='''DEF:mytemp=temperature.rrd:mtemp:AVERAGE'''
    LINE2='''LINE2:mytemp#FF0000'''
    graph_f=(f_name[:-3]+"png");
    ret = None;
    try:
        ret = rrdtool.graph(graph_f, '--start', 'now-10800s', '--step','300', '--width', '500', '--height', '300', '--title', 'Weather', DEF, LINE2);
    except Exception as e:
        print("=!> Failed to graph \"%s\":%s" %(graph_f, e));
        try:
            os.stat(f_name)
        except:
            pass;
        else:
            print("==> File \"%s\" still exists but rrdgraph failed!" %(f_name));
#    finally:
#        if AskUser("####> Found stale file \"%s\". Removing?"%(f_name)) == "y":
#            os.unlink(f_name);
    return(ret)

def get_db_row(db_conn_h, t_name, db_cond):
    query = '''SELECT * from %s %s''' % (t_name, db_cond)
    row = [];
    try:
        row = db_conn_h.execute(query);
    except Exception as e:
        print("!> Failed to fetch rows from db:%s" % (e));
    return (row);






def read_db(dbpath):
    """
        Read DB entries and map them to internal structures
    """
    print("=> Connecting to sqlite3 DB \"%s\"" %(dbpath));
    try:
        conn = sqlite3.connect(dbpath);
        c = conn.cursor();
    except Exception as e:
        print("!!!> Failed to connect to DB");
        sys.exit(3);


    #-----------
    # Temperature
    #------------
    Tsensors = TempSensor(['board', 'outside']);
    # First read one dataset
    for row in get_db_row(c, "temperature", '''WHERE sondname="board"'''):
        Tsensors.proc_db_row(row);

    RRD_db = 'temperature.rrd'
    tgraph = ProbeRRD_Create_temp(RRD_db);
    for ts in Tsensors.TS_sensors.ps_sensorset['TEMPERATURE']['board']:
        ProbeRRD_Update(RRD_db, ts);

    ProbeRRD_Graph_temp(RRD_db);
        
    #print("rrdupdate temperature.rrd %s"%(str(ts.toRRD())))
    
    # Now we read data from photoresistor
    ####################

    #-------
    # Light
    #-------

    RRD_db = 'light.rrd';
    ProbeRRD_Create_light(RRD_db);

    Lsensors = LightSensor(["general"]);
    for row in get_db_row(c, "light", ''' WHERE desc="general"'''):
        Lsensors.proc_db_row(row);

    for ts in Lsensors.LP_sensors.ps_sensorset['LIGHT']['general']:
        #print("LIGHT) %s" %(str(ts)));
        ProbeRRD_Update(RRD_db, ts);

    ProbeRRD_Graph_light('light.rrd');

    #---------
    # Humidity
    #--------
    RRD_db = 'humidity.rrd';
    DEF='''DEF:myhum=humidity.rrd:hum:AVERAGE'''
    LINE2='''LINE2:myhum#FF0000'''
    ProbeRRD_Create_hum(RRD_db);
    Hsensors = HumiditySensor(["board"], Hdebug=False);
    for row in get_db_row(c, "humidity", ''' WHERE desc="board"'''):
        Hsensors.proc_db_row(row);

    probes_total=0
    for ts in Hsensors.HS_sensors.ps_sensorset['HUMIDITY']['board']:
        ProbeRRD_Update(RRD_db, ts);
        probes_total+=1;
        #print("HUMIDITY) %s" %(str(ts)));
    
    ProbeRRD_Graph_humidity('humidity.rrd');

    return (conn)

##############################################################
# main
###



DBH = read_db('./mqtt.db');
DBH.close();


