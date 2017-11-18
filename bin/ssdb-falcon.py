#!/usr/bin/env python

import yaml

import ssdbmetrics

with open('conf/ssdb-open-falcon.yml', 'r') as ymlfile:
    config = yaml.load(ymlfile)

threads = []

for ssdb_cluster in config['ssdb-clusters']:
    metric_thread = ssdbmetrics.SSDBMetrics(config['falcon']['push_url'],
                                            ssdb_cluster['endpoint'],
                                            ssdb_cluster['host'],
                                            ssdb_cluster['port'],
                                            ssdb_cluster['password'],
                                            ssdb_cluster['tags'])
    metric_thread.start()
    threads.append(metric_thread)

for thread in threads:
    thread.join(5)