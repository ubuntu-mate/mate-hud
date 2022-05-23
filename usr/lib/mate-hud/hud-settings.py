#!/usr/bin/python

import gi
import logging
import os.path
import pkgconfig
import re
import setproctitle

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, Gtk

from common import *
import getkey_dialog

class HUDCurrentSettings():
    @property
    def shortcut(self):
        return get_string( 'org.mate.hud', None, 'shortcut' )

    @property
    def use_custom_width(self):
        return get_custom_width()[0]

    @property
    def custom_width(self):
        return get_custom_width()[1]

    @property
    def custom_width_units(self):
        return get_custom_width()[2]

    @property
    def location(self):
        return get_string( 'org.mate.hud', None, 'location' )

    @property
    def rofi_theme(self):
        return get_string( 'org.mate.hud', None, 'rofi-theme' )

    @property
    def hud_monitor(self):
        return get_string( 'org.mate.hud', None, 'hud-monitor' )

    @property
    def recently_used_max(self):
        return get_number( 'org.mate.hud', None, 'recently-used-max' )

    @property
    def menu_separator(self):
        return get_string( 'org.mate.hud', None, 'menu-separator' )

class HUDSettingsWindow(Gtk.Window):
    widget_name_to_property_map = { 'button-keyboard-shortcut': 'shortcut',
                                    'combobox-rofi-theme': 'rofi_theme',
                                    'checkbutton-use-custom-width': 'use_custom_width',
                                    'entry-custom-width': 'custom_width',
                                    'combobox-custom-width-units': 'custom_width_units',
                                    'combobox-hud-monitor': 'hud_monitor',
                                    'combobox-location': 'location',
                                    'combobox-menu-separator': 'menu_separator',
                                    'entry-recently-used-max': 'recently_used_max' }
    valid_units = [ 'px', 'em', 'ch', '%' ]

    def __init__(self):
        super().__init__(title="HUD Settings")
        self.add_custom_css_classes()
        self.set_border_width(10)
        self.set_resizable(False)
        # Would be nice to have our own icon to use, but for now...
        self.set_icon_name("preferences-system")

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=50)
        self.add(box_outer)

        box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        labelx = Gtk.Label(label="Keyboard Shortcut: ", xalign=0, tooltip_text="Keyboard shortcut to activate the HUD")
        hbox.pack_start(labelx, True, True, 0)
        self.buttonx = Gtk.Button(name='button-keyboard-shortcut')
        self.buttonx.connect("clicked", self.on_shortcut_clicked)
        hbox.pack_start(self.buttonx, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label0 = Gtk.Label(label="HUD Theme: ", xalign=0, tooltip_text="HUD theme. Default is 'mate-hud-rounded'\nThe mate-hud* themes attempt to match the system font and colors from the GTK theme.")
        hbox.pack_start(label0, True, True, 0)
        self.sel0 = Gtk.ComboBoxText(name='combobox-rofi-theme')
        hbox.pack_start(self.sel0, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label1 = Gtk.Label(label="Custom Width: ", xalign=0, tooltip_text="Override the width of the HUD specified in the theme")
        hbox.pack_start(label1, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.checkbutton1 = Gtk.CheckButton(name='checkbutton-use-custom-width')
        self.checkbutton1.connect("toggled", self.use_custom_theme_toggled)
        hbox_.pack_start(self.checkbutton1, True, True, 0)
        self.entry1 = Gtk.Entry(name='entry-custom-width', xalign=1, max_length=4, width_chars=5)
        hbox_.pack_start(self.entry1, True, True, 0)
        self.units1 = Gtk.ComboBoxText(name='combobox-custom-width-units')
        for u in range(len(self.valid_units)):
            self.units1.insert(u, str(u), self.valid_units[u])
        self.units1.set_active(0)
        hbox_.pack_start(self.units1, True, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label2 = Gtk.Label(label="Attach HUD to: ", xalign=0, tooltip_text="Where to attach the HUD.\nDefault is to the current window.\nIf set to monitor, the HUD will try to avoid overlapping any panels.")
        hbox.pack_start(label2, True, True, 0)
        self.sel2 = Gtk.ComboBoxText(name='combobox-hud-monitor')
        for u in range(len(HUD_DEFAULTS.VALID_MONITORS)):
            self.sel2.insert(u, str(u), HUD_DEFAULTS.VALID_MONITORS[u])
        hbox.pack_start(self.sel2, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label3 = Gtk.Label(label="HUD location: ", xalign=0, tooltip_text="How to position the HUD in relation to what is attached to (window or monitor).\n'default' is north west for LTR languages and north east for RTL languages.")
        hbox.pack_start(label3, True, True, 0)
        self.sel3 = Gtk.ComboBoxText(name='combobox-location')
        for u in range(len(HUD_DEFAULTS.VALID_LOCATIONS)):
            self.sel3.insert(u, str(u), HUD_DEFAULTS.VALID_LOCATIONS[u])
        hbox.pack_start(self.sel3, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label4 = Gtk.Label(label="Menu Separator: ", xalign=0, tooltip_text="Character to separate the parts of the menu heirarchy in the HUD (RTL and LTR variants)")
        hbox.pack_start(label4, True, True, 0)
        self.sel4 = Gtk.ComboBoxText(name='combobox-menu-separator')
        for u in range(len(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS)):
            self.sel4.insert(u, str(u), HUD_DEFAULTS.VALID_SEPARATOR_PAIRS[u])
        hbox.pack_start(self.sel4, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label5 = Gtk.Label(label="Max Recently Used Items: ", xalign=0, tooltip_text="Maximum number of recently used items to remember per application")
        hbox.pack_start(label5, True, True, 0)
        adjustment = Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=10, page_size=0, value=0)
        self.entry5 = Gtk.SpinButton(xalign=1, name='entry-recently-used-max', adjustment=adjustment)
        hbox.pack_start(self.entry5, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        label6 = Gtk.Label(label="Recently Used Item List: ", xalign=0, tooltip_text="Reset the recently used item list")
        hbox.pack_start(label6, True, True, 0)
        self.button_reset_recently_used = Gtk.Button(label="Reset")
        self.button_reset_recently_used.connect("clicked", self.reset_recently_used)
        hbox.pack_start(self.button_reset_recently_used, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)      

        box_outer.pack_start(box_main, True, True, 0)

        box_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        self.button_reset_to_defaults = Gtk.Button(label="Reset to defaults")
        self.button_reset_to_defaults.connect("clicked", self.reset_to_defaults)
        box_buttons.pack_start(self.button_reset_to_defaults, True, True, 0)
        self.button_reset = Gtk.Button(label="Clear Changes")
        self.button_reset.connect("clicked", self.reset_view)
        box_buttons.pack_start(self.button_reset, True, True, 0)
        self.button_apply = Gtk.Button(label="Apply Changes")
        self.button_apply.connect("clicked", self.apply_changes)
        box_buttons.pack_start(self.button_apply, False, True, 0)
        box_outer.pack_start(box_buttons, True, True, 0)

    def show_all(self):
        super().show_all()
        self.reload_view()
        self.connect_to_signals()

    def add_custom_css_classes(self):
        ## Add custom style classes for invalid or changed cells
        ## I don't really like doing it this way, but adding the
        ## error or warning class to the fields didn't do a good
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        css = b"""
        entry.changed, combobox.changed button, button.changed, spinbutton.changed entry, checkbutton.changed check {
            border: solid #1fced2;
            background-color: #1fced2;
            color: #000;
            border-width: 2px;
        }
        spinbutton.changed {
            color: #000
        }
        entry.invalid, combobox.invalid button, button.invalid, spinbutton.invalid entry, checkbutton.invalid check {
            border: solid #d83737;
            background-color: #d83737;
            color: #fff;
            border-width: 2px;
        }
        spinbutton.invalid {
            color: #fff
        }
        """
        provider.load_from_data(css)

    def use_custom_menu_separator_toggled(self, button):
        use_cms = button.get_active()
        self.sel4.set_editable(use_cms)
        self.sel4.set_visible(use_cms)

    def use_custom_theme_toggled(self, button):
        use_cw = button.get_active()
        self.entry1.set_editable(use_cw)
        self.entry1.set_visible(use_cw)
        self.units1.set_visible(use_cw)

    def on_shortcut_clicked(self, widget):
        keystr = getkey_dialog.ask_for_key(previous_key=get_string('org.mate.hud', None, 'shortcut'), screen=widget.get_screen(), parent=widget.get_toplevel())
        if not keystr:
            return
        self.buttonx.set_label(keystr)
        self.selection_changed(self.buttonx)

    def reset_to_defaults(self, button):
        logging.info("Resetting all settings to default")
        settings = Gio.Settings.new('org.mate.hud')
        keys = [ 'shortcut', 'hud-monitor', 'location', 'rofi-theme', 'menu-separator', 'custom-width', 'recently-used-max' ]
        for key in keys:
            settings.reset(key)

    def reset_recently_used(self, button):
        logging.info("Resetting recently used menu entry list")
        Gio.Settings.new('org.mate.hud').reset('recently-used')

    def apply_changes(self, button):
        logging.info("Applying changes")
        settings = Gio.Settings.new('org.mate.hud')
        settings.set_string('shortcut', self.buttonx.get_label())

        settings.set_string('hud-monitor', self.sel2.get_active_text())

        settings.set_string('location', self.sel3.get_active_text())

        if self.sel0.get_active_text().endswith(" (Invalid)"):
            settings.set_string('rofi-theme', HUD_DEFAULTS.THEME)
        else:
            settings.set_string('rofi-theme', self.sel0.get_active_text())

        settings.set_string('menu-separator', self.sel4.get_active_text())

        if self.checkbutton1.get_active():
            if validate_custom_width(self.entry1.get_text()):
                settings.set_string('custom-width', self.entry1.get_text() + self.units1.get_active_text())
            else:
                logging.error( "Invalid custom width specified, not setting new value." )
        else:
            settings.set_string('custom-width', '0')

        settings.set_int('recently-used-max', self.entry5.get_value_as_int())

        self.selection_changed_all()

    def selection_changed_all( self ):
        fields = [ self.buttonx, self.sel0, self.checkbutton1, self.entry1, self.units1, self.sel2, self.sel3, self.sel4, self.entry5 ]
        for f in fields:
            self.selection_changed( f )

    def selection_changed( self, field ):
        style_context = field.get_style_context()

        changed = False
        field_type =  type(field).__name__
        if field_type == 'Button':
            print( field.get_name() )
            changed = ( field.get_label() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'SpinButton':
            print( field.get_name() )
            changed = ( field.get_value_as_int() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'ComboBoxText' :
            changed = ( field.get_active_text() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'Entry' :
            changed = ( field.get_text() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'CheckButton' :
            changed = ( field.get_active() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        if changed == True:
            style_context.add_class('changed')
            field.set_tooltip_text("Change not applied yet")
        else:
            style_context.remove_class('changed')
            field.set_has_tooltip(False)

        if field == self.entry1:
            self.indicate_invalid( self.entry1, invalid=( not validate_custom_width(self.entry1.get_text() + self.units1.get_active_text()) ) )
        if field == self.sel0 and self.sel0.get_active_text():
            self.indicate_invalid( self.sel0, invalid=( self.sel0.get_active_text().endswith(' (Invalid)' ) ) )

    def indicate_invalid( self, field, invalid=True ):
        style_context = field.get_style_context()
        if invalid == True:
            style_context.add_class('invalid')
            field.set_tooltip_text("Invalid entry")
        else:
            style_context.remove_class('invalid')
            field.set_has_tooltip(False)

    def connect_to_signals(self):
        self.sel0.connect("changed", self.selection_changed)
        self.checkbutton1.connect("toggled", self.selection_changed )
        self.entry1.connect("changed", self.selection_changed)
        self.units1.connect("changed", self.selection_changed)
        self.sel2.connect("changed", self.selection_changed)
        self.sel3.connect("changed", self.selection_changed)
        self.sel4.connect("changed", self.selection_changed)
        self.entry5.connect("value-changed", self.selection_changed)

    def reload_view_on_change(self, schema, key):
        logging.info( "Reloading view in response to key change." )
        self.reload_view(key=key)

    def reset_view(self, button):
        self.reload_view()

    def reload_view(self, key=None):
        logging.info("reloading view" + ( " for " + key if key else "" ) )

        if not key or key == 'shortcut':
            self.buttonx.set_label( get_string( 'org.mate.hud', None, 'shortcut' ) )

        if not key or key == 'rofi-theme':
            themes = get_theme_list(sort=True)
            self.sel0.remove_all()
            for u in range(len(themes)):
                self.sel0.insert(u, str(u), themes[u])
            try:
                self.sel0.set_active(themes.index(get_rofi_theme()))
                self.indicate_invalid( self.sel0, invalid=False )
            except:
                self.sel0.insert(len(themes), str(len(themes)), get_rofi_theme() + ' (Invalid)')
                self.sel0.set_active(len(themes))
                self.indicate_invalid( self.sel0 )

        if not key or key == 'custom-width':
            use_cw, w, u = get_custom_width()
            self.checkbutton1.set_active(use_cw)
            self.entry1.set_visible(use_cw)
            self.units1.set_visible(use_cw)
            if use_cw:
                try:
                    self.entry1.set_text(w)
                    self.entry1.set_editable(use_cw)
                    self.units1.set_active(self.valid_units.index(u))
                except:
                    self.entry1.set_text('')
                    self.units1.set_active(self.valid_units.index('px'))

        if not key or key == 'hud-monitor':
            self.sel2.set_active(HUD_DEFAULTS.VALID_MONITORS.index(get_monitor()))

        if not key or key == 'location':
            self.sel3.set_active(HUD_DEFAULTS.VALID_LOCATIONS.index(get_location()))

        if not key or key == 'menu-separator':
            self.sel4.set_active(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS.index(get_menu_separator_pair()))

        if not key or key == 'recently-used-max':
            self.entry5.set_value(get_recently_used_max())

if __name__ == "__main__":
    setproctitle.setproctitle('hud-settings')
    logging.basicConfig(level=logging.INFO)

    win = HUDSettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    settings = Gio.Settings.new("org.mate.hud")
    settings.connect("changed::shortcut", win.reload_view_on_change)
    settings.connect("changed::rofi-theme", win.reload_view_on_change)
    settings.connect("changed::hud-monitor", win.reload_view_on_change)
    settings.connect("changed::location", win.reload_view_on_change)
    settings.connect("changed::custom-width", win.reload_view_on_change)
    settings.connect("changed::menu-separator", win.reload_view_on_change)
    settings.connect("changed::recently-used-max", win.reload_view_on_change)

    win.show_all()
    Gtk.main()
