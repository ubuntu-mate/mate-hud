#!/usr/bin/python3

import gi
import logging
import os
import re

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk

import i18n
_ = i18n.language.gettext

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

    @constant
    def VALID_SEPARATOR_PAIRS():
        # unicode pair: left arrow (for RTL languages),  3 spaces (to make it easier to read), right arrow
        # If you add more valid pairs here, be sure to add them in the schema org.mate.hud.separator-pairs enum too.
        return [ u'\u25C2' + ' '*3 + u'\u25B8',  # "◂   ▸"
                 u'\u2190' + ' '*3 + u'\u2794',  # "←   ➔" # doesn't seem to be a left arrow to match the right, so close enough
                 u'\u2190' + ' '*3 + u'\u279C',  # "←   ➜" # doesn't seem to be a left arrow to match the right, so close enough
                 u'\u276E' + ' '*3 + u'\u276F',  # "❮   ❯"
                 u'\u00AB' + ' '*3 + u'\u00BB',  # "«   »"
                 u'\u2039' + ' '*3 + u'\u203A' ] # "‹   ›"

    @constant
    def SEPARATOR():
        return HUD_DEFAULTS.VALID_SEPARATOR_PAIRS[0]

    @constant
    def RECENTLY_USED_MAX():
        return 10

    @constant
    def RECENTLY_USED_UNLIMITED():
        return -1

    @constant
    def RECENTLY_USED_NONE():
        return 0

    @constant
    def CUSTOM_WIDTH():
        return '0'

    @constant
    def PROMPT():
        return _('HUD')

    @constant
    def RECENTLY_USED_DECORATION():
        return u'\u2015' * 100

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
        logging.error(_('org.mate.hud gsettings not found. Defaulting to ') + rofi_theme)
    return rofi_theme

def validate_custom_width(custom_width):
    custom_width = re.sub(r'\s', '', custom_width)
    if len(re.findall(r'^[0-9]+(px|em|ch|%)?$', custom_width)) == 1:
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
        u = re.sub(r'^[0-9]+', '', custom_width)
        if u == '':
            u = 'px'
        return [ not ( w == '0' and u == 'px' ), w, u ]
    raise ValueError( _("Invalid custom width specified") )

def use_custom_width():
    try:
        w = get_custom_width()
        if not ( w[0] == '0' and w[1] == 'px' ):
            return True
    except:
        pass
    return False

def get_menu_separator_pair():
    menu_separator = HUD_DEFAULTS.SEPARATOR
    try: menu_separator = get_string('org.mate.hud', None, 'menu-separator')
    except: pass
    return menu_separator

def get_menu_separator(pair=None):
    if not pair:
        pair = get_menu_separator_pair()
    #pair stored as 'R   L' R: RTL separator, L: LTR separator (spaces may be variable, currently 3)
    if isrtl():
        return pair[0]
    else:
        return pair[-1]

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
        logging.error(_('org.mate.hud gsettings not found. Defaulting to ') + HUD_DEFAULTS.MONITOR)
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
        logging.error(_('org.mate.hud gsettings not found. Defaulting to ') + default_location)
    if location not in HUD_DEFAULTS.VALID_LOCATIONS:
        location = default_location
        logging.error(_("Invalid location specified, defaulting to ") + default_location )
    return location

def get_recently_used_max():
    recently_used_max = 0
    try:
        recently_used_max = get_number('org.mate.hud', None, 'recently-used-max')
    except:
        logging.error(_('org.mate.hud gsettings not found. Defaulting to ') + recently_used_max)
    return recently_used_max

def get_transparency():
    transparency = 100
    try:
        transparency = get_number('org.mate.hud', None, 'transparency')
    except:
        logging.error(_('org.mate.hud gsettings not found. Defaulting to ') + transparency)
    return transparency

def isrtl():
    window = Gtk.Window()
    style_context = window.get_style_context()
    state = style_context.get_state()
    return state & Gtk.StateFlags.DIR_RTL

def get_theme_list(sort=False):
    def sort_themes(theme_name):
        return theme_name.lower()

    themes = []
    theme_dirs = [ os.path.expanduser('~') + '/.local/share/rofi/themes/' ,
                   '/usr/share/rofi/themes/' ]
    for directory in theme_dirs:
        if os.path.isdir(directory):
            for filename in os.listdir(directory):
                f = os.path.join(directory, filename)
                # checking if it is a file
                if os.path.isfile(f) and filename[-5:] == '.rasi':
                    theme = filename[:-5]
                    if theme not in themes:
                        themes.append( theme )
    if sort:
        themes.sort(key=sort_themes)
    return themes

def rgba_to_hex(color):
   """
   Return hexadecimal string for :class:`Gdk.RGBA` `color`.
   """
   return "#{0:02x}{1:02x}{2:02x}".format(
                                    int(color.red   * 255),
                                    int(color.green * 255),
                                    int(color.blue  * 255))

def get_color(style_context, preferred_color, fallback_color):
    color = rgba_to_hex(style_context.lookup_color(preferred_color)[1])
    if color == '#000000':
        color = rgba_to_hex(style_context.lookup_color(fallback_color)[1])
    return color
