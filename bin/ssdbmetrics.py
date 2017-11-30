#!/usr/bin/env python

import threading
import ssdb
import json
import time
from datetime import datetime
import requests
import re
from itertools import izip_longest

def info_parser(lst):
    res = dict(izip_longest(*[iter(lst[1:])] * 2, fillvalue=None))
    binlogs = re.split(r"[\W\n:]+", res['binlogs'].strip())
    res['binlogs'] = dict(zip(binlogs[::2], binlogs[1::2]))
    data_key_range = re.split(r" *[\n:] +", res['data_key_range'].strip())
    res['data_key_range'] = dict(zip(data_key_range[::2], data_key_range[1::2]))
    serv_key_range = re.split(r" *[\n:] +", res['serv_key_range'].strip())
    res['serv_key_range'] = dict(zip(serv_key_range[::2], serv_key_range[1::2]))
    leveldb_stats = res['leveldb.stats'].strip().split('\n')
    stats_list = []
    for line in leveldb_stats:
        if line.find('Compactions') == -1 and line.find('Level') == -1 and line.find('------') == -1:
            stats = line.strip().split()
            stats_dict = dict()
            stats_dict["level"] = int(stats[0])
            stats_dict["files"] = int(stats[1])
            # Convert MB to byte
            stats_dict["size"] = int(stats[2]) * 1024 * 1024
            stats_dict["time"] = int(stats[3])
            stats_dict["read"] = int(stats[4]) * 1024 * 1024
            stats_dict["write"] = int(stats[5]) * 1024 * 1024
            if int(stats[0]) == len(stats_list):
                stats_list.append(stats_dict)
    res['leveldb.stats'] = stats_list
    res['name'] = lst[0]
    return res


class SSDBMetrics(threading.Thread):
    def __init__(self, falcon_conf, ssdb_conf):
        self.falcon_conf = falcon_conf
        self.ssdb_conf = ssdb_conf
        # Assign default conf
        if 'test_run' not in self.falcon_conf:
            self.falcon_conf['test_run'] = False
        if 'step' not in self.falcon_conf:
            self.falcon_conf['step'] = 60

        self.gauge_keywords = ['links', 'dbsize']
        self.counter_keywords = ['total_calls']
        self.level_db_keywords = ['files', 'size']

        super(SSDBMetrics, self).__init__(None, name=self.ssdb_conf['endpoint'])
        self.setDaemon(False)

    def new_metric(self, metric, value, type = 'GAUGE'):
        return {
            'counterType': type,
            'metric': metric,
            'endpoint': self.ssdb_conf['endpoint'],
            'timestamp': self.timestamp,
            'step': self.falcon_conf['step'],
            'tags': self.ssdb_conf['tags'],
            'value': value
        }

    def run(self):
        try:
            self.ssdb = ssdb.SSDB(host = self.ssdb_conf['host'], port = self.ssdb_conf['port'])
            self.ssdb.execute_command("auth", self.ssdb_conf['password'])
            self.ssdb.set_response_callback('info', info_parser)
            falcon_metrics = []
            # Statistics
            self.timestamp = int(time.time())
            ssdb_info = self.ssdb.execute_command("info")
            # Original metrics
            for keyword in self.gauge_keywords:
                falcon_metric = self.new_metric("ssdb." + keyword, int(ssdb_info[keyword]))
                falcon_metrics.append(falcon_metric)
            for keyword in self.counter_keywords:
                falcon_metric = self.new_metric("ssdb." + keyword, int(ssdb_info[keyword]), type='COUNTER')
                falcon_metrics.append(falcon_metric)
            for level_stat in ssdb_info["leveldb.stats"]:
                for keyword in self.level_db_keywords:
                    falcon_metric = self.new_metric("ssdb.level_%d_%s" % (level_stat['level'], keyword), level_stat[keyword])
                    falcon_metrics.append(falcon_metric)
            if self.falcon_conf['test_run']:
                print json.dumps(falcon_metrics)
            else:
                req = requests.post(self.falcon_conf['push_url'], data=json.dumps(falcon_metrics))
                print datetime.now(), "INFO: [%s]" % self.ssdb_conf['endpoint'], "[%s]" % self.falcon_conf['push_url'], req.text
        except Exception as e:
            if self.falcon_conf['test_run']:
                raise
            else:
                print datetime.now(), "ERROR: [%s]" % self.ssdb_conf['endpoint'], e
