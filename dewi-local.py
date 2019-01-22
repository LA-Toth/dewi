#!/usr/bin/env python3
# Copyright 2015-2019 Laszlo Attila Toth
# Distributed under the terms of the GNU Lesser General Public License v3

import sys

from dewi_core.application import MainApplication
from dewi_core.loader.loader import PluginLoader


def main():
    args = sys.argv[1:]

    loader = PluginLoader()
    app = MainApplication(loader, 'dewi', fallback_to_plugin_name='dewi.DewiPlugin')
    app.run(args)


if __name__ == '__main__':
    main()
