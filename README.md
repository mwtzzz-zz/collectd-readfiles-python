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
plugin. Such efficiency can be crucial as your environment scales up.
For example, [write_graphite](https://collectd.org/wiki/index.php/Plugin:Write_Graphite) 
maintains a persistent TCP connection with carbon to minimize network overhead. The python plugin
takes advantage of this, but the Exec plugin cannot.

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

* `Interval`: how often do you want the plugin to extract the metric value from the file and write them to the write plugins
* `Verbose`: if you want syslog to get more messages about what the plugin is doing
* `PluginName`: forms part of the whole metric name that gets submitted to collectd, so make it descriptive. 
* `DeriveMetricFiles`: one or more files that contain metrics that are of the "derive" type
* `GaugeMetricFiles`: one or more files that contain metrics that are of the "gauge" type

For information about different metric types, see: [metric types](https://docs.opnfv.org/en/stable-fraser/submodules/barometer/docs/development/requirements/02-collectd.html) and [man types.db(5)](http://linux.die.net/man/5/types.db)

Be aware that a setting called StoreRates for your write plugins affects the value that gets written 
for derive and counter metrics. When StoreRates is True, a rate is calculated from subsequent 
values of the metric. The delta is divided by the interval, so that the value that gets written is always 
"per second." This setting does not affect gauge metrics. 

Be aware that if you submit metrics to graphite faster than the finest granularity you 
have specified for storage retention, 
graphite only keeps the most recent value on disk. To be more specific: (a) the relay will pass metrics
to carbon-cache as fast as they come in, assuming it not configured to aggregate them; 
(b) each time carbon-cache receives a metric, it temporarily writes it to disk (assuming it has enough 
time to flush it from memory cache), **overwriting** the previous value if in the middle 
of the retention period; (c) each time the top of the retention period comes around, the latest value becomes the one permanently kept on disk. For example, assume your finest retention period is 1m and your
python plugin submits a metric every 20s. Each minute, the first two of these values (at 20s and 40s) 
will be temporarily written to the whisper file, but will be overwritten by the value submitted at 
the 60s mark. 

Notes
-----

The interval passed to dispatch() appears to have no effect. See:

* [Forum discussion google](https://plus.google.com/101465842317006300704/posts/JGWAhsT3avi)
* [Forum discussion github](https://github.com/collectd/collectd/issues/2909)

There is minimal documentation on how to write python plugins for collectd. Your best reference
is to look at what I've done and to read the man page. There's also a brief online tutorial 
you might find helpful:
* [man page for collectd-python](http://linux.die.net/man/5/collectd-python)
* [tutorial](https://blog.dbrgn.ch/2017/3/10/write-a-collectd-python-plugin/)

In a nutshell:
1. When you register configure_callback, it gets called once at startup and loads the config options
from collectd.conf. Your code is responsible for handling these options, 
assigning them to variables, or doing whatever you need with them. Collectd won't know what to 
do with them, as they are arbitrary options that you create.
2. When you register read_callback, collectd will automatically run this function at the interval
you specify. Therefore, you only need to run register_read() one time. Although you don't have to run it
from within your configure_callback function, it's a good place to do it since configure_callback
only gets called once and it's where you load the config options you likely will need to refer to 
in your read callback. You must explicitly call dispatch() from within your read_callback in order to submit metrics into collectd. If you don't call dispatch(), no values will be submitted as collectd 
does not automatically grab them for you.
3. dispatch() submits values into collectd, which caches them and sends them to all enabled 
write plugins. It does this via a method in a Values() object. It's okay to repeatedly use a 
Values object in a loop, because each time you initialize the object a different instance gets created
with a unique value to be dispatched.


License
-------

[MIT](http://mit-license.org/)


Contact
-------
If you find bugs or want to submit enhancements, please let me know via Issues and PRs. 
[Michael Martinez](mailto:mwtzzz@gmail.com)
