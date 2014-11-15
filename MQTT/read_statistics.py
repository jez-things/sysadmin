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


class ProbeFault(Exception):
    em = {201: "Database connection problem", \
          102: "Programming error", \
          103: "Incorrect data given", \
          104: "Incorrect data received", \
          202: "Database data corrupted" }

class ProbeIOerror(ProbeFault):
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

def epoch2str(estr, fmt=None):
    return (ProbeDateTime(int(estr), fmt))
    #return (rstr)


class SimpleProbe:
    sp_pdata = 0.00; # Data 
    sp_timdat = None # Class for expressing date and time
    sp_cnt = 0;      # counter

    def __init__(self, pdata, epocht):
        self.sp_timdat = ProbeDateTime(epocht);
        self.sp_pdata = pdata;
        self.sp_cnt+=1;

    def __str__(self):
        retstr = "%d) %f %s" %(self.sp_cnt, self.sp_pdata, self.sp_timdat);
        return (retstr)


class ProbeSet:
    ps_type = ""
    ps_sensorset = {};
    ps_cur_sensor = "";
    ps_sensor_names = [];

    def __init__(self, ptype, snames):
        self.ps_ptype = ptype;
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
        datas = self.ps_sensorset[self.ps_type][sname].append(sdata);
        self.ps_cnt += 1;
        return (datas);

    
    
class TempSensor(ProbeSet):
    TS_lastrec = None
    TS_sensors = None;
    TS_cnt = 0;

    def __init__(self):
        self.TS_lastrec = None;
        self.TS_sensors = ProbeSet("TEMPERATURE", "board", "outside");
        self.TS_cnt = 0;
        self.TS_db_rows = 0;

    def add_probe(self, temp, epocht, s_name):
        """
            Add entry
            returns probe
        """
        Tsensor = self.TS_sensors.add_sensor(s_name, SimpleProbe(temp, epocht));
        self.TS_cnt+=1
        return (Tsensor);

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

    def __init__(self, sensor):
        self.LP_sensors = ProbeSet("LIGHT", ['generic']);


    def add_probe(self, temp, epocht, s_name):
        """
            Add entry
            returns probe
        """
        Tsensor = self.TS_sensors.add_sensor(s_name, SimpleProbe(temp, epocht));
        self.TS_cnt+=1
        return (Tsensor);

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



class TempProbe(SimpleProbe):
    """
        class for temperature probes
    """
    tp_cnt = 0;
    tp_sensors = {};
    tp_cur_sensor = "board"
    tp_id = 0;
    
    def __init__(self, sensor):
        self.tp_sensors[sensor] = [];
        self.tp_cnt = 0;
        self.tp_cur_sensor = "board";
        self.iter_index = 0;
        
    def __iter__(self):
        self.iter_index = self.tp_cnt;
        return self

    def next(self):
        if self.iter_index == 0:
            raise StopIteration
        self.iter_index = self.iter_index - 1
        return (self.tp_sensors[self.tp_cur_sensor][self.iter_index])

    def add_probe(self, temp, epocht, sensor):
        """
            Add entry
        """
        prob = SimpleProbe(temp, epocht)
        self.tp_cnt+=1
        self.tp_id=self.tp_cnt;
        self.tp_sensors[sensor].append(prob)
        return (prob);

    def proc_db(self, row):
        """
            Function to process DB entries to internal structures
        """
        temp = 0.0;
        epocht = 0;
        sensor = "";
        ret = None;
        if (len(row) == 3):
            temp = float(row[2]);
            sensor = row[1];
            epocht = int(row[0]);
            if sensor != "board" and sensor != "outside":
                print("!!!> Unknown entry: %s" %(row));
                raise ProbeFault(103);
            ret = self.add_probe(temp, epocht, sensor);
        else:
            print("!!!> Incorrect database schema! Expected 3 entries found %d" %(len(row)));
            raise ProbeFault(103);
        return(ret);

        

#class HumidityProbe(SimpleProbe):




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

    temp_probes = [TempProbe('board'), TempProbe('outside'), TempProbe('bed')]
    # First read one dataset
    t_board = temp_probes[0];
    try:
        for row in c.execute('''SELECT * from temperature WHERE sondname="board" '''):
            t_board.proc_db(row);
    except Exception as e:
        print("!> Failed to fetch rows from db:%s" % (e));

    
    # Now we read data from photoresistor
    ####################
    light_probes = [LightProbe('general')]
    l_general = light_probes[0]
    try:
        for row in c.execute('''SELECT * from light WHERE desc="general" '''):
            l_general.proc_db(row);
    except Exception as e:
        print("!> Failed to fetch rows from db:%s" % (e));

    return (conn)

##############################################################
# main
###



DBH = read_db('./mqtt.db');
DBH.close();


