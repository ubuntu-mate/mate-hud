#!/usr/bin/env python3

import dbus
import os
import subprocess
import time
from Xlib import display, X, protocol, Xatom

class EWMH:
    """This class provides the ability to get and set properties defined by the EWMH spec.
    It was blanty ripped out of pyewmh
      * https://github.com/parkouss/pyewmh
    """
    
    NET_WM_WINDOW_TYPES = (
        '_NET_WM_WINDOW_TYPE_DESKTOP', '_NET_WM_WINDOW_TYPE_DOCK', '_NET_WM_WINDOW_TYPE_TOOLBAR', '_NET_WM_WINDOW_TYPE_MENU',
        '_NET_WM_WINDOW_TYPE_UTILITY', '_NET_WM_WINDOW_TYPE_SPLASH', '_NET_WM_WINDOW_TYPE_DIALOG', '_NET_WM_WINDOW_TYPE_DROPDOWN_MENU',
        '_NET_WM_WINDOW_TYPE_POPUP_MENU', '_NET_WM_WINDOW_TYPE_NOTIFICATION', '_NET_WM_WINDOW_TYPE_COMBO', '_NET_WM_WINDOW_TYPE_DND',
        '_NET_WM_WINDOW_TYPE_NORMAL')
    """List of strings representing all known window types."""
    
    NET_WM_ACTIONS = (
        '_NET_WM_ACTION_MOVE', '_NET_WM_ACTION_RESIZE', '_NET_WM_ACTION_MINIMIZE', '_NET_WM_ACTION_SHADE',
        '_NET_WM_ACTION_STICK', '_NET_WM_ACTION_MAXIMIZE_HORZ', '_NET_WM_ACTION_MAXIMIZE_VERT', '_NET_WM_ACTION_FULLSCREEN',
        '_NET_WM_ACTION_CHANGE_DESKTOP', '_NET_WM_ACTION_CLOSE', '_NET_WM_ACTION_ABOVE', '_NET_WM_ACTION_BELOW')
    """List of strings representing all known window actions."""
    
    NET_WM_STATES = (
        '_NET_WM_STATE_MODAL', '_NET_WM_STATE_STICKY', '_NET_WM_STATE_MAXIMIZED_VERT', '_NET_WM_STATE_MAXIMIZED_HORZ',
        '_NET_WM_STATE_SHADED', '_NET_WM_STATE_SKIP_TASKBAR', '_NET_WM_STATE_SKIP_PAGER', '_NET_WM_STATE_HIDDEN',
        '_NET_WM_STATE_FULLSCREEN','_NET_WM_STATE_ABOVE', '_NET_WM_STATE_BELOW', '_NET_WM_STATE_DEMANDS_ATTENTION')
    """List of strings representing all known window states."""
    
    def __init__(self, _display=None, root = None):
        self.display = _display or display.Display()
        self.root = root or self.display.screen().root
    
    def getActiveWindow(self):
        """Get the current active (toplevel) window or None (property _NET_ACTIVE_WINDOW)
        
        :return: Window object or None"""
        active_window = self._getProperty('_NET_ACTIVE_WINDOW')
        if active_window == None:
            return None

        return self._createWindow(active_window[0])

    def _getProperty(self, _type, win=None):
        if not win: win = self.root
        atom = win.get_full_property(self.display.get_atom(_type), X.AnyPropertyType)
        if atom: return atom.value
    
    def _setProperty(self, _type, data, win=None, mask=None):
        """Send a ClientMessage event to the root window"""
        if not win: win = self.root
        if type(data) is str:
            dataSize = 8
        else:
            data = (data+[0]*(5-len(data)))[:5]
            dataSize = 32
        
        ev = protocol.event.ClientMessage(window=win, client_type=self.display.get_atom(_type), data=(dataSize, data))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.root.send_event(ev, event_mask=mask)
    
    def _createWindow(self, wId):
        if not wId: return None
        return self.display.create_resource_object('window', wId)

"""
  format_label_list
"""
def format_label_list(label_list):
  head, *tail = label_list
  result = head
  for label in tail:
    result = result + ' > ' + label
  return result.replace('Root > ', '').replace('_', '')

