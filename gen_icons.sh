#!/usr/bin/env bash

dir="$( dirname "$(readlink -f "$0")" )"

if [ ! -f "${dir}"/usr/share/pixmaps/mate-hud.svg ] ; then
	echo "mate-hud.svg not found" >&2
	exit 1
fi

if ! which inkscape 2>/dev/null; then
	echo "inkscape required to convert svg to png"
	exit 1
fi

rm -fr "${dir}"/usr/share/icons

for d in 16 22 24 32 48 64 128 256 512 1024; do
	install -dm755 "${dir}"/usr/share/icons/hicolor/${d}x${d}/apps
	inkscape -w ${d} -h ${d} "${dir}"/usr/share/pixmaps/mate-hud.svg \
	                -o "${dir}"/usr/share/icons/hicolor/${d}x${d}/apps/mate-hud.png
	optipng -strip all -o7 "${dir}"/usr/share/icons/hicolor/${d}x${d}/apps/mate-hud.png
done

for d in 16 22 24 32 48 64 128 256; do
	d2=$(( $d * 2 ))
	install -dm755 "${dir}"/usr/share/icons/hicolor/${d}x${d}@2/apps
	inkscape -w ${d2} -h ${d2} "${dir}"/usr/share/pixmaps/mate-hud.svg \
	                -o "${dir}"/usr/share/icons/hicolor/${d}x${d}@2/apps/mate-hud.png
	optipng -strip all -o7 "${dir}"/usr/share/icons/hicolor/${d}x${d}@2/apps/mate-hud.png
done

install -Dm644 "${dir}"/usr/share/pixmaps/mate-hud.svg \
               "${dir}"/usr/share/icons/hicolor/scalable/apps/mate-hud.svg
