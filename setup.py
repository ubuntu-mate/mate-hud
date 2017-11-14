#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2016 by Martin Wimpress <code@flexion.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

import os
import sys

from glob import glob
from setuptools import setup

import DistUtilsExtra.command.build_extra
import DistUtilsExtra.command.build_i18n
import DistUtilsExtra.command.clean_i18n

__VERSION__ = '18.04.0'

def datafilelist(installbase, sourcebase):
    datafileList = []
    for root, subFolders, files in os.walk(sourcebase):
        fileList = []
        for f in files:
            fileList.append(os.path.join(root, f))
        datafileList.append((root.replace(sourcebase, installbase), fileList))
    return datafileList

data_files = [
    ('{prefix}/lib/mate-hud/'.format(prefix=sys.prefix), ['usr/lib/mate-hud/mate-hud']),
    ('{prefix}/share/glib-2.0/schemas/'.format(prefix=sys.prefix), ['usr/share/glib-2.0/schemas/org.mate.hud.gschema.xml']),
]

cmdclass = {
        "build" : DistUtilsExtra.command.build_extra.build_extra,
        "clean": DistUtilsExtra.command.clean_i18n.clean_i18n,
}

setup(
    name = "mate-hud",
    version = __VERSION__,
    description = "Run menubar commands, much like the Unity 7 HUD",
    license = 'GPLv2+',
    author = 'Martin Wimpress',
    url = 'https://bitbucket.org/ubuntu-mate/mate-hud/',
    #package_dir = {'': '.'},
    data_files = data_files,
    install_requires = ['setuptools'],
    #scripts = [],
    cmdclass = cmdclass,
)
