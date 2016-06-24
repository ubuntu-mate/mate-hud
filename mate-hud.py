#!/usr/bin/env python3

import dbus
import os
import subprocess
import time
from Xlib import display, X, protocol, Xatom

class EWMH:
    """This class provides the ability to get and set properties defined by the EWMH spec.
    
    Each property can be accessed in two ways. For example, to get the active window::

      win = ewmh.getActiveWindow()
      # or: win = ewmh.getProperty('_NET_ACTIVE_WINDOW')
    
    Similarly, to set the active window::

      ewmh.setActiveWindow(myWindow)
      # or: ewmh.setProperty('_NET_ACTIVE_WINDOW', myWindow)
    
    When a property is written, don't forget to really send the notification by flushing requests::

      ewmh.display.flush()
    
    :param _display: the display to use. If not given, Xlib.display.Display() is used.
    :param root: the root window to use. If not given, self.display.screen().root is used."""
    
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
        self.__getAttrs = {
            '_NET_CLIENT_LIST':         self.getClientList,
            '_NET_CLIENT_LIST_STACKING':    self.getClientListStacking,
            '_NET_NUMBER_OF_DESKTOPS':  self.getNumberOfDesktops,
            '_NET_DESKTOP_GEOMETRY':    self.getDesktopGeometry,
            '_NET_DESKTOP_VIEWPORT':    self.getDesktopViewPort,
            '_NET_CURRENT_DESKTOP':     self.getCurrentDesktop,
            '_NET_ACTIVE_WINDOW':       self.getActiveWindow,
            '_NET_WORKAREA':        self.getWorkArea,
            '_NET_SHOWING_DESKTOP':     self.getShowingDesktop,
            '_NET_WM_NAME':         self.getWmName,
            '_NET_WM_VISIBLE_NAME':     self.getWmVisibleName,
            '_NET_WM_DESKTOP':      self.getWmDesktop,
            '_NET_WM_WINDOW_TYPE':      self.getWmWindowType,
            '_NET_WM_STATE':        self.getWmState, 
            '_NET_WM_ALLOWED_ACTIONS':  self.getWmAllowedActions,
            '_NET_WM_PID':          self.getWmPid,
        }
        self.__setAttrs = {
            '_NET_NUMBER_OF_DESKTOPS':  self.setNumberOfDesktops,
            '_NET_DESKTOP_GEOMETRY':    self.setDesktopGeometry,
            '_NET_DESKTOP_VIEWPORT':    self.setDesktopViewport,
            '_NET_CURRENT_DESKTOP':     self.setCurrentDesktop,
            '_NET_ACTIVE_WINDOW':       self.setActiveWindow,
            '_NET_SHOWING_DESKTOP':     self.setShowingDesktop,
            '_NET_CLOSE_WINDOW':        self.setCloseWindow,
            '_NET_MOVERESIZE_WINDOW':   self.setMoveResizeWindow,
            '_NET_WM_NAME':         self.setWmName,
            '_NET_WM_VISIBLE_NAME':     self.setWmVisibleName,
            '_NET_WM_DESKTOP':      self.setWmDesktop,
            '_NET_WM_STATE':        self.setWmState, 
        }
    
    # ------------------------ setters properties ------------------------
    
    def setNumberOfDesktops(self, nb):
        """Set the number of desktops (property _NET_NUMBER_OF_DESKTOPS).
        
        :param nb: the number of desired desktops"""
        self._setProperty('_NET_NUMBER_OF_DESKTOPS', [nb])
    
    def setDesktopGeometry(self, w, h):
        """Set the desktop geometry (property _NET_DESKTOP_GEOMETRY)
        
        :param w: desktop width
        :param h: desktop height"""
        self._setProperty('_NET_DESKTOP_GEOMETRY', [w, h])
    
    def setDesktopViewport(self, w, h):
        """Set the viewport size of the current desktop (property _NET_DESKTOP_VIEWPORT)
        
        :param w: desktop width
        :param h: desktop height"""
        self._setProperty('_NET_DESKTOP_VIEWPORT', [w, h])
    
    def setCurrentDesktop(self, i):
        """Set the current desktop (property _NET_CURRENT_DESKTOP).
        
        :param i: the desired desktop number"""
        self._setProperty('_NET_CURRENT_DESKTOP', [i, X.CurrentTime])
    
    def setActiveWindow(self, win):
        """Set the given window active (property _NET_ACTIVE_WINDOW)
        
        :param win: the window object"""
        self._setProperty('_NET_ACTIVE_WINDOW', [1, X.CurrentTime, win.id], win)
    
    def setShowingDesktop(self, show):
        """Set/unset the mode Showing desktop (property _NET_SHOWING_DESKTOP)
        
        :param show: 1 to set the desktop mode, else 0"""
        self._setProperty('_NET_SHOWING_DESKTOP', [show])
    
    def setCloseWindow(self, win):
        """Colse the given window (property _NET_CLOSE_WINDOW)
        
        :param win: the window object"""
        self._setProperty('_NET_CLOSE_WINDOW', [int(time.mktime(time.localtime())), 1], win)
    
    def setWmName(self, win, name):
        """Set the property _NET_WM_NAME
        
        :param win: the window object
        :param name: desired name"""
        self._setProperty('_NET_WM_NAME', name, win)
    
    def setWmVisibleName(self, win, name):
        """Set the property _NET_WM_VISIBLE_NAME
        
        :param win: the window object
        :param name: desired visible name"""
        self._setProperty('_NET_WM_VISIBLE_NAME', name, win)
    
    def setWmDesktop(self, win, i):
        """Move the window to the desired desktop by changing the property _NET_WM_DESKTOP.
        
        :param win: the window object
        :param i: desired desktop number"""
        self._setProperty('_NET_WM_DESKTOP', [i, 1], win)
    
    def setMoveResizeWindow(self, win, gravity=0, x=None, y=None, w=None, h=None):
        """Set the property _NET_MOVERESIZE_WINDOW to move or resize the given window.
        Flags are automatically calculated if x, y, w or h are defined.
        
        :param win: the window object
        :param gravity: gravity (one of the Xlib.X.*Gravity constant or 0)
        :param x: int or None
        :param y: int or None
        :param w: int or None
        :param h: int or None"""
        gravity_flags = gravity | 0b0000100000000000 # indicate source (application)
        if x is None: x = 0
        else: gravity_flags = gravity_flags | 0b0000010000000000 # indicate presence of x
        if y is None: y = 0
        else: gravity_flags = gravity_flags | 0b0000001000000000 # indicate presence of y
        if w is None: w = 0
        else: gravity_flags = gravity_flags | 0b0000000100000000 # indicate presence of w
        if h is None: h = 0
        else: gravity_flags = gravity_flags | 0b0000000010000000 # indicate presence of h
        self._setProperty('_NET_MOVERESIZE_WINDOW', [gravity_flags, x, y, w, h], win)
    
    def setWmState(self, win, action, state, state2=0):
        """Set/unset one or two state(s) for the given window (property _NET_WM_STATE).
        
        :param win: the window object
        :param action: 0 to remove, 1 to add or 2 to toggle state(s)
        :param state: a state
        :type state: int or str (see :attr:`NET_WM_STATES`)
        :param state2: a state or 0
        :type state2: int or str (see :attr:`NET_WM_STATES`)"""
        if type(state) != int: state = self.display.get_atom(state, 1)
        if type(state2) != int: state2 = self.display.get_atom(state2, 1)
        self._setProperty('_NET_WM_STATE', [action, state, state2, 1], win)
    
    # ------------------------ getters properties ------------------------
    
    def getClientList(self):
        """Get the list of windows maintained by the window manager for the property
        _NET_CLIENT_LIST.
        
        :return: list of Window objects"""
        return map(self._createWindow, self._getProperty('_NET_CLIENT_LIST'))
    
    def getClientListStacking(self):
        """Get the list of windows maintained by the window manager for the property
        _NET_CLIENT_LIST_STACKING.
        
        :return: list of Window objects"""
        return map(self._createWindow, self._getProperty('_NET_CLIENT_LIST_STACKING'))
    
    def getNumberOfDesktops(self):
        """Get the number of desktops (property _NET_NUMBER_OF_DESKTOPS).
        
        :return: int"""
        return self._getProperty('_NET_NUMBER_OF_DESKTOPS')[0]
    
    def getDesktopGeometry(self):
        """Get the desktop geometry (property _NET_DESKTOP_GEOMETRY) as an array
        of two integers [width, height].
        
        :return: [int, int]"""
        return self._getProperty('_NET_DESKTOP_GEOMETRY')
    
    def getDesktopViewPort(self):
        """Get the current viewports of each desktop as a list of [x, y] representing
                the top left corner (property _NET_DESKTOP_VIEWPORT).
        
        :return: list of [int, int]"""
        return self._getProperty('_NET_DESKTOP_VIEWPORT')
    
    def getCurrentDesktop(self):
        """Get the current desktop number (property _NET_CURRENT_DESKTOP)
        
        :return: int"""
        return self._getProperty('_NET_CURRENT_DESKTOP')[0]
    
    def getActiveWindow(self):
        """Get the current active (toplevel) window or None (property _NET_ACTIVE_WINDOW)
        
        :return: Window object or None"""
        active_window = self._getProperty('_NET_ACTIVE_WINDOW')
        if active_window == None:
            return None

        return self._createWindow(active_window[0])
    
    def getWorkArea(self):
        """Get the work area for each desktop (property _NET_WORKAREA) as a list of [x, y, width, height]
        
        :return: a list of [int, int, int, int]"""
        return self._getProperty('_NET_WORKAREA')
    
    def getShowingDesktop(self):
        """Get the value of "showing the desktop" mode of the window manager (property _NET_SHOWING_DESKTOP).
        1 means the mode is activated, and 0 means deactivated.
        
        :return: int"""
        return self._getProperty('_NET_SHOWING_DESKTOP')[0]
    
    def getWmName(self, win):
        """Get the property _NET_WM_NAME for the given window as a string.
        
        :param win: the window object
        :return: str"""
        return self._getProperty('_NET_WM_NAME', win)
    
    def getWmVisibleName(self, win):
        """Get the property _NET_WM_VISIBLE_NAME for the given window as a string.
        
        :param win: the window object
        :return: str"""
        return self._getProperty('_NET_WM_VISIBLE_NAME', win)
    
    def getWmDesktop(self, win):
        """Get the current desktop number of the given window (property _NET_WM_DESKTOP).
        
        :param win: the window object
        :return: int"""
        return self._getProperty('_NET_WM_DESKTOP', win)[0]
    
    def getWmWindowType(self, win, str=False):
        """Get the list of window types of the given window (property _NET_WM_WINDOW_TYPE).
        
        :param win: the window object
        :param str: True to get a list of string types instead of int
        :return: list of (int|str)"""
        types = self._getProperty('_NET_WM_WINDOW_TYPE', win)
        if not str: return types
        return map(self._getAtomName, types)
    
    def getWmState(self, win, str=False):
        """Get the list of states of the given window (property _NET_WM_STATE).
        
        :param win: the window object
        :param str: True to get a list of string states instead of int
        :return: list of (int|str)"""
        states = self._getProperty('_NET_WM_STATE', win)
        if not str: return states
        return map(self._getAtomName, states)
    
    def getWmAllowedActions(self, win, str=False):
        """Get the list of allowed actions for the given window (property _NET_WM_ALLOWED_ACTIONS).
        
        :param win: the window object
        :param str: True to get a list of string allowed actions instead of int
        :return: list of (int|str)"""
        wAllowedActions = self._getProperty('_NET_WM_ALLOWED_ACTIONS', win)
        if not str: return wAllowedActions  
        return map(self._getAtomName, wAllowedActions)
    
    def getWmPid(self, win):
        """Get the pid of the application associated to the given window (property _NET_WM_PID)
        
        :param win: the window object"""
        return self._getProperty('_NET_WM_PID', win)[0]
    
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
    
    def _getAtomName(self, atom):
        try: return self.display.get_atom_name(atom)
        except: return 'UNKNOWN'
    
    def _createWindow(self, wId):
        if not wId: return None
        return self.display.create_resource_object('window', wId)

    def getReadableProperties(self):
        """Get all the readable properties' names"""
        return self.__getAttrs.keys()

    def getProperty(self, prop, *args, **kwargs):
        """Get the value of a property. See the corresponding method for the required arguments.
        For example, for the property _NET_WM_STATE, look for :meth:`getWmState`"""
        f = self.__getAttrs.get(prop)
        if not f: raise KeyError('Unknown readable property: %s' % prop)
        return f(self, *args, **kwargs)
    
    def getWritableProperties(self):
        """Get all the writable properties names"""
        return self.__setAttrs.keys()
    
    def setProperty(self, prop, *args, **kwargs):
        """Set the value of a property by sending an event on the root window. See the corresponding method for
        the required arguments. For example, for the property _NET_WM_STATE, look for :meth:`setWmState`"""
        f = self.__setAttrs.get(prop)
        if not f: raise KeyError('Unknown writable property: %s' % prop)
        f(self, *args, **kwargs)



"""
  format_label_list
"""
def format_label_list(label_list):
  head, *tail = label_list
  result = head
  for label in tail:
    result = result + " > " + label
  result = result.replace("Root > ", "")
  result = result.replace("_", "")
  return result

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