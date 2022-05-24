#!/usr/bin/python3

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

import i18n
_ = i18n.language.gettext

class HUDCurrentSettings():
    @property
    def shortcut(self):
        return get_string( 'org.mate.hud', None, 'shortcut' )

    @property
    def use_custom_width(self):
        return get_custom_width()[0]

    @property
    def custom_width(self):
        return int(get_custom_width()[1])

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
    widget_name_to_property_map = { 'combobox-keyboard-shortcut': 'shortcut',
                                    'button-keyboard-shortcut': 'shortcut',
                                    'combobox-rofi-theme': 'rofi_theme',
                                    'checkbutton-use-custom-width': 'use_custom_width',
                                    'entry-custom-width': 'custom_width',
                                    'combobox-custom-width-units': 'custom_width_units',
                                    'combobox-hud-monitor': 'hud_monitor',
                                    'combobox-location': 'location',
                                    'combobox-menu-separator': 'menu_separator',
                                    'entry-recently-used-max': 'recently_used_max' }
    valid_units = [ 'px', 'em', 'ch', '%' ]
    single_modifier_keys = [ 'Alt_L', 'Alt_R', 'Ctrl_L', 'Ctrl_R', 'Super_L', 'Super_R' ]

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
        lbl_shortcut = Gtk.Label(label=_("Keyboard Shortcut: "), xalign=0, tooltip_text=_("Keyboard shortcut to activate the HUD"))
        hbox.pack_start(lbl_shortcut, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.cbx_shortcut = Gtk.ComboBoxText(name='combobox-keyboard-shortcut')
        for u in range(len(self.single_modifier_keys)):
            self.cbx_shortcut.insert(u, str(u), self.single_modifier_keys[u])
        self.cbx_shortcut.insert(len(self.single_modifier_keys), str(len(self.single_modifier_keys)), _("Custom: "))
        hbox_.pack_start(self.cbx_shortcut, False, True, 0)
        self.btn_shortcut = Gtk.Button(name='button-keyboard-shortcut')
        self.btn_shortcut.connect("clicked", self.on_shortcut_clicked)
        hbox_.pack_start(self.btn_shortcut, False, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_theme = Gtk.Label(label=_("HUD Theme: "), xalign=0, tooltip_text=_("HUD theme. Default is 'mate-hud-rounded'\nThe mate-hud* themes attempt to match the system font and colors from the GTK theme."))
        hbox.pack_start(lbl_theme, True, True, 0)
        self.cbx_theme = Gtk.ComboBoxText(name='combobox-rofi-theme')
        hbox.pack_start(self.cbx_theme, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_width = Gtk.Label(label=_("Custom Width: "), xalign=0, tooltip_text=_("Override the width of the HUD specified in the theme"))
        hbox.pack_start(lbl_width, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.ckb_width = Gtk.CheckButton(name='checkbutton-use-custom-width')
        self.ckb_width.connect("toggled", self.use_custom_width_toggled)
        hbox_.pack_start(self.ckb_width, True, True, 0)
        self.width_adjustments = [ Gtk.Adjustment(lower=0, upper=7680, step_increment=10, page_increment=100, page_size=0, value=600), # pixels
                                   Gtk.Adjustment(lower=0, upper=200, step_increment=1, page_increment=5, page_size=0, value=40),      # em
                                   Gtk.Adjustment(lower=0, upper=200, step_increment=1, page_increment=5, page_size=0, value=40),      # ch
                                   Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=5, page_size=0, value=40)]      # %
        self.sb_width = Gtk.SpinButton(name='entry-custom-width') # set the adjustment when we load the value from gsettings
        hbox_.pack_start(self.sb_width, True, True, 0)
        self.cbx_units_width = Gtk.ComboBoxText(name='combobox-custom-width-units')
        for u in range(len(self.valid_units)):
            self.cbx_units_width.insert(u, str(u), self.valid_units[u])
        self.cbx_units_width.set_active(0)
        hbox_.pack_start(self.cbx_units_width, True, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_hud_monitor = Gtk.Label(label=_("Attach HUD to: "), xalign=0, tooltip_text=_("Where to attach the HUD.\nDefault is to the current window.\nIf set to monitor, the HUD will try to avoid overlapping any panels."))
        hbox.pack_start(lbl_hud_monitor, True, True, 0)
        self.cbx_monitor = Gtk.ComboBoxText(name='combobox-hud-monitor')
        for u in range(len(HUD_DEFAULTS.VALID_MONITORS)):
            self.cbx_monitor.insert(u, str(u), HUD_DEFAULTS.VALID_MONITORS[u])
        hbox.pack_start(self.cbx_monitor, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_location = Gtk.Label(label=_("HUD location: "), xalign=0, tooltip_text=_("How to position the HUD in relation to what is attached to (window or monitor).\n'default' is north west for LTR languages and north east for RTL languages."))
        hbox.pack_start(lbl_location, True, True, 0)
        self.cbx_location = Gtk.ComboBoxText(name='combobox-location')
        for u in range(len(HUD_DEFAULTS.VALID_LOCATIONS)):
            self.cbx_location.insert(u, str(u), HUD_DEFAULTS.VALID_LOCATIONS[u])
        hbox.pack_start(self.cbx_location, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_separator = Gtk.Label(label=_("Menu Separator: "), xalign=0, tooltip_text=_("Character to separate the parts of the menu heirarchy in the HUD (RTL and LTR variants)"))
        hbox.pack_start(lbl_separator, True, True, 0)
        self.cbx_separator = Gtk.ComboBoxText(name='combobox-menu-separator')
        for u in range(len(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS)):
            self.cbx_separator.insert(u, str(u), HUD_DEFAULTS.VALID_SEPARATOR_PAIRS[u])
        hbox.pack_start(self.cbx_separator, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_recent_max = Gtk.Label(label=_("Max Recently Used Items: "), xalign=0, tooltip_text=_("Maximum number of recently used items to remember per application"))
        hbox.pack_start(lbl_recent_max, True, True, 0)
        adjustment = Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=10, page_size=0, value=0)
        self.sb_recent_max = Gtk.SpinButton(xalign=1, name='entry-recently-used-max', adjustment=adjustment)
        hbox.pack_start(self.sb_recent_max, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_recent_reset = Gtk.Label(label=_("Recently Used Item List: "), xalign=0, tooltip_text=_("Reset the recently used item list"))
        hbox.pack_start(lbl_recent_reset, True, True, 0)
        self.button_reset_recently_used = Gtk.Button(label=_("Reset"))
        self.button_reset_recently_used.connect("clicked", self.reset_recently_used)
        hbox.pack_start(self.button_reset_recently_used, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        box_outer.pack_start(box_main, True, True, 0)

        box_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        self.button_reset_to_defaults = Gtk.Button(label=_("Reset to defaults"))
        self.button_reset_to_defaults.connect("clicked", self.reset_to_defaults)
        box_buttons.pack_start(self.button_reset_to_defaults, True, True, 0)
        self.button_reset = Gtk.Button(label=_("Clear Changes"))
        self.button_reset.connect("clicked", self.reset_view)
        box_buttons.pack_start(self.button_reset, True, True, 0)
        self.button_apply = Gtk.Button(label=_("Apply Changes"))
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
        ## enough job indicating there was a change / issue
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
        """
        provider.load_from_data(css)

    def use_custom_menu_separator_toggled(self, button):
        use_cms = button.get_active()
        self.cbx_separator.set_editable(use_cms)
        self.cbx_separator.set_visible(use_cms)


    def use_custom_width_toggled(self, button):
        use_cw = button.get_active()
        self.sb_width.set_editable(use_cw)
        self.sb_width.set_visible(use_cw)
        self.cbx_units_width.set_visible(use_cw)

    def on_shortcut_clicked(self, widget):
        keystr = getkey_dialog.ask_for_key(previous_key=get_string('org.mate.hud', None, 'shortcut'), screen=widget.get_screen(), parent=widget.get_toplevel())
        if not keystr:
            return
        self.btn_shortcut.set_label(keystr)
        self.selection_changed(self.btn_shortcut)

    def reset_to_defaults(self, button):
        logging.info(_("Resetting all settings to default"))
        settings = Gio.Settings.new('org.mate.hud')
        keys = [ 'shortcut', 'hud-monitor', 'location', 'rofi-theme', 'menu-separator', 'custom-width', 'recently-used-max' ]
        for key in keys:
            settings.reset(key)

    def reset_recently_used(self, button):
        logging.info(_("Resetting recently used menu entry list"))
        Gio.Settings.new('org.mate.hud').reset('recently-used')

    def apply_changes(self, button):
        logging.info(_("Applying changes"))
        settings = Gio.Settings.new('org.mate.hud')
        settings.set_string('shortcut', self.btn_shortcut.get_label())

        settings.set_string('hud-monitor', self.cbx_monitor.get_active_text())

        settings.set_string('location', self.cbx_location.get_active_text())

        settings.set_string('rofi-theme', self.cbx_theme.get_active_text())

        settings.set_string('menu-separator', self.cbx_separator.get_active_text())

        if self.ckb_width.get_active():
            settings.set_string('custom-width', str(self.sb_width.get_value_as_int()) + self.cbx_units_width.get_active_text())
        else:
            settings.set_string('custom-width', '0')

        settings.set_int('recently-used-max', self.sb_recent_max.get_value_as_int())

        self.selection_changed_all()

    def selection_changed_all( self ):
        fields = [ self.cbx_shortcut, self.btn_shortcut, self.cbx_theme, self.ckb_width, self.sb_width, self.cbx_units_width, self.cbx_monitor, self.cbx_location, self.cbx_separator, self.sb_recent_max ]
        for f in fields:
            self.selection_changed( f )

    def shortcut_selector_changed( self, field ):
        use_custom = ( field.get_active_text() == _('Custom') + ': ' )
        if not use_custom:
            self.btn_shortcut.set_label(field.get_active_text())
            self.selection_changed(self.btn_shortcut)
        self.btn_shortcut.set_visible( use_custom )
        self.selection_changed(field)

    def selection_changed( self, field ):
        style_context = field.get_style_context()

        changed = False
        if field.get_name() == 'combobox-keyboard-shortcut' and field.get_active_text() == _('Custom') + ': ':
            field = self.btn_shortcut
        field_type =  type(field).__name__
        if field_type == 'Button':
            changed = ( field.get_label() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'SpinButton':
            changed = ( field.get_value_as_int() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'ComboBoxText' :
            changed = ( field.get_active_text() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'Entry' :
            changed = ( field.get_text() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        elif field_type == 'CheckButton' :
            changed = ( field.get_active() != getattr( HUDCurrentSettings(), self.widget_name_to_property_map.get( field.get_name() ) ) )
        if changed:
            style_context.add_class('changed')
            field.set_tooltip_text(_("Change not applied yet"))
        else:
            style_context.remove_class('changed')
            field.set_has_tooltip(False)
        
        if field.get_name() == 'combobox-custom-width-units': # and changed:
            logging.info( 'Changing width adjustment' )
            self.sb_width.set_adjustment( self.width_adjustments[ field.get_active() ] )

    def connect_to_signals(self):
        self.cbx_theme.connect("changed", self.selection_changed)
        self.ckb_width.connect("toggled", self.selection_changed )
        self.sb_width.connect("changed", self.selection_changed)
        self.cbx_units_width.connect("changed", self.selection_changed)
        self.cbx_monitor.connect("changed", self.selection_changed)
        self.cbx_location.connect("changed", self.selection_changed)
        self.cbx_separator.connect("changed", self.selection_changed)
        self.sb_recent_max.connect("value-changed", self.selection_changed)
        self.cbx_shortcut.connect("changed", self.shortcut_selector_changed)

    def reload_view_on_change(self, schema, key):
        logging.info( _("Reloading view in response to key change.") )
        self.reload_view(key=key)

    def reset_view(self, button):
        self.reload_view()

    def reload_view(self, key=None):
        logging.info(_("Reloading view") + ( " " + _('for') + " " + key if key else "" ) )

        if not key or key == 'shortcut':
            shortcut = get_string( 'org.mate.hud', None, 'shortcut' )
            if shortcut in self.single_modifier_keys:
                self.cbx_shortcut.set_active(self.single_modifier_keys.index(shortcut))
                self.btn_shortcut.set_visible(False)
            else:
                self.cbx_shortcut.set_active(self.single_modifier_keys.index(_('Custom') + ': '))
                self.btn_shortcut.set_visible(True)
            self.btn_shortcut.set_label( get_string( 'org.mate.hud', None, 'shortcut' ) )

        if not key or key == 'rofi-theme':
            themes = get_theme_list(sort=True)
            self.cbx_theme.remove_all()
            for u in range(len(themes)):
                self.cbx_theme.insert(u, str(u), themes[u])
            try:
                self.cbx_theme.set_active(themes.index(get_rofi_theme()))
            except:
                Gio.Settings.new('org.mate.hud').set_string('rofi-theme', HUD_DEFAULTS.THEME)
                self.cbx_theme.set_active(themes.index(HUD_DEFAULTS.THEME))

        if not key or key == 'custom-width':
            try:
                use_cw, w, u = get_custom_width()
            except:
                Gio.Settings.new('org.mate.hud').set_string('custom-width', '0')
            self.ckb_width.set_active(use_cw)
            self.sb_width.set_visible(use_cw)
            self.cbx_units_width.set_visible(use_cw)
            if use_cw:
                if u == self.cbx_units_width.get_active_text():
                    self.sb_width.set_value(int(w))
                self.sb_width.set_editable(use_cw)
                self.cbx_units_width.set_active(self.valid_units.index(u))
                self.sb_width.set_adjustment( self.width_adjustments[self.cbx_units_width.get_active()] )

        if not key or key == 'hud-monitor':
            self.cbx_monitor.set_active(HUD_DEFAULTS.VALID_MONITORS.index(get_monitor()))

        if not key or key == 'location':
            self.cbx_location.set_active(HUD_DEFAULTS.VALID_LOCATIONS.index(get_location()))

        if not key or key == 'menu-separator':
            self.cbx_separator.set_active(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS.index(get_menu_separator_pair()))

        if not key or key == 'recently-used-max':
            self.sb_recent_max.set_value(get_recently_used_max())

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
