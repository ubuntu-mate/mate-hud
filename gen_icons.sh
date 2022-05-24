#!/bin/bash

dir="$( dirname "$(readlink -f "$0")" )"

if [ ! -f "${dir}"/usr/share/pixmaps/mate-hud.svg ] ; then
	echo "mate-hud.svg not found" >&2
	exit 1
fi

for d in 16 22 24 32 48 64 128 256 512 ; do
	install -dm755 "${dir}"/usr/share/icons/hicolor/${d}x${d}/apps
	inkscape -w ${d} -h ${d} "${dir}"/usr/share/pixmaps/mate-hud.svg -o output.png \
	                -o "${dir}"/usr/share/icons/hicolor/${d}x${d}/apps/mate-hud.png
done
install -Dm644 "${dir}"/usr/share/pixmaps/mate-hud.svg \
               "${dir}"/usr/share/icons/hicolor/apps/scalable/mate-hud.svg
