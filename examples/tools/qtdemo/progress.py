#!/usr/bin/env python

############################################################################
##
## Copyright (C) 2006-2006 Trolltech ASA. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

#import sys
#import math
from PyQt4 import QtCore, QtGui 

class Helper:
    def __init__(self):
        gradient = QtGui.QLinearGradient(QtCore.QPointF(50, -20), QtCore.QPointF(80, 20))
        gradient.setColorAt(0.0, QtCore.Qt.white)
        gradient.setColorAt(1.0, QtGui.QColor(0xa6, 0xce, 0x39))
        
        gradient2 = QtGui.QLinearGradient(QtCore.QPointF(50, -20), QtCore.QPointF(80, 20))
        gradient2.setColorAt(0.0, QtGui.QColor(0xa6, 0xce, 0x39))
        gradient2.setColorAt(1.0, QtCore.Qt.white)
        

        self.background = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        self.circleBrush = QtGui.QBrush(gradient)
        self.circlePen = QtGui.QPen(QtGui.QBrush(gradient2), 0.0)
        self.circlePen.setWidth(0)
        self.textPen = QtGui.QPen(QtGui.QColor(0, 0, 0, 150))
        self.textFont = QtGui.QFont()
        self.textFont.setPixelSize(50)

    def paint(self, painter, event, elapsed):
        painter.fillRect(event.rect(), self.background)
        painter.translate(10, 150)

        painter.save()
        painter.setBrush(self.circleBrush)
        painter.setPen(self.circlePen)
        painter.scale(elapsed/10 * 0.0050, 1.0)     
        
        rectangle=QtCore.QRectF(0.0, 0.0, 50.0, 50.0);
        painter.drawRect(rectangle)
        painter.restore()

        painter.setPen(self.textPen)
        painter.setFont(self.textFont)
#        painter.drawText(QRect(0, 0, 180, 120), Qt.AlignCenter, "13%")


#class Widget(QWidget):
#    def __init__(self, helper, parent = None):
#        QWidget.__init__(self, parent)
#        
#        self.helper = helper
#        self.elapsed = 0
#        self.goback=False
#
#    def animate(self):
#        if not self.goback:
#            self.elapsed = (self.elapsed + self.sender().interval()) % 10000
#        else:
#            self.elapsed = (self.elapsed - self.sender().interval()) % 10000
#        
#        if self.elapsed == 5000:
#            self.goback=True
#        if self.elapsed ==0:
#            self.goback=False
#        print self.elapsed 
#        self.repaint()
#
#    def paintEvent(self, event):
#        painter = QPainter()
#        painter.begin(self)
#        painter.setRenderHint(QPainter.Antialiasing)
#        self.helper.paint(painter, event, self.elapsed)
#        painter.end()

        
    
        

#class Window(QWidget):
#    def __init__(self, parent = None):
#        QWidget.__init__(self, parent)
#
#        helper = Helper()
#        native = Widget(helper, self)
#
##        layout = QGridLayout()
##        layout.addWidget(native, 0, 0)
##        self.setLayout(layout)
#
#        timer = QTimer(self)
#        self.connect(timer, SIGNAL("timeout()"), native.animate)
#        timer.start(50)
#
##        self.setWindowTitle(self.tr("2D Painting on Native and OpenGL Widgets"))


#if __name__ == '__main__':
#    app = QApplication(sys.argv)
#    window = Window()
#    window.show()
#    sys.exit(app.exec_())
