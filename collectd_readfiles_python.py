#!/usr/bin/env python
#
# collectd-readfiles-python
# ======================
#
# Plugin for collectd that reads metrics from file(s) specified
# in the Module section for the Plugin in collectd.conf
# Each file is assumed to contain a metric value on the first line.
# Metrics are submitted to all enabled write plugins.
#
# https://github.com/mwtzzz/collectd-readfiles/
#

import sys
import string
import os
import collectd
import threading

class ObtainMetrics(object):
    def __init__(self):
        self.plugin_name = 'collectd-readfiles-python'
        self.derivemetricfiles = ""
        self.gaugemetricfiles = ""
        self.interval = 60.0
        self.verbose_logging = True

    """
    Whether or not collectd.[info|warning|etc] messages get written depends
    on LogLevel for syslog in /etc/collectd.conf
    """
    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.warning('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        """
        Grab the configuration.
        """
        for node in conf.children:
            # self.log_verbose("node.values: %s\n" % str(node.values))
            val = str(node.values[0])

            if node.key == 'DeriveMetricFiles':
                self.derivemetricfiles = node.values
            elif node.key == 'GaugeMetricFiles':
                self.gaugemetricfiles = node.values
            elif node.key == 'Interval':
                self.interval = float(val)
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            else:
                collectd.warning(
                    '%s plugin: Unknown config key: %s.' % (
                        self.plugin_name,
                        node.key))

        self.log_verbose(
            'Configured with DeriveMetricFiles %s, GaugeMetricFiles %s, Interval %s, Plugin Name %s' % (
                self.derivemetricfiles, self.gaugemetricfiles, self.interval, self.plugin_name))
        
        collectd.register_read(self.read_callback, self.interval)

    # collectd runs the read callback in a separate thread at frequency of self.interval
    def read_callback(self):
        def read_and_dispatch_file(datasource, F_type):
                try:
                    metricfile = open(datasource, 'r')
                except:
                    collectd.warning("Unable to open %s. Moving on to next file ...\n" % datasource)
                    return
                self.log_verbose("Obtaining metric for file: %s\n" % datasource)
                val = collectd.Values()
                inst = os.path.basename(os.path.dirname(datasource))
                if not inst:
                    inst = os.path.basename(datasource)
                # the following four components determine the metric name
                val.plugin = self.plugin_name
                val.plugin_instance = inst
                val.type = F_type
                val.type_instance = os.path.basename(datasource)
                #
                metricvalue = metricfile.readline()
                if not metricvalue:
                    collectd.warning("Unable to read a value from %s. Moving on to next file ... \n" % datasource)
                    metricfile.close()
                    return
                val.values = [float(metricvalue)]
                val.meta={'0': True}
                self.log_verbose("Dispatching value %s with interval %s\n" % (val.values, self.interval))
                """
                Dispatch values stored in the val object to all enabled write plugins.
                Interval is basically unused and/or expected to be the same as
                how often the callback is called.
                """
                val.dispatch(interval=self.interval)
                metricfile.close()

        """  
        Metric types can be derive, counter, gauge, or absolute.
        See https://docs.opnfv.org/en/stable-fraser/submodules/barometer/docs/development/requirements/02-collectd.html
        and see man 5 types.db
        """

        for file in self.derivemetricfiles:
            self.log_verbose("Processing %s\n" % file)
            """
            Note: using multiprocessing instead of threading results in nothing 
                  getting written
            """
            p = threading.Thread(target=read_and_dispatch_file,
                args=(file,"derive"))
            p.start()

        for file in self.gaugemetricfiles:
            self.log_verbose("Processing %s\n" % file)
            p = threading.Thread(target=read_and_dispatch_file,
                args=(file,"gauge"))
            p.start()

def restore_sigchld():
    """
    See https://github.com/deniszh/collectd-iostat-python/issues/2 
    """
    if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

# if this script is launched from command line just print to standard out
if __name__ == '__main__':
    print("%s lauched directly from command line" % (sys.argv[0]))
    sys.exit(0)
# otherwise if it is launched from within collectd then do the collectd stuff
else:
    stuff = ObtainMetrics()
    collectd.register_init(restore_sigchld)
    collectd.register_config(stuff.configure_callback)
    collectd.warning("This plugin has exited.")

