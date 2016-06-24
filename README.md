# mate-hud

Provides a way to run menubar commands through `dmenu`, much like the
Unity 7 Heads-Up Display (HUD). `mate-hud` was originally forked from
`i3-hud-menu`:

  * https://jamcnaughton.com/2015/10/19/hud-for-xubuntu/
  * https://github.com/jamcnaughton/i3-hud-menu
  * https://github.com/RafaelBocquet/i3-hud-menu

## What is a HUD and why should I care?

A Heads-Up Display (HUD) allows you to search through an application's
appmenu. So if you’re trying to find that single filter in Gimp but
can't remember which filter category it fits into or if you can't
recall if preferences sits under File, Edit or Tools on your favourite
browser, you can just search for it rather than hunting through the
menus.

### Implementation

`mate-hud-service.py` is an implementation of the
`com.canonical.AppMenu.Registrar` DBus service. Applications exporting
their menu via `dbusmenu` need this service to run. `mate-hud.py`
tries to get the menu of the currently focused X11 window, lists
possible actions and asks the user which one to run.

`mate-hud.py`, should be bound to a keyboard shortcut such as `Ctrl
+ Alt + Space` or perhaps a panel icon.

## Setup

  * `mate-hud-service.py` should be started on session start-up.
  * The following should be added to the users `~/.profile` or `/etc/profile.d` or `/etc/X11/Xsession.d/`.

    export APPMENU_DISPLAY_BOTH=1
    if [ -n "$GTK_MODULES" ]
    then
      GTK_MODULES="$GTK_MODULES:unity-gtk-module"
    else
      GTK_MODULES="unity-gtk-module"
    fi
    
    if [ -z "$UBUNTU_MENUPROXY" ]
    then
      UBUNTU_MENUPROXY=1
    fi 

    export GTK_MODULES
    export UBUNTU_MENUPROXY

## Dependencies

  * `appmenu-qt`
  * `dmenu`
  * `python3`
  * `python3-dbus`
  * `python3-xlib`
  * `unity-gtk2-module`
  * `unity-gtk3-module`

## TODO

  * **[ DONE ]** Replace `xprop` with Python implementation.
  * Replace `dmenu` with [rofi](https://davedavenport.github.io/rofi/)
    * Automatically theme `rofi` based on the currently selected theme.

## Known Issues

  * May not be compatible to `topmenu-gtk`.