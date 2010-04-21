#!/usr/bin/env python
############################################################################
############################################################################

import sys
import os

from PyQt4 import QtGui

import qtdemo_rc1

from displaywidget1 import DisplayWidget
from displayshape1 import PanelShape
from launcher import Launcher

if __name__ == "__main__":
    # Make sure we run from the right directory.  (I don't think this should be
    # necessary.)
    dir = os.path.dirname(__file__)
    if dir:
        os.chdir(dir)

    app = QtGui.QApplication(sys.argv)
    launcher = Launcher()
    if not launcher.setup():
        sys.exit(1)
    launcher.show()
    sys.exit(app.exec_())
