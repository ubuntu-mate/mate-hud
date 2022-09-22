#!/usr/bin/python3

import gi
import logging
import os.path
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
    def monitor(self):
        return get_string( 'org.mate.hud', None, 'hud-monitor' )

    @property
    def recently_used_max(self):
        return get_number( 'org.mate.hud', None, 'recently-used-max' )

    @property
    def menu_separator(self):
        return get_string( 'org.mate.hud', None, 'menu-separator' )

    @property
    def use_prompt(self):
        return get_string( 'org.mate.hud', None, 'prompt' ) != ''

    @property
    def prompt(self):
        return get_string( 'org.mate.hud', None, 'prompt' )

    @property
    def transparency(self):
        return get_number( 'org.mate.hud', None, 'transparency' )
    # Add new properties here that return the current value of a gsettings key

class HUDSettingsWindow(Gtk.Window):
    # Add 'widget-name': 'HUDCurrentSettings property name' when adding a new option
    widget_property_map = {
        'shortcut':        'shortcut',
        'custom-shortcut': 'shortcut',
        'theme':           'rofi_theme',
        'use-width':       'use_custom_width',
        'width':           'custom_width',
        'width-units':     'custom_width_units',
        'monitor':         'monitor',
        'location':        'location',
        'separator':       'menu_separator',
        'recently-used':   'recently_used_max',
        'use-prompt':      'use_prompt',
        'prompt':          'prompt',
        'transparency':    'transparency'
    }

    widget_signal_map = {
    #   widget:                [ signal,          function_name ]
        'theme':               [ "changed",       'selection_changed' ],
        'use-width':           [ "toggled",       'use_custom_width_toggled' ],
        'width':               [ "changed",       'selection_changed' ],
        'width-units':         [ "changed",       'selection_changed' ],
        'monitor':             [ "changed",       'selection_changed' ],
        'location':            [ "changed",       'selection_changed' ],
        'separator':           [ "changed",       'selection_changed' ],
        'recently-used':       [ "value-changed", 'selection_changed' ],
        'use-prompt':          [ "toggled",       'use_prompt_toggled' ],
        'prompt':              [ "changed",       'selection_changed' ],
        'shortcut':            [ "changed",       'shortcut_selector_changed' ],
        'custom-shortcut':     [ "clicked",       'on_shortcut_clicked' ],
        'transparency':        [ "value-changed", 'selection_changed' ],
        'reset-recently-used': [ "clicked",       'reset_recently_used' ],
        'reset-to-defaults':   [ "clicked",       'reset_to_defaults' ],
        'reset':               [ "clicked",       'reset_view' ],
        'apply-changes':       [ "clicked",       'apply_changes' ]
    }


    # I guess if there are ever widgets that don't correespond to a property, we would
    # have to write this out, but for now this works fine
    widget_names = list( widget_property_map.keys() )

    # Add new gsettings options here if we provide fields to change them
    # A changed listener will be set up with a callback to reload_view_on_change
    keys = [ 'shortcut',
             'hud-monitor',
             'location',
             'rofi-theme',
             'menu-separator',
             'custom-width',
             'recently-used-max',
             'prompt' ]

    valid_units = [ 'px', 'em', 'ch', '%' ]
    single_modifier_keys = [ 'Alt_L', 'Alt_R', 'Ctrl_L', 'Ctrl_R', 'Super_L', 'Super_R' ]

    def __init__(self):
        super().__init__(title="HUD Settings")
        self.add_custom_css_classes()
        self.set_border_width(10)
        self.set_resizable(False)
        self.set_icon_name("mate-hud")

        box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=50)
        self.add(box_outer)

        box_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_shortcut = Gtk.Label(label=_("Keyboard Shortcut: "), xalign=0,
                                 tooltip_text=_("Keyboard shortcut to activate the HUD"))
        hbox.pack_start(lbl_shortcut, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cbx_shortcut = Gtk.ComboBoxText(name='shortcut')
        for u in range(len(self.single_modifier_keys)):
            cbx_shortcut.insert(u, str(u), self.single_modifier_keys[u])
        cbx_shortcut.insert(len(self.single_modifier_keys), str(len(self.single_modifier_keys)), _("Custom: "))
        hbox_.pack_start(cbx_shortcut, False, True, 0)
        btn_shortcut = Gtk.Button(name='custom-shortcut')
        hbox_.pack_start(btn_shortcut, False, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_theme = Gtk.Label(label=_("HUD Theme: "), xalign=0,
                              tooltip_text=_("HUD theme. Default is 'mate-hud-rounded'\n" + \
                                             "The mate-hud* themes attempt to match the system font and colors from the GTK theme."))
        hbox.pack_start(lbl_theme, True, True, 0)
        cbx_theme = Gtk.ComboBoxText(name='theme')
        hbox.pack_start(cbx_theme, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_prompt = Gtk.Label(label=_("HUD Prompt: "), xalign=0,
                              tooltip_text=_("HUD prompt. Default is 'HUD' localized if possible."))
        hbox.pack_start(lbl_prompt, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ckb_prompt = Gtk.CheckButton(name='use-prompt')
        hbox_.pack_start(ckb_prompt, True, True, 0)
        entry_prompt = Gtk.Entry(name='prompt')
        entry_prompt.set_placeholder_text(HUD_DEFAULTS.PROMPT)
        hbox_.pack_start(entry_prompt, False, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_width = Gtk.Label(label=_("Custom Width: "), xalign=0,
                              tooltip_text=_("Override the width of the HUD specified in the theme"))
        hbox.pack_start(lbl_width, True, True, 0)
        hbox_ = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ckb_width = Gtk.CheckButton(name='use-width')
        hbox_.pack_start(ckb_width, True, True, 0)
        self.width_adjustments = {
            'px': Gtk.Adjustment(lower=0, upper=7680, step_increment=10, page_increment=100, page_size=0, value=600),
            'em': Gtk.Adjustment(lower=0, upper=200, step_increment=1, page_increment=5, page_size=0, value=40),
            'ch': Gtk.Adjustment(lower=0, upper=200, step_increment=1, page_increment=5, page_size=0, value=40),
            '%':  Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=5, page_size=0, value=40)
        }
        sb_width = Gtk.SpinButton(name='width') # set the adjustment when we load the value from gsettings
        hbox_.pack_start(sb_width, True, True, 0)
        cbx_units_width = Gtk.ComboBoxText(name='width-units')
        for u in range(len(self.valid_units)):
            cbx_units_width.insert(u, str(u), self.valid_units[u])
        cbx_units_width.set_active(0)
        hbox_.pack_start(cbx_units_width, True, True, 0)
        hbox.pack_start(hbox_, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_monitor = Gtk.Label(label=_("Attach HUD to: "), xalign=0,
                                    tooltip_text=_("Where to attach the HUD.\nDefault is to the current window.\n" +
                                                   "If set to monitor, the HUD will try to avoid overlapping any panels."))
        hbox.pack_start(lbl_monitor, True, True, 0)
        cbx_monitor = Gtk.ComboBoxText(name='monitor')
        for u in range(len(HUD_DEFAULTS.VALID_MONITORS)):
            cbx_monitor.insert(u, str(u), HUD_DEFAULTS.VALID_MONITORS[u])
        hbox.pack_start(cbx_monitor, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_location = Gtk.Label(label=_("HUD location: "), xalign=0,
                                 tooltip_text=_("How to position the HUD in relation to what is attached to (window or monitor).\n" + \
                                                "'default' is north west for LTR languages and north east for RTL languages."))
        hbox.pack_start(lbl_location, True, True, 0)
        cbx_location = Gtk.ComboBoxText(name='location')
        for u in range(len(HUD_DEFAULTS.VALID_LOCATIONS)):
            cbx_location.insert(u, str(u), HUD_DEFAULTS.VALID_LOCATIONS[u])
        hbox.pack_start(cbx_location, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_separator = Gtk.Label(label=_("Menu Separator: "), xalign=0,
                                  tooltip_text=_("Character to separate the parts of the menu heirarchy in the HUD (RTL and LTR variants)"))
        hbox.pack_start(lbl_separator, True, True, 0)
        cbx_separator = Gtk.ComboBoxText(name='separator')
        for u in range(len(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS)):
            cbx_separator.insert(u, str(u), HUD_DEFAULTS.VALID_SEPARATOR_PAIRS[u])
        hbox.pack_start(cbx_separator, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_transparency = Gtk.Label(label=_("Transparency: "), xalign=0,
                                   tooltip_text=_("Transparency of the HUD window\n" + \
                                                  "  0: Completely transparent\n" + \
                                                  "100: Solid color"))
        hbox.pack_start(lbl_transparency, True, True, 0)
        adjustment = Gtk.Adjustment(lower=0, upper=100, step_increment=1, page_increment=5, page_size=0, value=0)
        sb_transparency = Gtk.SpinButton(xalign=1, name='transparency', adjustment=adjustment)
        hbox.pack_start(sb_transparency, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_recent_max = Gtk.Label(label=_("Max Recently Used Items: "), xalign=0,
                                   tooltip_text=_("Maximum number of recently used items to remember per application\n" + \
                                                  " 0: Don't save recently used items\n" + \
                                                  "-1: save unlimited recently used items"))
        hbox.pack_start(lbl_recent_max, True, True, 0)
        adjustment = Gtk.Adjustment(lower=-1, upper=100, step_increment=1, page_increment=10, page_size=0, value=0)
        sb_recent_max = Gtk.SpinButton(xalign=1, name='recently-used', adjustment=adjustment)
        hbox.pack_start(sb_recent_max, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        lbl_recent_reset = Gtk.Label(label=_("Recently Used Item List: "), xalign=0,
                                     tooltip_text=_("Reset the recently used item list"))
        hbox.pack_start(lbl_recent_reset, True, True, 0)
        btn_reset_recently_used = Gtk.Button(name='reset-recently-used', label=_("Reset"))
        hbox.pack_start(btn_reset_recently_used, False, True, 0)
        box_main.pack_start(hbox, True, True, 0)

        box_outer.pack_start(box_main, True, True, 0)

        box_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        btn_reset_to_defaults = Gtk.Button(name='reset-to-defaults', label=_("Reset to defaults"))
        box_buttons.pack_start(btn_reset_to_defaults, True, True, 0)
        btn_reset = Gtk.Button(name='reset', label=_("Clear Changes"))
        box_buttons.pack_start(btn_reset, True, True, 0)
        btn_apply = Gtk.Button(name='apply-changes', label=_("Apply Changes"))
        box_buttons.pack_start(btn_apply, False, True, 0)
        box_outer.pack_start(box_buttons, True, True, 0)

    def show_all(self):
        super().show_all()
        self.reload_view()
        # Connect to the widget changed signals after we load the view
        # and establish the widget's initial values. Otherwise, the we'll
        # be responding to change signals as we load the initial state
        self.connect_to_signals()

    def add_custom_css_classes(self):
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        color = rgba_to_hex(style_context.lookup_color('theme_selected_bg_color')[1])
        css = bytes("""
        entry.changed,
        combobox.changed button.combo,
        comboboxtext.changed button.combo,
        button.changed,
        spinbutton.changed entry,
        checkbutton.changed check {
            border: solid #1fced2;
            border-width: 2px;
        }
        """.replace('#1fced2', color).encode('utf-8'))
        provider.load_from_data(css)

    def get_widget_by_name(self, name, root=None):
        if not root: root = self.get_toplevel()
        if root.get_name() == name:
            return root
        try:
            widgets = root.get_children()
        except:
            widgets = []
        for w in widgets:
            if str(w.get_name()) == name:
                return w
            try:
                children = w.get_children()
            except:
                children = []
            for y in children:
                z = self.get_widget_by_name( name, root=y )
                if z: return z
        return None

    def use_custom_width_toggled(self, button):
        use_cw = button.get_active()
        self.get_widget_by_name('width').set_visible(use_cw)
        self.get_widget_by_name('width-units').set_visible(use_cw)
        self.selection_changed(button)
        self.selection_changed(self.get_widget_by_name('width'))
        self.selection_changed(self.get_widget_by_name('width-units'))

    def use_prompt_toggled(self, button):
        self.get_widget_by_name('prompt').set_visible(button.get_active())
        self.selection_changed(button)
        self.selection_changed(self.get_widget_by_name('prompt'))

    def recent_max_update_tooltip(self):
        w = self.get_widget_by_name('recently-used')
        recent_max = w.get_value_as_int()
        if recent_max == HUD_DEFAULTS.RECENTLY_USED_UNLIMITED:
            w.set_tooltip_text(_('Unlimited'))
        elif recent_max == HUD_DEFAULTS.RECENTLY_USED_NONE:
            w.set_tooltip_text(_("Don't save or show recently used menu items"))
        else:
            w.set_has_tooltip(False)

    def on_shortcut_clicked(self, widget):
        keystr = getkey_dialog.ask_for_key(
            previous_key=get_string('org.mate.hud', None, 'shortcut'),
            screen=widget.get_screen(),
            parent=widget.get_toplevel()
        )
        if not keystr:
            return
        w = self.get_widget_by_name('custom-shortcut')
        w.set_label(keystr)
        self.selection_changed(w)

    def reset_to_defaults(self, button):
        logging.info(_("Resetting all settings to default"))
        settings = Gio.Settings.new('org.mate.hud')
        for key in self.keys:
            settings.reset(key)

    def reset_recently_used(self, button):
        logging.info(_("Resetting recently used menu entry list"))
        Gio.Settings.new('org.mate.hud').reset('recently-used')

    def apply_changes(self, button):
        logging.info(_("Applying changes"))

        settings = Gio.Settings.new('org.mate.hud')
        settings.set_string( 'shortcut',          self.get_widget_by_name('custom-shortcut').get_label())
        settings.set_string( 'hud-monitor',       self.get_widget_by_name('monitor').get_active_text())
        settings.set_string( 'location',          self.get_widget_by_name('location').get_active_text())
        settings.set_string( 'rofi-theme',        self.get_widget_by_name('theme').get_active_text())
        settings.set_string( 'menu-separator',    self.get_widget_by_name('separator').get_active_text())
        settings.set_int(    'recently-used-max', self.get_widget_by_name('recently-used').get_value_as_int())
        settings.set_int(    'transparency',      self.get_widget_by_name('transparency').get_value_as_int())
        if self.get_widget_by_name('use-prompt').get_active():
            settings.set_string( 'prompt',        self.get_widget_by_name('prompt').get_text())
        else:
            settings.set_string( 'prompt',        '')

        if self.get_widget_by_name('use-width').get_active():
            settings.set_string('custom-width', \
                                str(self.get_widget_by_name('width').get_value_as_int()) + \
                                self.get_widget_by_name('width-units').get_active_text())
        else: # Default is use the theme width (no custom width, so apply that if the checkbutton isn't checked
            settings.set_string('custom-width', HUD_DEFAULTS.CUSTOM_WIDTH)

        self.selection_changed_all()

    def selection_changed_all( self ):
        for name in self.widget_names:
            widget = self.get_widget_by_name( name )
            if widget: self.selection_changed( widget )

    def shortcut_selector_changed( self, widget ):
        use_custom = ( widget.get_active_text() == _('Custom') + ': ' )
        custom_shortcut_btn = self.get_widget_by_name( 'custom-shortcut' )
        if not use_custom:
            custom_shortcut_btn.set_label(widget.get_active_text())
            self.selection_changed(custom_shortcut_btn)
        custom_shortcut_btn.set_visible( use_custom )
        self.selection_changed(widget)

    def selection_changed( self, widget ):
        style_context = widget.get_style_context()

        if widget.get_name() == 'shortcut' and widget.get_active_text() == _('Custom') + ': ':
            widget = self.get_widget_by_name( 'custom-shortcut' )
        widget_type =  type(widget).__name__
        current_value = getattr( HUDCurrentSettings(), self.widget_property_map.get( widget.get_name() ) )
        displayed_value = current_value # assume not changed, til we get the value
        if   widget_type == 'Button':       displayed_value = widget.get_label()
        elif widget_type == 'SpinButton':   displayed_value = widget.get_value_as_int()
        elif widget_type == 'ComboBoxText': displayed_value = widget.get_active_text()
        elif widget_type == 'Entry':        displayed_value = widget.get_text()
        elif widget_type == 'CheckButton':  displayed_value = widget.get_active()
        changed = ( current_value != displayed_value )
        if changed:
            style_context.add_class('changed')
            widget.set_tooltip_text(_("Change not applied yet"))
        else:
            style_context.remove_class('changed')
            widget.set_has_tooltip(False)
        if widget.get_name() == 'recently-used':
            self.recent_max_update_tooltip()
        if widget.get_name() == 'width-units': # and changed:
            logging.info( 'Changing width adjustment' )
            self.get_widget_by_name('width').set_adjustment( self.width_adjustments[ widget.get_active_text() ] )

    def connect_to_signals(self):
        names = self.widget_signal_map.keys()
        for name in names:
            signal, function = self.widget_signal_map[name]
            self.get_widget_by_name(name).connect( signal, getattr( self, function ) )

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
                self.get_widget_by_name('shortcut').set_active(self.single_modifier_keys.index(shortcut))
                self.get_widget_by_name('custom-shortcut').set_visible(False)
            else:
                # The shortcut combobox has all the single modifiers, then 'Custom: '
                self.get_widget_by_name('shortcut').set_active(len(self.single_modifier_keys))
                self.get_widget_by_name('custom-shortcut').set_visible(True)
            self.get_widget_by_name('custom-shortcut').set_label( get_string( 'org.mate.hud', None, 'shortcut' ) )

        if not key or key == 'rofi-theme':
            themes = get_theme_list(sort=True)
            widget = self.get_widget_by_name('theme')
            widget.remove_all()
            for u in range(len(themes)):
                widget.insert(u, str(u), themes[u])
            try:
                widget.set_active(themes.index(get_rofi_theme()))
            except:
                Gio.Settings.new('org.mate.hud').set_string('rofi-theme', HUD_DEFAULTS.THEME)
                widget.set_active(themes.index(HUD_DEFAULTS.THEME))

        if not key or key == 'custom-width':
            try:
                use_width, width, units = get_custom_width()
            except:
                Gio.Settings.new('org.mate.hud').set_string('custom-width', HUD_DEFAULTS.CUSTOM_WIDTH)
                use_width, width, units = get_custom_width()

            widget_use = self.get_widget_by_name('use-width')
            widget_width = self.get_widget_by_name('width')
            widget_units = self.get_widget_by_name('width-units')
            widget_use.set_active(use_width)
            widget_width.set_visible(use_width)
            widget_units.set_visible(use_width)
            if use_width:
                if units == widget_units.get_active_text():
                    widget_width.set_value(int(width))
                widget_units.set_active(self.valid_units.index(units))
                widget_width.set_adjustment( self.width_adjustments[self.get_widget_by_name('width-units').get_active_text()] )

        if not key or key == 'prompt':
            use_prompt = HUDCurrentSettings().use_prompt
            self.get_widget_by_name('use-prompt').set_active(use_prompt)
            self.get_widget_by_name('prompt').set_text( HUDCurrentSettings().prompt )
            self.get_widget_by_name('prompt').set_visible( use_prompt )

        if not key or key == 'hud-monitor':
            self.get_widget_by_name('monitor').set_active(HUD_DEFAULTS.VALID_MONITORS.index(get_monitor()))

        if not key or key == 'location':
            self.get_widget_by_name('location').set_active(HUD_DEFAULTS.VALID_LOCATIONS.index(get_location()))

        if not key or key == 'menu-separator':
            self.get_widget_by_name('separator').set_active(HUD_DEFAULTS.VALID_SEPARATOR_PAIRS.index(get_menu_separator_pair()))

        if not key or key == 'recently-used-max':
            self.get_widget_by_name('recently-used').set_value(get_recently_used_max())
            self.recent_max_update_tooltip()

        if not key or key == 'transparency':
            self.get_widget_by_name('transparency').set_value(get_transparency())

if __name__ == "__main__":
    setproctitle.setproctitle('hud-settings')
    logging.basicConfig(level=logging.INFO)

    win = HUDSettingsWindow()
    win.connect("destroy", Gtk.main_quit)
    settings = Gio.Settings.new("org.mate.hud")
    for k in win.keys:
        settings.connect("changed::" + k, win.reload_view_on_change)

    win.show_all()
    Gtk.main()
