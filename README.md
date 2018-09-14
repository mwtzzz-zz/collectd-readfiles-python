collectd-readfiles-python
======================

`collectd-readfiles-python` is a plugin for collectd that gathers metrics from file(s) you specify and 
submits them to collectd at the interval you specify.

You may specify any number of files you want to monitor. The plugin assumes the first line of the file 
contains the value that you are interested in.

This plugin uses threads to process the files in parallel, thereby minimizing overhead. Files that
don't exist or cannot be opened for reading are skipped without impacting the rest of them.

This plugin was written in python to take advantage of collectd's builtin python interpreter which
makes use of collectd's callback functions. This allows it to take advantage of collectd's caching and
interface with the write plugins. This makes it much more efficient than using the Exec 
plugin, which can be important the more your environment scales up. For example, [write_graphite](https://collectd.org/wiki/index.php/Plugin:Write_Graphite) 
maintains a persistent TCP connection with carbon to minimize network overhead, something you cannot
do with the Exec plugin.

How to use it
-------------

First, copy collectd_readfiles_python.py to the module path on your system, eg. /usr/lib64/collectd/

Next, edit collectd.conf as shown in the following example:

```
<Plugin python>
    ModulePath "/usr/lib64/collectd/"
    Import "collectd_readfiles_python"

    <Module collectd_readfiles_python>
        DeriveMetricFiles "/sys/class/net/eth0/statistics/rx_bytes" "/sys/class/net/eth0/statistics/tx_by
tes"
        Interval 25
        Verbose true
        PluginName collectd_generic_network_stats__python
    </Module>
</Plugin>

```

* `Interval`: how often do you want the plugin to extract the metric value from the file
* `Verbose`: if you want syslog to get more messages about what the plugin is doing
* `PluginName`: forms part of the whole metric name that gets submitted to collectd, so make it descriptive. 
* `DeriveMetricFiles`: one or more files that contain metrics that are of the "derive" type
* `GaugeMetricFiles`: one or more files that contain metrics that are of the "gauge" type

For information about different metric types, see: [metric types](https://docs.opnfv.org/en/stable-fraser/submodules/barometer/docs/development/requirements/02-
and [man types.db(5)](http://linux.die.net/man/5/types.db)

Also, be aware that a setting called StoreRates for your write plugins affects the value that gets written 
for derive and counter metrics. When StoreRates is True, a rate is calculated from subsequent 
values of the metric. The delta is divided by the interval, so that the value that gets written is always 
"per second." This setting does not affect gauge metrics. 

Notes
-----

The interval passed to dispatch() appears to have no effect. See:

* [Forum discussion google](https://plus.google.com/101465842317006300704/posts/JGWAhsT3avi)
* [Forum discussion github](https://github.com/collectd/collectd/issues/2909)

License
-------

[MIT](http://mit-license.org/)


Contact
-------

[Michael Martinez](mailto:mwtzzz@gmail.com)
