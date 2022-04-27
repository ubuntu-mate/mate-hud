#!/usr/bin/python

import gi
import logging
import os
import pkgconfig
import re
import setproctitle

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, Gtk

from common import *

class HUDSettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="HUD Settings")
        self.set_border_width(10)

        ## Add custom style classes for invalid or changed cells
        ## I don't really like doing it this way, but adding the
        ## error or warning class to the fields didn't really
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        css = b"""
        entry.changed, combobox.changed button{
            border: solid #1fced2;
            background-color: #1fced2;
            color: #000;
            border-width: 2px;
        }
        entry.invalid, combobox.invalid button {
            border: solid #d83737;
            background-color: #d83737;
            color: #fff;
            border-width: 2px;
        }
        """
        provider.load_from_data(css)

        def use_custom_theme_toggled(self):
            entry1.set_editable(checkbutton1.get_active())

        def use_custom_menu_separator_toggled(self):
            entry4.set_editable(checkbutton4.get_active())

        def selection_changed(self):
            if self == checkbutton1 or self == entry1 or self == units1:
                indicate_changed( checkbutton1 )
                indicate_changed( entry1 )
                indicate_changed( units1 )
            if self == checkbutton4 or self == entry4:
                indicate_changed( checkbutton4 )
                indicate_changed( entry4 )
            else:
                indicate_changed( self )

        def reset_to_defaults(self):
            print("resetting settings to default")
            settings = Gio.Settings.new('org.mate.hud')
            keys = [ 'hud-monitor', 'location', 'rofi-theme', 'menu-separator', 'custom-width' ]
            for key in keys:
                settings.reset(key)

        def apply_changes(self):
            print("applying changes")
            settings = Gio.Settings.new('org.mate.hud')
            settings.set_string('hud-monitor', sel2.get_active_text())
            indicate_changed( sel2, False )

            settings.set_string('location', sel3.get_active_text())
            indicate_changed( sel3, False )

            if sel0.get_active_text().endswith(" (Invalid)"):
                settings.set_string('rofi-theme', HUD_DEFAULTS.THEME)
            else:
                settings.set_string('rofi-theme', sel0.get_active_text())
            indicate_changed( sel0, False )

            sep = entry4.get_text()
            default = HUD_DEFAULTS.SEPARATOR if not isrtl() else HUD_DEFAULTS.SEPARATOR_RTL
            if not checkbutton4.get_active():
                sep = 'default'
            elif len(re.findall(r'^(0[xX])?[0-9A-Fa-f]{2,6}$', sep)) == 1:
                try:
                    sep =  chr(int(sep, 16))
                except:
                    sep = default_sep
            elif len(sep) == 1:
                pass
            else:
                sep = default_sep
            settings.set_string('menu-separator', sep)
            indicate_changed( entry4, False )

            if checkbutton1.get_active():
                if validate_custom_width(entry1.get_text()):
                    settings.set_string('custom-width', entry1.get_text() + units1.get_active_text())
                else:
                    logging.error( "Invalid custom width specified, not setting new value." )
            else:
                settings.set_string('custom-width', '0')
            indicate_changed( entry1, False )

        def indicate_changed( field, changed=True ):
            style_context = field.get_style_context()
            if changed == True:
                style_context.add_class('changed')
            else:
                style_context.remove_class('changed')
            field.set_tooltip_text("Change not applied yet")

        def indicate_invalid( field, invalid=True ):
            style_context = field.get_style_context()
            if invalid == True:
                style_context.add_class('invalid')
            else:
                style_context.remove_class('invalid')
            field.set_tooltip_text("Invalid entry")

        global reload_view_on_change
        def reload_view_on_change(schema, key):
            logging.info( "Reloading view in response to key change." )
            reload_view(key=key)

        def reload_view(key=None):
            logging.info("reloading view" + ( " for " + key if key else "" ) )

            if not key or key == 'rofi-theme':
                themes = []
                theme_dirs = [ os.path.expanduser('~') + '/.local/share/rofi/themes/' ,
                               pkgconfig.variables('rofi').get('prefix') + '/share/rofi/themes/' ]
                for directory in theme_dirs:
                    for filename in os.listdir(directory):
                        f = os.path.join(directory, filename)
                        # checking if it is a file
                        if os.path.isfile(f):
                            if filename[-5:] == '.rasi':
                                theme = filename[:-5]
                                if theme not in themes:
                                    themes.append( theme )
                def sort_themes(a):
                    return a.lower()
                themes.sort(key=sort_themes)
                for u in range(len(themes)):
                    sel0.insert(u, str(u), themes[u])
                try:
                    sel0.set_active(themes.index(get_rofi_theme()))
                    indicate_invalid( sel0, invalid=False )
                except:
                    sel0.insert(len(themes), str(len(themes)), get_rofi_theme() + ' (Invalid)')
                    sel0.set_active(len(themes))
                    indicate_invalid( sel0 )

            if not key or key == 'custom-width':
                checkbutton1.set_active( use_custom_width() )
                try:
                    w = get_custom_width()
                    entry1.set_text(w[0])
                    entry1.set_editable(use_custom_width())
                    units1.set_active(valid_units.index(w[1]))
                except:
                    entry1.set_text('')
                    units1.set_active(valid_units.index('px'))

            if not key or key == 'hud-monitor':
                sel2.set_active(HUD_DEFAULTS.VALID_MONITORS.index(get_monitor()))

            if not key or key == 'location':
                sel3.set_active(HUD_DEFAULTS.VALID_LOCATIONS.index(get_location()))

            if not key or key == 'menu-separator':
                checkbutton4.set_active(use_custom_separator())
                entry4.set_text(get_menu_separator())

        settings = Gio.Settings.new("org.mate.hud")
        settings.connect("changed::rofi-theme", reload_view_on_change)
        settings.connect("changed::hud-monitor", reload_view_on_change)
        settings.connect("changed::location", reload_view_on_change)
        settings.connect("changed::custom-width", reload_view_on_change)
        settings.connect("changed::menu-separator", reload_view_on_change)

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box_outer)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)        
        label0 = Gtk.Label(label="HUD Theme: ", xalign=0, tooltip_text="HUD theme. Default is 'mate-hud-rounded'\nThe mate-hud* themes attempt to match the system font and colors from the GTK theme.")
        hbox.pack_start(label0, True, True, 0)
        sel0 = Gtk.ComboBoxText()
        hbox.pack_start(sel0, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)        
        label1 = Gtk.Label(label="Custom Width: ", xalign=0, tooltip_text="Override the width of the HUD specified in the theme")
        hbox.pack_start(label1, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        checkbutton1 = Gtk.CheckButton()
        checkbutton1.connect("toggled", use_custom_theme_toggled)
        hbox_.pack_start(checkbutton1, True, True, 0)
        entry1 = Gtk.Entry(xalign=1, max_length=4, width_chars=5)
        hbox_.pack_start(entry1, True, True, 0)
        units1 = Gtk.ComboBoxText()
        valid_units = [ 'px', 'em', 'ch', '%' ]
        for u in range(len(valid_units)):
            units1.insert(u, str(u), valid_units[u])
        units1.set_active(0)
        hbox_.pack_start(units1, True, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)        
        label2 = Gtk.Label(label="Attach HUD to: ", xalign=0, tooltip_text="Where to attach the HUD.\nDefault is to the current window.\nIf set to monitor, the HUD will try to avoid overlapping any panels.")
        hbox.pack_start(label2, True, True, 0)
        sel2 = Gtk.ComboBoxText()
        for u in range(len(HUD_DEFAULTS.VALID_MONITORS)):
            sel2.insert(u, str(u), HUD_DEFAULTS.VALID_MONITORS[u])
        hbox.pack_start(sel2, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label3 = Gtk.Label(label="HUD location: ", xalign=0, tooltip_text="How to position the HUD in relation to what is attached to (window or monitor).\n'default' is north west for LTR languages and north east for RTL languages.")
        hbox.pack_start(label3, True, True, 0)
        sel3 = Gtk.ComboBoxText()
        for u in range(len(HUD_DEFAULTS.VALID_LOCATIONS)):
            sel3.insert(u, str(u), HUD_DEFAULTS.VALID_LOCATIONS[u])
        hbox.pack_start(sel3, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label4 = Gtk.Label(label="Custom Menu Separator: ", xalign=0, tooltip_text="Character to use to denote the menu heirarchy in the HUD.\nMust be one character or the unicode code point (in hex) of a single character\nor the word 'default': » for LTR languages and « for RTL languages")
        hbox.pack_start(label4, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        checkbutton4 = Gtk.CheckButton()
        checkbutton4.connect("toggled", use_custom_menu_separator_toggled)
        hbox_.pack_start(checkbutton4, True, True, 0)
        entry4 = Gtk.Entry(xalign=1, max_length=8, width_chars=9)
        hbox_.pack_start(entry4, True, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        button_reset = Gtk.Button(label="Reset to defaults")
        button_reset.connect("clicked", reset_to_defaults)
        hbox.pack_start(button_reset, True, True, 0)
        button_apply = Gtk.Button(label="Apply Changes")
        button_apply.connect("clicked", apply_changes)
        hbox.pack_start(button_apply, False, True, 0)
        box_outer.pack_start(hbox, True, True, 0)

        reload_view()
        sel0.connect("changed", selection_changed)
        entry1.connect("changed", selection_changed)
        units1.connect("changed", selection_changed)
        sel2.connect("changed", selection_changed)
        sel3.connect("changed", selection_changed)
        entry4.connect("changed", selection_changed)
        indicate_invalid( sel0 )

if __name__ == "__main__":
    setproctitle.setproctitle('hud-settings')
    logging.basicConfig(level=logging.INFO)

    win = HUDSettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    settings = Gio.Settings.new("org.mate.hud")
    settings.connect("changed::rofi-theme", reload_view_on_change)
    settings.connect("changed::hud-monitor", reload_view_on_change)
    settings.connect("changed::location", reload_view_on_change)
    settings.connect("changed::custom-width", reload_view_on_change)
    settings.connect("changed::menu-separator", reload_view_on_change)

    win.show_all()
    Gtk.main()
