#!/usr/bin/python

import gi
import logging
import os
import pkgconfig
import re

from gi.repository import Gio

def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)
    
class Defaults(object):
    @constant
    def THEME():
        return 'mate-hud-rounded'

    @constant
    def SEPARATOR():
        return u'\u00BB'

    @constant
    def SEPARATOR_RTL():
        return u'\u00AB'

    @constant
    def LOCATION():
        return 'north west'
        
    @constant
    def LOCATION_RTL():
        return 'north east'

    @constant
    def MONITOR():
        return 'window'

    @constant
    def VALID_LOCATIONS():
        return [ 'default', 'north west', 'north', 'north east', 'east', 'south east', 'south', 'south west', 'west', 'center' ]

    @constant
    def VALID_MONITORS():
        return [ 'window', 'monitor' ]

HUD_DEFAULTS = Defaults()

def get_bool(schema, path, key):
    if path:
        settings = Gio.Settings.new_with_path(schema, path)
    else:
        settings = Gio.Settings.new(schema)
    return settings.get_boolean(key)

def get_string(schema, path, key):
    if path:
        settings = Gio.Settings.new_with_path(schema, path)
    else:
        settings = Gio.Settings.new(schema)
    return settings.get_string(key)

def get_number(schema, path, key):
    if path:
        settings = Gio.Settings.new_with_path(schema, path)
    else:
        settings = Gio.Settings.new(schema)
    return settings.get_int(key)

def get_list(schema, path, key):
    if path:
        settings = Gio.Settings.new_with_path(schema, path)
    else:
        settings = Gio.Settings.new(schema)
    return settings.get_strv(key)

def get_rofi_theme():
    rofi_theme = 'mate-hud-rounded'
    try:
        rofi_theme = get_string('org.mate.hud', None, 'rofi-theme')
    except:
        logging.error('org.mate.hud gsettings not found. Defaulting to %s.' % rofi_theme)
    return rofi_theme

def validate_custom_width(custom_width):
    custom_width = re.sub(r'\s', '', custom_width)
    if len(re.findall(r'^[0-9]+(\.[0-9]+)?(px|em|ch|%)?$', custom_width)) == 1:
        w = re.sub(r'(px|em|ch|%)?$', '', custom_width)
        try:
            w = int(w)
            return True
        except:
            pass
    return False

def get_custom_width():
    custom_width = get_string('org.mate.hud', None, 'custom-width')
    if validate_custom_width(custom_width):
        custom_width = re.sub(r'\s', '', custom_width)
        w = re.sub(r'(px|em|ch|%)?$', '', custom_width)
        u = re.sub(r'^[0-9]+(\.[0-9]+)?', '', custom_width)
        if u == '':
            u = 'px'
        return [ w, u ]
    raise ValueError( "Invalid custom width specified" )

def use_custom_width():
    try:
        w = get_custom_width()
        if not ( w[0] == '0' and w[1] == 'px' ):
            return True
    except:
        pass
    return False

def get_menu_separator():
    default = HUD_DEFAULTS.SEPARATOR if not isrtl() else HUD_DEFAULTS.SEPARATOR_RTL
    menu_separator = get_string('org.mate.hud', None, 'menu-separator')
    if len(re.findall(r'^(0[xX])?[0-9A-Fa-f]{2,6}$', menu_separator)) == 1:
        try:
            return chr(int(menu_separator, 16))
        except:
            return default
    elif len(menu_separator) == 1:
        return menu_separator
    else:
        return default

def monitor_rofi_argument(monitor):
    arguments = { 'window': '-2', 'monitor': '-1' }
    if monitor in HUD_DEFAULTS.VALID_MONITORS:
        return arguments[monitor]
    else:
        return arguments[HUD_DEFAULTS.MONITOR]

def get_monitor():
    monitor = HUD_DEFAULTS.MONITOR
    try:
        monitor = get_string('org.mate.hud', None, 'hud-monitor')
    except:
        logging.error('org.mate.hud gsettings not found. Defaulting to %s.' % HUD_DEFAULTS.MONITOR)
    if monitor in HUD_DEFAULTS.VALID_MONITORS:
        return monitor
    else:
        return HUD_DEFAULTS.MONITOR

def get_location():
    default_location = 'default'
    location = default_location
    try:
        location = get_string('org.mate.hud', None, 'location')
    except:
        logging.error('org.mate.hud gsettings not found. Defaulting to %s.' % default_location)
    if location not in HUD_DEFAULTS.VALID_LOCATIONS:
        location = default_location
        logging.error("Invalid location specified, defaulting to %s" % default_location )
    return location

def use_custom_separator():
    default = HUD_DEFAULTS.SEPARATOR if not isrtl() else HUD_DEFAULTS.SEPARATOR_RTL
    sep = get_menu_separator()
    return not ( sep == default or sep == 'default' )

def isrtl():
    lang = os.environ['LANG'].split('_')[0]
    rtl_languages = [ 'ar', 'arc', 'ckb', 'dv', 'fa', 'ha', 'he', 'khw', 'ks', 'ps', 'sd', 'ur', 'yi' ]
    return lang in rtl_languages
