# mate-hud

Provides a way to run menubar commands through
[rofi](https://github.com/davatorium/rofi), much like the Unity 7
Heads-Up Display (HUD). `mate-hud` was originally forked from
`i3-hud-menu`:

  * https://jamcnaughton.com/2015/10/19/hud-for-xubuntu/
  * https://github.com/jamcnaughton/i3-hud-menu
  * https://github.com/RafaelBocquet/i3-hud-menu

It was subsequently improved by incorporating improvements from
[snippins](https://gist.github.com/snippins)

  * [HUD.py](https://gist.github.com/snippins/ee943f2b25db555ef12107f7cee20241)

## What is a HUD and why should I care?

A Heads-Up Display (HUD) allows you to search through an application's
appmenu. So if you're trying to find that single filter in Gimp but
can't remember which filter category it fits into or if you can't
recall if preferences sits under File, Edit or Tools on your favourite
browser, you can just search for it rather than hunting through the
menus.

### Implementation

[vala-panel-appmenu](https://github.com/rilian-la-te/vala-panel-appmenu)
includes an implementation of the `com.canonical.AppMenu.Registrar` DBus
service. Applications exporting their menu via `dbusmenu` need this
service to run. `mate-hud.py` tries to get the menu of the currently
focused window, lists possible actions and asks the user which one to
run. `mate-hud.py`, binds itself to the `Alt_L` keyboard
shortcut by default (can be changed in the settings GUI).

### Settings

`mate-hud` includes a small GUI for configuring settings: `hud-settings.py`
which should show up in your applications menu. `mate-hud.py` reads two gsettings keys:

  * `org.mate.hud`: `shortcut` (Default: `'Alt_L'`)
  * `org.mate.hud`: `rofi-theme` (Default: `mate-hud`)

`mate-hud.py` will not execute until those gsettings keys are created,
which the `mate-hud` Debian package will do, and the `enabled` key
is set to *True* using something like `dconf-editor`.

`mate-hud` can be enabled or disabled by MATE Tweak under `Panel > Panel Features > Enable HUD`.

### Themes

`mate-hud.py` uses the `mate-hud-rounded` theme by default.
The included `mate-hud` and `mate-hud-rounded` themes and their HiDPI variants
try to use colors from your GTK theme and your system font. You can see
the available themes and make changes with the included settings program.

### Manual Setup

  * The `vala-panel-appmenu` applet for MATE or XFCE should be added to a panel.
  * `mate-hud.py` should be started on session start-up.
  * The following should be added to the users `~/.profile` or `/etc/profile.d` or `/etc/X11/Xsession.d/`.

```
if [ -n "$GTK_MODULES" ]; then
    GTK_MODULES="$GTK_MODULES:unity-gtk-module"
else
    GTK_MODULES="unity-gtk-module"
fi

export GTK_MODULES
export UBUNTU_MENUPROXY=1
```

## Dependencies

  * `appmenu-qt`
  * `gir1.2-gtk-3.0`
  * `mate-desktop`
  * `python3`
  * `python3-dbus`
  * `python3-pyinotify`
  * `python3-setproctitle`
  * `python3-xlib`
  * `rofi`
  * `unity-gtk2-module`
  * `unity-gtk3-module`
  * `plotinus` (optional - additional menu backend for some GTK3 programs without a traditional menu)

A reference package for Debian/Ubuntu is available from:

  * https://bitbucket.org/flexiondotorg/debian-packages

## Compatibility

Compatibility may depend on your environment's compatability with the [rofi](https://github.com/davatorium/rofi/) package, which means environments using Wayland (e.g. Ubuntu 21.04) may not work (see [related rofi issue](https://github.com/davatorium/rofi/issues/446)).
