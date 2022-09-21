#!/usr/bin/python3

import os, sys
import locale
import gettext

APP_NAME = "mate-hud"
LOCALE_DIR = os.path.join(sys.prefix, "share", "locale")
gettext.install (True)
gettext.bindtextdomain (APP_NAME, LOCALE_DIR)
gettext.textdomain (APP_NAME)
language = gettext.translation (APP_NAME, LOCALE_DIR, fallback = True)