"""
  try_appmenu_interface
"""
def try_appmenu_interface(window_id):
  # --- Get Appmenu Registrar DBus interface
  session_bus = dbus.SessionBus()
  appmenu_registrar_object = session_bus.get_object('com.canonical.AppMenu.Registrar', '/com/canonical/AppMenu/Registrar')
  appmenu_registrar_object_iface = dbus.Interface(appmenu_registrar_object, 'com.canonical.AppMenu.Registrar')

  # --- Get dbusmenu object path
  try:
    dbusmenu_bus, dbusmenu_object_path = appmenu_registrar_object_iface.GetMenuForWindow(window_id)
  except dbus.exceptions.DBusException:
    return

  # --- Access dbusmenu items
  dbusmenu_object = session_bus.get_object(dbusmenu_bus, dbusmenu_object_path)
  dbusmenu_object_iface = dbus.Interface(dbusmenu_object, 'com.canonical.dbusmenu')
  dbusmenu_items = dbusmenu_object_iface.GetLayout(0, -1, ["label"])

  dbusmenu_item_dict = dict()

  #For excluding items which have no action
  blacklist = []

  """ explore_dbusmenu_item """
  def explore_dbusmenu_item(item, label_list):
    item_id = item[0]
    item_props = item[1]

    item_children = item[2]

    if 'label' in item_props:
      new_label_list = label_list + [item_props['label']]
    else:
      new_label_list = label_list

    if len(item_children) == 0:
      if new_label_list not in blacklist:
        dbusmenu_item_dict[format_label_list(new_label_list)] = item_id
    else:
      blacklist.append(new_label_list)
      for child in item_children:
        explore_dbusmenu_item(child, new_label_list)

  explore_dbusmenu_item(dbusmenu_items[1], [])

  dmenuKeys = sorted(dbusmenu_item_dict.keys())

  # --- Run dmenu
  dmenu_string = ''
  head, *tail = dmenuKeys
  dmenu_string = head
  for m in tail:
    dmenu_string += '\n'
    dmenu_string += m

  dmenu_cmd = subprocess.Popen(['dmenu', '-i', '-l', '15'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  dmenu_cmd.stdin.write(dmenu_string.encode('utf-8'))
  dmenu_result = dmenu_cmd.communicate()[0].decode('utf8').rstrip()
  dmenu_cmd.stdin.close()

  # --- Use dmenu result
  if dmenu_result in dbusmenu_item_dict:
    action = dbusmenu_item_dict[dmenu_result]
    dbusmenu_object_iface.Event(action, 'clicked', 0, 0)


"""
  try_gtk_interface
"""
def try_gtk_interface(gtk_bus_name, gtk_object_path):
  # --- Ask for menus over DBus ---
  session_bus = dbus.SessionBus()
  gtk_menubar_object = session_bus.get_object(gtk_bus_name, gtk_object_path)
  gtk_menubar_object_iface = dbus.Interface(gtk_menubar_object, dbus_interface='org.gtk.Menus')
  gtk_action_object_actions_iface = dbus.Interface(gtk_menubar_object, dbus_interface='org.gtk.Actions')
  gtk_menubar_results = gtk_menubar_object_iface.Start([x for x in range(1024)])

  # --- Construct menu list ---
  gtk_menubar_menus = dict()
  for gtk_menubar_result in gtk_menubar_results:
    gtk_menubar_menus[(gtk_menubar_result[0], gtk_menubar_result[1])] = gtk_menubar_result[2]

  gtk_menubar_action_dict = dict()
 # gtk_menubar_target_dict = dict()

  """ explore_menu """
  def explore_menu(menu_id, label_list):
    if menu_id in gtk_menubar_menus:
      for menu in gtk_menubar_menus[menu_id]:
        if 'label' in menu:
          menu_label = menu['label']
          new_label_list = label_list + [menu_label]
          formatted_label = format_label_list(new_label_list)

          if 'action' in menu:
            menu_action = menu['action']
            if ':section' not in menu and ':submenu' not in menu:
              gtk_menubar_action_dict[formatted_label] = menu_action
            # if 'target' in menu:
             # menu_target = menu['target']
             # gtk_menubar_target_dict[formatted_label] = menu_target

        if ':section' in menu:
          menu_section = menu[':section']
          section_menu_id = (menu_section[0], menu_section[1])
          explore_menu(section_menu_id, label_list)

        if ':submenu' in menu:
          menu_submenu = menu[':submenu']
          submenu_menu_id = (menu_submenu[0], menu_submenu[1])
          explore_menu(submenu_menu_id, new_label_list)

  explore_menu((0,0), [])

  dmenuKeys = sorted(gtk_menubar_action_dict.keys())

  # --- Run dmenu
  dmenu_string = ''
  head, *tail = dmenuKeys
  dmenu_string = head
  for m in tail:
    dmenu_string += '\n'
    dmenu_string += m

  dmenu_cmd = subprocess.Popen(['dmenu', '-i', '-l', '15', '-fn', '"Ubuntu Regular-10.5"', '-nb', '#33322f', '-nf', '#cccccc', '-sf', '#cccccc', '-sb', '#87a752'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  dmenu_cmd.stdin.write(dmenu_string.encode('utf-8'))
  dmenu_result = dmenu_cmd.communicate()[0].decode('utf8').rstrip()
  dmenu_cmd.stdin.close()

  # --- Use dmenu result
  if dmenu_result in gtk_menubar_action_dict:
    action = gtk_menubar_action_dict[dmenu_result]
    # print('GTK Action :', action)
    gtk_action_object_actions_iface.Activate(action.replace('unity.', ''), [], dict())

if __name__ == "__main__":
  # Get Window properties and GTK MenuModel Bus name
  ewmh = EWMH()
  win = ewmh.getActiveWindow()
  window_id = hex(ewmh._getProperty('_NET_ACTIVE_WINDOW')[0])
  gtk_bus_name = ewmh._getProperty('_GTK_UNIQUE_BUS_NAME', win)
  gtk_object_path = ewmh._getProperty('_GTK_MENUBAR_OBJECT_PATH', win)
  print('Window id is :', window_id)
  print('_GTK_UNIQUE_BUS_NAME: ' + gtk_bus_name)
  print('_GTK_MENUBAR_OBJECT_PATH: ' + gtk_object_path)

  if (not gtk_bus_name) or (not gtk_object_path):
    print('Trying AppMenu')
    try_appmenu_interface(int(window_id, 16))
  else:
    print('Trying GTK interface')
    try_gtk_interface(gtk_bus_name, gtk_object_path)