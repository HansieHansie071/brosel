#!/usr/bin/env python
"""Select a browser to use by URL rules

A script and a macOS wrapper app which can be used as OS-wide Default Browser.
The rules are customisable through a config file.

The wrapper app is generated with Platypus (http://sveinbjorn.org/platypus). 
The rules are read with the yaml module, but they are package with the wrapper
app.
"""
__author__ = "halloleo"
__version__ = "0.3.2"
__copyright__ = "Copyright 2017, halloleo"
__appname__ = "brosel" # needs to be hard-coded because Platypus needs "script" as the filename for script

import sys
import os
from os import path as osp

#
# Constants
#
script_path = osp.dirname(__file__)
data_path = osp.join(osp.expanduser('~/Library/Application Support/'), __appname__)
# Log constants
logpath = osp.join(data_path, 'Logs')
# config file constants
cfg_files_list = [osp.join(osp.expanduser('~'), '.' + __appname__) ,
                  osp.join(data_path, __appname__+'.yaml')]
BROWSER_DEFAULT = 'open -a Safari %s'

#
# Logging
#
try:
    os.makedirs(logpath)
except OSError:
    pass
logpath = osp.join(logpath, __appname__+'.log')

import logging
import logging.config
log = logging.getLogger(__name__)
loglevel = logging.INFO

if osp.exists(osp.join(script_path,'DEBUG')):
    loglevel = logging.DEBUG

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main': {
            'datefmt':'%Y-%m-%d %H:%M:%S',
            'format': '%(asctime)s %(levelname)s: %(message)s',
        },
    },
    'handlers': {
        'stdout': {
            'class':'logging.StreamHandler',
            'formatter':'main'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'main',
            'filename': logpath,
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 1,
        }
    },
    'loggers': {
        '': {
            'handlers': ['file','stdout'],
            'level': loglevel,
            'propagate': True
        }
    }
})

#
# Configuration file
#
import re
import webbrowser
import yaml

class Config:
    """
    holds the configuration
    """

    def __init__(self):
        # data
        self.browser_default = BROWSER_DEFAULT
        self.rules = []

        fn = self.find_cfg_file()
        if fn:
            log.info("Loading config from %s" % fn)
            self.load_from_file(fn)
        else:
            log.debug("No config found")

    def find_cfg_file(self):
        for fn in cfg_files_list:
            log.debug("Check file location %s..." % fn)
            if osp.exists(fn):
                return fn
        return None

    def load_from_file(self, fname):
        # load data
        yaml_data = None
        try:
            with open(fname, 'r') as fstream:
                yaml_data = yaml.load(fstream)
        except (IOError, yaml.YAMLError) as e:
                log.debug('Exception %s' % e)
        log.debug("yaml_data = %s" % yaml_data)

        # fit data into config object
        try:
            self.browser_default  = yaml_data['basic']['browser_id']
        except (KeyError, TypeError) as e:
            log.debug('Exception %s' % e)
        try:
            rules_data = yaml_data['rules']
            log.debug("r_data = %s" % rules_data)
            for r_data in rules_data:
                log.debug("r = %s" % r_data)

                # each rule can have keys "browser_id", "url_pattern" and
                # "url_replace"
                r={}
                keys = ['browser_id', 'url_pattern', 'url_replace']
                for k in keys:
                    try:
                        r[k] = r_data[k]
                    except KeyError as e:
                        log.debug('Key Error %s' % e)
                if len (r) > 0:
                    self.rules.append(r)
        except (KeyError, TypeError) as e:
            log.debug('Exception %s' % e)

#
# The real work
#
def select_and_open (url, cfg):
    """Select the browser to use via configuration and open the URL"""
    # set default browser
    log.debug("Initialise with default browser")
    selected_browser = webbrowser.get(cfg.browser_default)
    # set browser according to rules
    for r in cfg.rules:
        url_pattern = r.get('url_pattern')
        url_replace = r.get('url_replace')
        browser_id = r.get('browser_id')
        if isinstance(url_pattern, basestring):
            p = re.compile(url_pattern)
            if p.search(url):
                if isinstance(url_replace, basestring):
                    url = p.sub(url_replace, url)
                if isinstance(browser_id, basestring):
                    log.debug("-- Set browser to browser '%s'" % browser_id)
                    selected_browser = webbrowser.get(browser_id)

    log.info("Selected browser: '%s %s'" % (selected_browser.name,
                                          ' '.join(selected_browser.args)))
    log.info("URL to open via 'open_new_tab': '%s'" % url)
    selected_browser.open_new_tab(url)
    log.debug("'open_new_tab' done")



if __name__ == '__main__':
    args = sys.argv[1:]
    log.debug("Program args: %s" % args)
    cfg = Config()
    for arg in args:
        log.debug("Find browser for url '%s'..." % arg)
        select_and_open(arg, cfg)
