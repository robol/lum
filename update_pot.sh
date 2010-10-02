#!/bin/bash

# Extract strings from glade file
for file in src/lum/interface/ui/*.ui; do
	intltool-extract --type gettext/glade --local "$file"
done

xgettext -p locale/ --language=Python --keyword=_ --keyword=N_ \
	--output=lum.pot lum src/lum/*.py src/lum/interface/*.py \
	tmp/*.h

rm tmp -rf
