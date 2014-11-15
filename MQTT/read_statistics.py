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

class ProbeDateTime:
    dattim = None;
    epoch = 0;
    dattim_str = ""
    dattim_fmt = '%H:%M:%S  %d-%b-%Y(%Z)'
    pass

def epoch2str(estr, fmt=None):
    e2str = ProbeDateTime()
    e2str.dattim = time.localtime(int(estr))
    e2str.epoch = int(estr)
    if fmt == None:
        fmt = e2str.dattim_fmt;
    rstr = e2str.dattim_str = time.strftime(fmt, e2str.dattim);
    return (rstr)


class SimpleProbe:
    sp_pdata = 0.00;
    sp_epocht = 0;
    sp_timdat_str = ""
    sp_timdat_fmt = '%H:%M:%S %d-%m-%Y'
    sp_cnt = 0;

    def __init__(self, pdata, epocht):
        self.sp_pdata = pdata;
        self.sp_epocht = epocht;
        self.sp_timdat_str = epoch2str(ftm);
        self.sp_cnt+=1;

    def __str__(self):
        retstr = "%f %s" %(self.sp_pdata, self.sp_timdat_str);
        return (retstr)


class LightProbe(SimpleProbe):
    lp_sensors = {};
    lp_cur_pos = "";
    lp_cnt = 0;

    def __init__(self, pos):
        self.lp_cur_pos = pos;
        self.lp_sensors = {};

    def add(self, pos, val, epocht):
        dset = self.sensors[pos];
        dset.append(SimpleProbe(


class TempProbe(SimpleProbe):
    """
        class for temperature probes
    """
    tp_cnt = 0;
    tp_thermometrs = {};
    tp_cur_pos = "board"
    tp_id = 0;
    
    def __init__(self, pos):
        self.tp_thermometrs[pos] = [];
        self.tp_cnt = 0;
        self.tp_cur_pos = "board";
        self.iter_index = 0;
        
    def __iter__(self):
        self.iter_index = self.tp_cnt;
        return self

    def next(self):
        if self.iter_index == 0:
            raise StopIteration
        self.iter_index = self.iter_index - 1
        return (self.tp_thermometrs[self.tp_cur_pos][self.iter_index])

    def add_probe(self, temp, ftm, pos):
        prob = SimpleProbe(temp, ftm)
        self.tp_cnt+=1
        self.tp_id=self.tp_cnt;
        self.tp_thermometrs[pos].append(prob)
        return (prob);

    def proc_db(self, row):
        temp = 0.0;
        epocht = 0;
        pos = "";
        ret = None;
        if (len(row) == 3):
            temp = float(row[2]);
            pos = row[1];
            epocht = int(row[0]);
            if pos != "board" and pos != "outside":
                print("!!!> Unknown entry: %s" %(row));
            ret = self.add_probe(temp, epocht, pos);
        else:
            print("!!!> Incorrect database schema! Expected 3 entries found %d" %(len(row)));
        return(ret);

        

class Temperature(TempProbe):
    t_sensors = {};
    t_sens_cnt = 0;



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
            try:
                t_board.proc_db(row);
            except Exception as e:
                print("!> Failed to process entry %s" %(str(row)));

            if (len(row) > 2):
                ntmp = float(row[2]);
                pos = row[1];
                etim = int(row[0]);
                if pos == "board":
                    t_board.add_probe(ntmp, etim, "board");
                elif pos == "outside":
                    t_board.add_probe(ntmp, etim, "outside");
                else:
                    print("!!!> Unknown entry: %s" %(row));
    except Exception as e:
        print("!> Failed to fetch rows from db:%s" % (e));


    # Now we read data from photoresistor
    try:
        for row in c.execute('''SELECT * from light WHERE desc="general" '''):
            if (len(row) > 2):
                ntmp = float(row[2]);
                pos = row[1];
                etim = int(row[0]);
                if pos == "general":
                    t_board.add_probe(ntmp, etim, "board");
                elif pos == "outside":
                    t_board.add_probe(ntmp, etim, "outside");
                else:
                    print("!!!> Unknown entry: %s" %(row));

    for tb in t_board.tp_thermometrs['board']:
        print tb;
    print("=> %d probes" %(t_board.tp_cnt));


    return (conn)

##############################################################
# main
###



DBH = read_db('./mqtt.db');
DBH.close();


