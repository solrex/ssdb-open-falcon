#!/usr/bin/env python

import threading
# Official version of ssdb-py does not support 'info' command.
# Please use https://github.com/solrex/ssdb-py
# Install: sudo python ./setup.py install
import ssdb
import json
import time
from datetime import datetime
import requests

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
        self.level_db_keywords = ['Files', 'Size(MB)']

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
            self.ssdb = ssdb.SSDB(host = self.ssdb_conf['host'], port = self.ssdb_conf['port'], password = self.ssdb_conf['password'])
            falcon_metrics = []
            # Statistics
            self.timestamp = int(time.time())
            ssdb_info = self.ssdb.info()
            # Original metrics
            for keyword in self.gauge_keywords:
                falcon_metric = self.new_metric("ssdb." + keyword, int(ssdb_info[keyword]))
                falcon_metrics.append(falcon_metric)
            for keyword in self.counter_keywords:
                falcon_metric = self.new_metric("ssdb." + keyword, int(ssdb_info[keyword]), type='COUNTER')
                falcon_metrics.append(falcon_metric)
            for level_stat in ssdb_info['leveldb']['stats']:
                for keyword in self.level_db_keywords:
                    falcon_metric = self.new_metric("ssdb.level_%d_%s" % (level_stat['Level'], keyword), level_stat[keyword])
                    falcon_metrics.append(falcon_metric)
            if self.falcon_conf['test_run']:
                print(json.dumps(falcon_metrics))
            else:
                req = requests.post(self.falcon_conf['push_url'], data=json.dumps(falcon_metrics))
                print(datetime.now(), "INFO: [%s]" % self.ssdb_conf['endpoint'], "[%s]" % self.falcon_conf['push_url'], req.text)
        except Exception as e:
            if self.falcon_conf['test_run']:
                raise
            else:
                print(datetime.now(), "ERROR: [%s]" % self.ssdb_conf['endpoint'], e)
