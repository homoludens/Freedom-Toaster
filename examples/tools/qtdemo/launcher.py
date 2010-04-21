#!/usr/bin/env python
############################################################################
##
## Copyright (C) 2004-2005 Trolltech AS. All rights reserved.
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

import sys
import re
import os
from PyQt4 import QtCore, QtGui, QtNetwork, QtXml, QtAssistant
import burning
from displaywidget1 import DisplayWidget
from displayshape1 import TitleShape, DisplayShape, PanelShape, ImageShape, DocumentShape
#from progress import Helper

class Launcher(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        self.categories = {}
        self.runningProcesses = {}
        self.examples = {}
        self.runningExamples = []
        self.titleFont = QtGui.QFont(self.font())
        self.titleFont.setWeight(QtGui.QFont.Bold)
        self.fontRatio = 0.8
        self.documentFont = self.font()
        self.inFullScreenResize = False
        self.currentCategory = "[starting]"
        self.qtLogo = QtGui.QImage()
        self.rbLogo = QtGui.QImage()
        self.background = QtGui.QColor(20, 20, 20, 120)
        self.currentExample = ""
        self.progressBar = QtGui.QProgressBar(self)
        self.buttonCancel= QtGui.QPushButton("Cancel", self);
        self.burningProcess=None
        parentPageAction1 = QtGui.QAction(self.tr("Show Parent Page"), self)
        parentPageAction2 = QtGui.QAction(self.tr("Show Parent Page"), self)
        parentPageAction3 = QtGui.QAction(self.tr("Show Parent Page"), self)
        parentPageAction1.setShortcut(QtGui.QKeySequence(self.tr("Escape")))
        parentPageAction2.setShortcut(QtGui.QKeySequence(self.tr("Backspace")))
        parentPageAction3.setShortcut(QtGui.QKeySequence(self.tr("Alt+Left")))

        fullScreenAction = QtGui.QAction(self.tr("Toggle &Full Screen"), self)
        fullScreenAction.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+F")))

        exitAction = QtGui.QAction(self.tr("E&xit"), self)
        exitAction.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+Q")))

        self.connect(parentPageAction1, QtCore.SIGNAL("triggered()"), self, QtCore.SIGNAL("showPage()"))
        self.connect(parentPageAction2, QtCore.SIGNAL("triggered()"), self, QtCore.SIGNAL("showPage()"))
        self.connect(parentPageAction3, QtCore.SIGNAL("triggered()"), self, QtCore.SIGNAL("showPage()"))
        self.connect(fullScreenAction, QtCore.SIGNAL("triggered()"), self.toggleFullScreen)
        self.connect(exitAction, QtCore.SIGNAL("triggered()"), self.close)

        self.display = DisplayWidget()

        self.addAction(parentPageAction1)
        self.addAction(parentPageAction2)
        self.addAction(parentPageAction3)
        self.addAction(fullScreenAction)
        self.addAction(exitAction)

        self.slideshowTimer = QtCore.QTimer(self)
        self.slideshowTimer.setInterval(2000)
        self.resizeTimer = QtCore.QTimer(self)
        self.resizeTimer.setSingleShot(True)
        self.connect(self.resizeTimer, QtCore.SIGNAL("timeout()"), self.redisplayWindow)

        self.assistant = QtAssistant.QAssistantClient("assistant", self)

        self.connect(self.display, QtCore.SIGNAL("actionRequested"),
                     self.executeAction)
        self.connect(self.display, QtCore.SIGNAL("categoryRequested"),
                     self.showExamples)
        self.connect(self.display, QtCore.SIGNAL("documentationRequested"),
                     self.showExampleDocumentation)
        self.connect(self.display, QtCore.SIGNAL("exampleRequested"),
                     self.showExampleSummary)

        self.connect(self.display, QtCore.SIGNAL("launchRequested"),
                     self.launchExample)

        self.connect(self, QtCore.SIGNAL("showPage()"), self.showParentPage,
                QtCore.Qt.QueuedConnection)
        self.connect(self, QtCore.SIGNAL("windowResized()"), self.redisplayWindow,
                QtCore.Qt.QueuedConnection)

        self.setCentralWidget(self.display)
        self.setMaximumSize(QtGui.QApplication.desktop().screenGeometry().size())
        self.setWindowTitle(self.tr("PyQt Examples and Demos"))
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("images/qt4-logo.png")))

    def setup(self):
        self.documentationDir = QtCore.QDir("./../../../")

        if not self.documentationDir.cd("html"):
            QtGui.QMessageBox.warning(self, self.tr("No Documentation Found"),
                            self.tr("I could not find the Qt documentation."),
                            QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton)

        self.imagesDir = QtCore.QDir(".")
        if not self.imagesDir.cd("images"):
            QtGui.QMessageBox.warning(self, self.tr("No Images found"),
                            self.tr("I could not find any images for the Qt documentation"),
                            QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton)

        self.maximumLabels = 0

        # No demos have been ported yet.
        #self.demosDir = QtCore.QDir("./../../../demos")
        #demoCategories = self.readInfo(":/demos.xml", self.demosDir)
        demoCategories = 0

        self.examplesDir = QtCore.QDir("./../../")
        exampleCategories = self.readInfo("examples.xml", self.examplesDir)

        if demoCategories + exampleCategories <= 0:
            QtGui.QMessageBox.warning(self, self.tr("No Examples or Demos found"),
                                        self.tr("I could not find any PyQt examples or demos.\n"\
                                                "Please ensure that PyQt is installed correctly."),
                                        QtGui.QMessageBox.Cancel, QtGui.QMessageBox.NoButton)
            return False

        self.maximumLabels = max(demoCategories + exampleCategories, self.maximumLabels)

        for category in self.categories:
            self.maximumLabels = max(len(self.categories[category]['examples']) + 1, self.maximumLabels)

        mainDescription = self.categories['[main]']['description']
        if len(mainDescription) > 0:
            mainDescription += self.tr("\n")

        self.categories['[main]']['description'] = mainDescription + self.tr(
            "<p>Press <b>Escape</b>, <b>Backspace</b>, or <b>%1</b> to "
            "return to a previous menu.</p>"
            "<p>Press <b>%2</b> to switch between normal and full screen "
            "modes.</p>"
            "<p>Use <b>%3</b> to exit the launcher.</p>") \
                .arg(QtCore.QString(QtGui.QKeySequence(self.tr("Alt+Left")))) \
                .arg(QtCore.QString(QtGui.QKeySequence(self.tr("Ctrl+F")))) \
                .arg(QtCore.QString(QtGui.QKeySequence(self.tr("Ctrl+Q"))))

        self.emit(QtCore.SIGNAL("showPage()"))
        return True

        
    def enableBurning(self):
        for i in range(0, self.display.shapesCount()):
            shape = self.display.shape(i)
#            if shape.metadata.get("launch", "") == example:
#                shape.metadata["fade"] = 15
#                self.display.enableUpdates()

        self.slideshowTimer.start()

    def enableLaunching(self):
        process = self.sender()
        example = self.runningProcesses[process]
        del self.runningProcesses[process]
        process.deleteLater()
        self.runningExamples.remove(example)

        if example == self.currentExample:
            for i in range(0, self.display.shapesCount()):
                shape = self.display.shape(i)
                if shape.metadata.get("launch", "") == example:
                    shape.metadata["fade"] = 15
                    self.display.enableUpdates()

            self.slideshowTimer.start()

    def executeAction(self, action):
        if action == "parent":
            self.showParentPage()
        elif action == "exit":
            if len(self.runningExamples) == 0:
                self.connect(self.display, QtCore.SIGNAL("displayEmpty()"), self.close)
                self.display.reset()
            else:
                self.close()

    def launchExample(self, uniquename):
        if uniquename in self.runningExamples:
            return
        print "Burn baby, burn!!!"

#        process = QtCore.QProcess(self)
#        self.connect(process, QtCore.SIGNAL("finished(int)"), self.enableLaunching)
#        
#
#        self.runningExamples.append(uniquename)
#        self.runningProcesses[process] = uniquename
#
#        if self.examples[uniquename]['changedirectory'] == 'true':
#            process.setWorkingDirectory(self.examples[uniquename]['absolute path'])
        isofile=self.examples[uniquename]['path'].toAscii().data()[:-2]+"iso"
        self.burningProcess = burning.Window()
        self.burningProcess.startCommand(isofile)

#        process.start(sys.executable, [self.examples[uniquename]['path']])

#        if process.state() == QtCore.QProcess.Starting:
#            self.slideshowTimer.stop()
        
        burnbg = QtGui.QImage(self.imagesDir.absoluteFilePath("burnbg.png"))
        burnshape = ImageShape( burnbg,QtCore.QPointF(0.0, 0.0), QtCore.QSizeF(self.width(), self.height()), 55, QtCore.Qt.AlignLeft)
        burnshape.metadata["fade"] = 15
        
        burnProgress = QtGui.QImage(self.imagesDir.absoluteFilePath("burnProgress.jpg"))
        burnProgressShape = ImageShape( burnProgress,QtCore.QPointF(-300.0, 0.0), QtCore.QSizeF(self.width(), self.height()), 255, QtCore.Qt.AlignCenter)
        
        self.progressBar = QtGui.QProgressBar(self)
        
        self.progressBar.setWindowTitle(self.tr("Burning"))
        self.progressBar.setFixedSize(400, 50)
        self.progressBar.move(200, 260)
        self.progressBar.setRange(1, 10)
        format=QtCore.QString.fromAscii("Burning starting in %v seconds")
        self.progressBar.setFormat(format)
        self.progressBar.setValue(10)
        
        self.buttonCancel = QtGui.QPushButton("Cancel", self)
        self.buttonCancel.move(360, 340)
        self.buttonCancel.show()
        
        self.connect(self.burningProcess, QtCore.SIGNAL("burningProgress(int)"), self.updateProgressBarBurning)
        self.connect(self.burningProcess, QtCore.SIGNAL("burningStartingIn(int)"), self.updateProgressBarStarting)
        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), QtCore.SIGNAL("showPage()"))
        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), self.enableBurning)
#        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), self.burningFinishedMessage)
        self.connect(self.burningProcess, QtCore.SIGNAL("burningError(int)"), self.errorBurning)
        self.connect(self.buttonCancel, QtCore.SIGNAL("clicked()"), self.burningCanceled)
        self.progressBar.show()
        
        
        
        imageSize = burnProgressShape.maxSize
        imagePosition = QtCore.QPointF(self.width() - imageSize.width()/2, burnProgressShape.position().y())
        burnProgressShape.setTarget(QtCore.QPointF(self.width()-imageSize.width()/2, imagePosition.y()))
        
        self.slideshowTimer.stop()
        self.disconnect(self.slideshowTimer, QtCore.SIGNAL("timeout()"), self.updateExampleSummary)
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow)
        
        self.display.dimmShapes(burnshape, self.progressBar)
#        self.display.insertShape(0, burnProgressShape)

    def burningCanceled(self):
        self.burningProcess.stopCommand(335)
        self.progressBar.setRange(0, 10)
        self.progressBar.setValue(10)
        format=QtCore.QString.fromAscii("Burning Canceled")
        self.progressBar.setFormat(format)
        self.buttonCancel.hide()
        QtCore.QTimer.singleShot(5000, self,  QtCore.SIGNAL("showPage()"))
        self.enableBurning()

    def burningFinishedMessage(self):
        format=QtCore.QString.fromAscii("Burning Finished")
        self.progressBar.setFormat(format)
#        QtCore.QTimer.singleShot(5000, self,  QtCore.SIGNAL("showPage()"))

    def errorBurning(self, i):
        if i==333:
            format=QtCore.QString.fromAscii("Error while burning: Try different media.")
        if i==334:
            format=QtCore.QString.fromAscii("No media.")
        self.progressBar.setFormat(format)
        QtCore.QTimer.singleShot(5000, self,  QtCore.SIGNAL("showPage()"))
        
    def updateProgressBarBurning(self, i):
        if i==0:
            self.progressBar.setRange(0, 100)
            format=QtCore.QString.fromAscii("Burning progress %p%")
            self.progressBar.setFormat(format)
            self.progressBar.show()
        self.progressBar.setValue(i)
        
        if i==100:
            format=QtCore.QString.fromAscii("Burning finished: Ejecting")
            self.progressBar.setFormat(format)
    def updateProgressBarStarting(self, i):
        if i==9:
            self.progressBar.setRange(1, 10)
            format=QtCore.QString.fromAscii("Burning starting in %v  seconds")
            self.progressBar.setFormat(format)
        self.progressBar.setValue(i)
        
        if i==1:
            self.progressBar.setRange(0,0)
            self.buttonCancel.hide()



    def showCategories(self):
        self.newPage()
        self.fadeShapes()
        self.currentCategory = ""
        self.currentExample = ""

        # Sort the category names excluding any "Qt" prefix.
        def csort(c1, c2):
            if c1.startsWith("Qt "):
                c1 = c1[3:]

            if c2.startsWith("Qt "):
                c2 = c2[3:]

            return cmp(c1, c2)

        categories = [c for c in self.categories.keys() if c != "[main]"]
        categories.sort(csort)

        horizontalMargin = 0.025*self.width()
        verticalMargin = 0.025*self.height()
        title = TitleShape(self.tr("Freedom Toster slobodnakulture"),
                        self.titleFont, QtGui.QPen(QtGui.QColor("#a6ce39")), QtCore.QPointF(),
                        QtCore.QSizeF(0.5*self.width(), 4*verticalMargin))

        title.setPosition(QtCore.QPointF(self.width() / 2 - title.rect().width() / 2,
                                         -title.rect().height()))
        title.setTarget(QtCore.QPointF(title.position().x(), verticalMargin))

        self.display.appendShape(title)

        topMargin = 6*verticalMargin
        bottomMargin = self.height() - 3.2*verticalMargin
        space = bottomMargin - topMargin
        step = min(title.rect().height() / self.fontRatio, space/self.maximumLabels )
        step=title.rect().height()/self.fontRatio
        textHeight = self.fontRatio * step

        startPosition = QtCore.QPointF(0.0, topMargin)
        maxSize = QtCore.QSizeF(10.8*horizontalMargin, textHeight)
        maxWidth = 160.0

        newShapes = []

        for category in categories:
            caption = TitleShape(category, self.font(), QtGui.QPen(QtCore.Qt.white), QtCore.QPointF(startPosition), QtCore.QSizeF(maxSize))
            caption.setPosition(QtCore.QPointF(10*caption.rect().width(),
                                caption.position().y()))
            caption.setTarget(QtCore.QPointF(3*horizontalMargin, caption.position().y()))

            newShapes.append(caption)
            startPosition += QtCore.QPointF(0.0, step)
#            print caption.rect().width()
            maxWidth = max(maxWidth, caption.rect().width() )
#        startPosition = QtCore.QPointF(0.0, 500.0)
        exitButton = TitleShape(self.tr("Exit"), self.font(), QtGui.QPen(QtCore.Qt.white),
                                   QtCore.QPointF(QtCore.QPointF(0.0, 500.0)), QtCore.QSizeF(maxSize))
        exitButton.setTarget(QtCore.QPointF(3*horizontalMargin, exitButton.position().y()))
        newShapes.append(exitButton)

        startPosition = QtCore.QPointF(self.width(), topMargin)

        extra = (step - textHeight)/4

        backgroundPath = QtGui.QPainterPath()
        backgroundPath.addRoundRect(-2*extra, -extra, maxWidth + 4*extra, textHeight + 2*extra, 15, 85)
        
        brush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
        outlinebrush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
        
        normal1 = QtGui.QColor(120, 120, 120, 50)
        normal2 = QtGui.QColor(60, 60, 60, 50)
        highlight = QtGui.QColor(255, 255, 255, 70);
        shadow = QtGui.QColor(0, 0, 0, 120);
        sunken = QtGui.QColor(220, 220, 220, 30);
        
        brush.setSpread(QtGui.QLinearGradient.PadSpread)
        brush.setColorAt(0.0, normal1)
        brush.setColorAt(1.0, normal2)
        outlinebrush.setColorAt(1.0, shadow)
        outlinebrush.setColorAt(0.0, highlight)
        
        for category in categories:
#            startPosition += QtCore.QPointF(800.0, 0.0)
            background = PanelShape(backgroundPath,
                QtGui.QBrush(brush), QtGui.QBrush(outlinebrush),
#                QtGui.QBrush(QtGui.QColor(255, 255, 255, 20)), QtGui.QBrush(QtGui.QColor(125, 125, 125, 255)),
                QtGui.QPen(QtGui.QPen(QtGui.QBrush(outlinebrush), 1)), QtCore.QPointF(startPosition),
                QtCore.QSizeF(2*maxWidth + 8*extra, textHeight + 2*extra))

            background.metadata["category"] = category
            background.setInteractive(True)
            background.setTarget(QtCore.QPointF(2*horizontalMargin,
                                          background.position().y()))
            self.display.insertShape(0, background)
            startPosition += QtCore.QPointF(800.0, step)

        exitPath = QtGui.QPainterPath()
        exitPath.moveTo(-2*extra, -extra)
        exitPath.lineTo(-8*extra, textHeight/2)
        exitPath.lineTo(-extra, textHeight + extra)
        exitPath.lineTo(maxWidth + 2*extra, textHeight + extra)
        exitPath.lineTo(maxWidth + 2*extra, -extra)
        exitPath.closeSubpath()
        

        exitBackground = PanelShape(exitPath,
            QtGui.QBrush(QtGui.QColor(20, 20, 20, 120)), QtGui.QBrush(QtGui.QColor(120, 120, 120, 120)),
            QtGui.QPen(QtCore.Qt.NoPen), QtCore.QPointF(QtCore.QPointF(startPosition.x(), 500.0)),
            QtCore.QSizeF(maxWidth + 10*extra, textHeight + 2*extra))

        exitBackground.metadata["action"] = "exit"
        exitBackground.setInteractive(True)
        exitBackground.setTarget(QtCore.QPointF(2*horizontalMargin,
                                          exitBackground.position().y()))
        self.display.insertShape(0, exitBackground)
        textStartPos=800.0
        for caption in newShapes:
            position = caption.target()
            size = caption.rect().size()
            
            caption.setPosition(QtCore.QPointF(textStartPos, position.y()))
            textStartPos += 800.0
            self.display.appendShape(caption)

        leftMargin = 5*horizontalMargin + maxWidth
        rightMargin = self.width() - 3*horizontalMargin

        description = DocumentShape(self.categories['[main]']['description'],
            self.documentFont, QtCore.QPointF(leftMargin, topMargin),
                QtCore.QSizeF(rightMargin - leftMargin, space))
        description.animateWait=1
        description.metadata["fade"] = 10
        self.display.appendShape(description)

        imageHeight = title.rect().height() + verticalMargin

        qtLength = min(imageHeight, title.rect().left()-3*horizontalMargin)
        qtMaxSize = QtCore.QSizeF(qtLength, qtLength)

        qtShape = ImageShape(self.qtLogo,
                QtCore.QPointF(2*horizontalMargin-extra, -imageHeight), qtMaxSize, 0,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        qtShape.metadata["fade"] = 15
        qtShape.setTarget(QtCore.QPointF(qtShape.rect().x(), verticalMargin))
        self.display.insertShape(0, qtShape)

        trolltechMaxSize = QtCore.QSizeF(
                self.width()-3*horizontalMargin-title.rect().right(), imageHeight)

        trolltechShape = ImageShape(self.rbLogo,
                QtCore.QPointF(self.width()-2*horizontalMargin-trolltechMaxSize.width()+extra,
                        -imageHeight),
                trolltechMaxSize, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        trolltechShape.metadata["fade"] = 15
        trolltechShape.setTarget(QtCore.QPointF(trolltechShape.rect().x(),
                            verticalMargin))

        self.display.insertShape(0, trolltechShape)

        self.addVersionAndCopyright(QtCore.QRectF(2*horizontalMargin,
                    self.height() - verticalMargin - textHeight,
                    self.width() - 4*horizontalMargin, textHeight))

    def showExampleDocumentation(self, uniqueName):
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow)
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.close)
        self.currentExample = uniqueName
        print "showExampleDocumentation"
        self.progressBar = QtGui.QProgressBar(self)
        
        self.progressBar.setWindowTitle(self.tr("Burning"))
        self.progressBar.setFixedSize(400, 50)
        self.progressBar.move(200, 260)
        self.progressBar.setRange(0,0)
        format=QtCore.QString.fromAscii("Blanking CD-RW")
        self.progressBar.setFormat(format)
        self.progressBar.show()
        
        self.burningProcess = burning.Window()
        self.burningProcess.blankCommand()
        self.buttonCancel = QtGui.QPushButton("Cancel", self)
        self.buttonCancel.move(360, 340)
        self.buttonCancel.show()
        
        burnbg = QtGui.QImage(self.imagesDir.absoluteFilePath("burnbg.png"))
        burnshape = ImageShape( burnbg,QtCore.QPointF(0.0, 0.0), QtCore.QSizeF(self.width(), self.height()), 55, QtCore.Qt.AlignLeft)
        burnshape.metadata["fade"] = 15
        
#        self.assistant.showPage(self.examples[uniqueName]["document path"])
        
        self.slideshowTimer.stop()
        self.disconnect(self.slideshowTimer, QtCore.SIGNAL("timeout()"), self.updateExampleSummary)
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow)
        self.connect(self.burningProcess, QtCore.SIGNAL("burningStartingIn(int)"), self.updateProgressBarStartBlanking)
#        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), QtCore.SIGNAL("showPage()"))
        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), self.enableBurning)
        self.connect(self.burningProcess, QtCore.SIGNAL("burningFinished()"), self.blankingFinishedMessage)
#        self.connect(self.buttonCancel, QtCore.SIGNAL("burningFinished()"), self.blankingFinishedMessage)
        self.connect(self.buttonCancel, QtCore.SIGNAL("clicked()"), self.blankingCanceled)
        
        self.display.dimmShapes(burnshape, self.progressBar)

    def blankingCanceled(self):
        self.burningProcess.stopCommand(335)
        self.progressBar.setRange(0, 10)
        self.progressBar.setValue(10)
        format=QtCore.QString.fromAscii("Blanking Canceled")
        self.progressBar.setFormat(format)
        self.buttonCancel.hide()
        QtCore.QTimer.singleShot(5000, self,  QtCore.SIGNAL("showPage()"))
        self.enableBurning()
        
    def updateProgressBarStartBlanking(self, i):
        if i==9:
            self.progressBar.setRange(1, 10)
            format=QtCore.QString.fromAscii("Blanking starting in %v  seconds")
            self.progressBar.setFormat(format)
        self.progressBar.setValue(i)
        
        if i==1:
            self.progressBar.setRange(0,0)
            self.buttonCancel.hide()
        
    def blankingFinishedMessage(self):
        self.progressBar.setRange(0, 10)
        self.progressBar.setValue(10)
        format=QtCore.QString.fromAscii("Blanking Finished")
        self.progressBar.setFormat(format)
        QtCore.QTimer.singleShot(5000, self,  QtCore.SIGNAL("showPage()"))
        
    def showExamples(self, category):
        self.newPage()
        self.fadeShapes()
        self.currentCategory = category
        self.currentExample = ""

        horizontalMargin = 0.025*self.width()
        verticalMargin = 0.025*self.height()

        title = self.addTitle(category, verticalMargin)
        self.addTitleBackground(title)

        topMargin = 6*verticalMargin
        bottomMargin = self.height() - 3.2*verticalMargin
        space = bottomMargin - topMargin
        step = min(title.rect().height() / self.fontRatio, space/self.maximumLabels )
        textHeight = self.fontRatio * step
        if textHeight > 20.0:
            textHeight=20.0

        startPosition = QtCore.QPointF(self.width(), topMargin)
        finishPosition = QtCore.QPointF(3*horizontalMargin, topMargin)
        maxSize = QtCore.QSizeF(32*horizontalMargin, textHeight)
        maxWidth = 0.0
        
        
        
        for example in self.categories[self.currentCategory]['examples']:
            startPosition += QtCore.QPointF(800.0, 0.0)
            caption = TitleShape(example, self.font(), QtGui.QPen(QtCore.Qt.white), QtCore.QPointF(startPosition), QtCore.QSizeF(maxSize))
            caption.setTarget(QtCore.QPointF(finishPosition))

            self.display.appendShape(caption)

            startPosition += QtCore.QPointF(0.0, step)

            finishPosition += QtCore.QPointF(0.0, step)
            maxWidth = max(maxWidth, 160.0 )
#            maxWidth = max(maxWidth, caption.rect().width(), 160.0 )

        menuButton = TitleShape(self.tr("Main Menu"), self.font(),
                                QtGui.QPen(QtCore.Qt.white),
                                QtCore.QPointF(startPosition.x(),500.0),
                                QtCore.QSizeF(maxSize))
        menuButton.setTarget(QtCore.QPointF(finishPosition.x(), 500.0))
        self.display.appendShape(menuButton)

        startPosition = QtCore.QPointF(self.width(), topMargin )
        extra = (step - textHeight)/4
        
        brush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
        outlinebrush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
        
        normal1 = QtGui.QColor(120, 120, 120, 50)
        normal2 = QtGui.QColor(60, 60, 60, 50)
        highlight = QtGui.QColor(255, 255, 255, 70);
        shadow = QtGui.QColor(0, 0, 0, 120);
        sunken = QtGui.QColor(220, 220, 220, 30);
        
        brush.setSpread(QtGui.QLinearGradient.PadSpread)
        brush.setColorAt(0.0, normal1)
        brush.setColorAt(1.0, normal2)
        outlinebrush.setColorAt(1.0, shadow)
        outlinebrush.setColorAt(0.0, highlight)
        
        for example in self.categories[self.currentCategory]['examples']:
            uniquename = self.currentCategory + "-" + example

            path = QtGui.QPainterPath()
            path.addRoundRect(-2*extra, -extra, maxWidth + 4*extra, textHeight+2*extra, 15, 85)
#            path.addRoundRect(-2*extra, -extra, 160.0, textHeight+2*extra, 15, 85)
            startPosition += QtCore.QPointF(800.0, 0.0)
            background = PanelShape(path, QtGui.QBrush(brush), QtGui.QBrush(outlinebrush), 
#                QtGui.QBrush(self.examples[uniquename]['color']),
#                QtGui.QBrush(QtGui.QColor("#e0e0ff")),
                QtGui.QPen(QtGui.QPen(QtGui.QBrush(outlinebrush), 1)), QtCore.QPointF(startPosition),
#                QtCore.QSizeF(maxWidth + 4*extra, textHeight + 2*extra))
                QtCore.QSizeF(maxWidth + 4*extra, textHeight + 2*extra))

            background.metadata["example"] =  uniquename
            background.setInteractive(True)
            background.setTarget(QtCore.QPointF(2*horizontalMargin,
                                          background.position().y()))
            self.display.insertShape(0, background)
            startPosition += QtCore.QPointF(0.0, step)
        
        backPath = QtGui.QPainterPath()
        backPath.moveTo(-2*extra, -extra)
        backPath.lineTo(-8*extra, textHeight/2)
        backPath.lineTo(-extra, textHeight + extra)
        backPath.lineTo(maxWidth + 2*extra, textHeight + extra)
        backPath.lineTo(maxWidth + 2*extra, -extra)
        backPath.closeSubpath()

        buttonBackground = PanelShape(backPath,
            QtGui.QBrush(QtGui.QColor("#a6ce39")), QtGui.QBrush(QtGui.QColor("#c7f745")),
            QtGui.QPen(QtCore.Qt.NoPen), QtCore.QPointF(startPosition.x(), 500.0),
            QtCore.QSizeF(maxWidth + 10*extra, textHeight + 2*extra))

        buttonBackground.metadata["action"] =  "parent"
        buttonBackground.setInteractive(True)
        buttonBackground.setTarget(QtCore.QPointF(2*horizontalMargin,
                                          buttonBackground.position().y()))
        self.display.insertShape(0, buttonBackground)

        leftMargin = 3*horizontalMargin + maxWidth
        rightMargin = self.width() - 3*horizontalMargin
        
#        print background
        description = DocumentShape(self.categories[self.currentCategory]['description'],
            self.documentFont, QtCore.QPointF(leftMargin, topMargin),
                QtCore.QSizeF(rightMargin - leftMargin, space), 0)
        description.animateWait=1
        description.metadata["fade"] =  15
        self.display.appendShape(description)

        self.addVersionAndCopyright(QtCore.QRectF(2*horizontalMargin,
                    self.height() - verticalMargin - textHeight,
                    self.width() - 4*horizontalMargin, textHeight))

    def showExampleSummary(self, uniquename):
        self.newPage()
        self.fadeShapes()
        self.currentExample = uniquename

        horizontalMargin = 0.025*self.width()
        verticalMargin = 0.025*self.height()

        title = self.addTitle(self.examples[uniquename]['name'], verticalMargin)
        titleBackground = self.addTitleBackground(title)

        topMargin = 2*verticalMargin + titleBackground.rect().bottom()
        bottomMargin = self.height() - 8*verticalMargin
        space = bottomMargin - topMargin
        step = min(title.rect().height() / self.fontRatio,
                    ( bottomMargin + 4.8*verticalMargin - topMargin )/self.maximumLabels )
        footerTextHeight = self.fontRatio * step

        leftMargin = 3*horizontalMargin
        rightMargin = self.width() - 3*horizontalMargin

        if self.examples[self.currentExample].has_key('description'):
            description = DocumentShape( self.examples[self.currentExample]['description'],
                                self.documentFont, QtCore.QPointF(leftMargin, topMargin),
                                QtCore.QSizeF(rightMargin-leftMargin, space), 0 )
            description.metadata["fade"] = 10

            description.setPosition(QtCore.QPointF(description.position().x(),
                            0.8*self.height()-description.rect().height()))

            self.display.appendShape(description)
            space = description.position().y() - topMargin - 2*verticalMargin

        if self.examples[self.currentExample].has_key('image files'):
            image = QtGui.QImage(self.examples[self.currentExample]['image files'][0])
            imageMaxSize = QtCore.QSizeF(self.width() - 8*horizontalMargin, space)

            self.currentFrame = ImageShape( image,
                            QtCore.QPointF(self.width()-imageMaxSize.width()/2, topMargin),
                            QtCore.QSizeF(imageMaxSize ))

            self.currentFrame.metadata["fade"] = 15
            self.currentFrame.setTarget(QtCore.QPointF(self.width()/2-imageMaxSize.width()/2,
                                    topMargin))
            self.display.appendShape(self.currentFrame)

            if len(self.examples[self.currentExample]['image files']) > 1:
                self.connect(self.slideshowTimer, QtCore.SIGNAL("timeout()"),
                        self.updateExampleSummary)
                self.slideshowFrame = 0
                self.slideshowTimer.start()

        maxSize = QtCore.QSizeF(0.3*self.width(),2*verticalMargin)
        leftMargin = 0.0
        rightMargin = 0.0

        backButton = TitleShape(self.currentCategory, self.font(),
            QtGui.QPen(QtCore.Qt.white), QtCore.QPointF(0.1*self.width(), self.height()), QtCore.QSizeF(maxSize),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        backButton.setTarget(QtCore.QPointF(backButton.position().x(),
                                      self.height() - 5.2*verticalMargin))

        self.display.appendShape(backButton)

        maxWidth = backButton.rect().width()
        textHeight = backButton.rect().height()
        extra = (3*verticalMargin - textHeight)/4

        path = QtGui.QPainterPath()
        path.moveTo(-extra, -extra)
        path.lineTo(-4*extra, textHeight/2)
        path.lineTo(-extra, textHeight + extra)
        path.lineTo(maxWidth + 2*extra, textHeight + extra)
        path.lineTo(maxWidth + 2*extra, -extra)
        path.closeSubpath()

        buttonBackground = PanelShape(path,
            QtGui.QBrush(QtGui.QColor("#a6ce39")), QtGui.QBrush(QtGui.QColor("#c7f745")), QtGui.QPen(QtCore.Qt.NoPen),
            QtCore.QPointF(backButton.position()),
            QtCore.QSizeF(maxWidth + 6*extra, textHeight + 2*extra))

        buttonBackground.metadata["category"] =  self.currentCategory
        buttonBackground.setInteractive(True)
        buttonBackground.setTarget(QtCore.QPointF(backButton.target()))

        self.display.insertShape(0, buttonBackground)

        leftMargin = buttonBackground.rect().right()
        
        
        if self.examples[self.currentExample].has_key('absolute path'):
            launchCaption = TitleShape(self.tr("Burn"),
                self.font(), QtGui.QPen(QtCore.Qt.white), QtCore.QPointF(0.0, 0.0), QtCore.QSizeF(maxSize),
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            launchCaption.setPosition(QtCore.QPointF(
                0.9*self.width() - launchCaption.rect().width(), self.height()))
            launchCaption.setTarget(QtCore.QPointF(launchCaption.position().x(),
                                             self.height() - 5.2*verticalMargin))

            self.display.appendShape(launchCaption)

            maxWidth = launchCaption.rect().width()
            textHeight = launchCaption.rect().height()
            extra = (3*verticalMargin - textHeight)/4

            path = QtGui.QPainterPath()
            path.addRoundRect(-2*extra, -extra, maxWidth + 4*extra, textHeight + 2*extra, 55, 85)

            backgroundColor = QtGui.QColor(20, 20, 20, 120) #QtGui.QColor("#a63e39")
            highlightedColor = QtGui.QColor(120, 120, 120, 120) #QtGui.QColor("#f95e56")

            brush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
            outlinebrush=QtGui.QLinearGradient(0, 0, 0, textHeight + 2*extra)
            
            normal1 = QtGui.QColor(120, 120, 120, 50)
            normal2 = QtGui.QColor(60, 60, 60, 50)
            highlight = QtGui.QColor(255, 255, 255, 70);
            shadow = QtGui.QColor(0, 0, 0, 120);
            sunken = QtGui.QColor(220, 220, 220, 30);
            
            brush.setSpread(QtGui.QLinearGradient.PadSpread)
            brush.setColorAt(0.0, normal1)
            brush.setColorAt(1.0, normal2)
            outlinebrush.setColorAt(1.0, shadow)
            outlinebrush.setColorAt(0.0, highlight)
            
            
            background = PanelShape(path,
                QtGui.QBrush(brush), QtGui.QBrush(outlinebrush), QtGui.QPen(QtGui.QPen(QtGui.QBrush(outlinebrush), 1)),
                QtCore.QPointF(launchCaption.position()),
                QtCore.QSizeF(maxWidth + 4*extra, textHeight + 2*extra))

            background.metadata["fade minimum"] =  120
            background.metadata["launch"] =  self.currentExample
            background.setInteractive(True)
            background.setTarget(QtCore.QPointF(launchCaption.target()))

            if self.currentExample in self.runningExamples:
                background.metadata["highlight"] =  True
                background.metadata["highlight scale"] =  0.99
                background.animate()
                background.metadata["fade"] =  -135
                self.slideshowTimer.stop()
            self.display.insertShape(0, background)

            rightMargin = background.rect().left()

        if self.examples[self.currentExample].has_key('document path'):

            documentCaption = TitleShape(self.tr("Blank CD-RW"),
                self.font(), QtGui.QPen(QtCore.Qt.white), QtCore.QPointF(0.0, 0.0), QtCore.QSizeF(maxSize),
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

            if rightMargin == 0.0:
                documentCaption.setPosition(QtCore.QPointF(
                    0.9*self.width() - documentCaption.rect().width(), self.height()))
            else:
                documentCaption.setPosition(QtCore.QPointF(
                    leftMargin/2 + rightMargin/2 - documentCaption.rect().width()/2,
                    self.height()))

            documentCaption.setTarget(QtCore.QPointF(documentCaption.position().x(),
                                               self.height() - 5.2*verticalMargin))

            self.display.appendShape(documentCaption)

            maxWidth = documentCaption.rect().width()
            textHeight = documentCaption.rect().height()
            extra = (3*verticalMargin - textHeight)/4

            path = QtGui.QPainterPath()
            path.addRect(-2*extra, -extra, maxWidth + 4*extra, textHeight + 2*extra)

            background = PanelShape(path,
                QtGui.QBrush(QtGui.QColor("#9c9cff")), QtGui.QBrush(QtGui.QColor("#cfcfff")), QtGui.QPen(QtCore.Qt.NoPen),
                QtCore.QPointF(documentCaption.position()),
                QtCore.QSizeF(maxWidth + 4*extra, textHeight + 2*extra))

            background.metadata["fade minimum"] =  120
            background.metadata["documentation"] =  self.currentExample
            background.setInteractive(True)
            background.setTarget(QtCore.QPointF(documentCaption.target()))

            self.display.insertShape(0, background)

        self.addVersionAndCopyright(QtCore.QRectF(2*horizontalMargin,
                    self.height() - verticalMargin - footerTextHeight,
                    self.width() - 4*horizontalMargin, footerTextHeight))

    def showParentPage(self):
        self.slideshowTimer.stop()
        self.disconnect(self.slideshowTimer, QtCore.SIGNAL("timeout()"), self.updateExampleSummary)
        self.progressBar.hide()
        if len(self.currentExample) > 0:
            self.currentExample = ""
            self.redisplayWindow()
        elif len(self.currentCategory) > 0:
            self.currentCategory = ""
            self.redisplayWindow()

    def updateExampleSummary(self):
        if self.examples[self.currentExample].has_key('image files'):
            self.currentFrame.metadata["fade"] = -15
            self.currentFrame.setTarget(QtCore.QPointF((self.currentFrame.position() -
                        QtCore.QPointF(0.5*self.width(), 0))))
            self.slideshowFrame = (self.slideshowFrame+1) % len(self.examples[self.currentExample]['image files'])
            image = QtGui.QImage(self.examples[self.currentExample]['image files'][self.slideshowFrame])

            imageSize = self.currentFrame.maxSize
            imagePosition = QtCore.QPointF(self.width() - imageSize.width()/2,
                                    self.currentFrame.position().y())

            self.currentFrame = ImageShape(image, QtCore.QPointF(imagePosition), QtCore.QSizeF(imageSize))
            self.currentFrame.metadata["fade"] = 15
            self.currentFrame.setTarget(QtCore.QPointF(self.width()/2-imageSize.width()/2,
                            imagePosition.y()))

            self.display.appendShape(self.currentFrame)

    def closeEvent(self, event):
        if len(self.runningExamples) > 0:
            if QtGui.QMessageBox.warning(self, self.tr("Examples Running"),
                    self.tr("There are examples running. Do you really want to exit?"),
                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No ) == QtGui.QMessageBox.No:
                event.ignore()
                return

        for example in self.runningProcesses.keys():
            example.terminate()
            example.waitForFinished(1000)

        self.runningProcesses.clear()
        self.resizeTimer.stop()
        self.slideshowTimer.stop()

    def resizeEvent(self, event):
        self.documentFont = QtGui.QFont(self.font())
        self.documentFont.setPointSizeF(min(self.documentFont.pointSizeF()*self.width()/640.0,
                                            self.documentFont.pointSizeF()*self.height()/480.0))
        self.documentFont.setBold(True)

        if self.inFullScreenResize:
            self.emit(QtCore.SIGNAL("windowResized()"))
            self.inFullScreenResize = False
        elif self.currentCategory != "[starting]":
            self.resizeTimer.start(500)

    def toggleFullScreen(self):
        if self.inFullScreenResize:
            return

        self.inFullScreenResize = True
        self.connect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow, QtCore.Qt.QueuedConnection)
        self.display.reset()

    def redisplayWindow(self):
        if len(self.currentExample) > 0:
            self.showExampleSummary(self.currentExample)
        elif len(self.currentCategory) > 0:
            self.showExamples(self.currentCategory)
        else:
            self.showCategories()

    def resizeWindow(self):
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow)

        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def addTitle(self, title, verticalMargin):
        titlePosition = QtCore.QPointF(0.0, 2*verticalMargin)

        newTitle = TitleShape(title, self.titleFont, QtGui.QPen(QtCore.Qt.white),
                            QtCore.QPointF(titlePosition), QtCore.QSizeF(0.5*self.width(), 2*verticalMargin ),
                            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop )
        newTitle.setPosition(QtCore.QPointF(-newTitle.rect().width(), titlePosition.y()))
        newTitle.setTarget(QtCore.QPointF(0.25*self.width(), titlePosition.y()))
        newTitle.metadata["fade"] =  15

        self.display.appendShape(newTitle)

        return newTitle

    def addTitleBackground(self, titleShape):
        backgroundPath = QtGui.QPainterPath()

        backgroundPath.addRect(0, -titleShape.rect().height()*0.3, self.width(),
                                titleShape.rect().height()*1.6)

        titleBackground = PanelShape(backgroundPath, QtGui.QBrush(QtGui.QColor(120, 120, 120, 120)),
                                    QtGui.QBrush(QtGui.QColor("#a6ce39") ), QtGui.QPen(QtCore.Qt.NoPen),
                                    QtCore.QPointF( self.width(), titleShape.position().y() ),
                                    QtCore.QSizeF(backgroundPath.boundingRect().size() ))
        titleBackground.setTarget(QtCore.QPointF(0.0, titleShape.position().y()))

        self.display.insertShape(0, titleBackground)

        return titleBackground

    def readExampleDescription(self, parentNode):
        node = parentNode.firstChild()
        description = ""
        while not node.isNull():
            if node.isText():
                description += node.nodeValue()
            elif node.hasChildNodes():
                if node.nodeName() == "b":
                    beginTag = "<b>"
                    endTag = "</b>"
                elif node.nodeName() == "a":
                    beginTag = "<font color=\"white\">"
                    endTag = "</font>"
                elif node.nodeName() == "i":
                    beginTag = "<i>"
                    endTag = "</i>"
                elif node.nodeName() == "tt":
                    beginTag = "<tt>"
                    endTag = "</tt>"

                description += beginTag + self.readExampleDescription(node) + endTag

            node = node.nextSibling()

        return description

    def readInfo(self, resource, dir_):
        categoriesFile = QtCore.QFile(resource)
        document = QtXml.QDomDocument()
        document.setContent(categoriesFile)
        documentElement = document.documentElement()
        categoryNodes = documentElement.elementsByTagName("category")

        self.categories['[main]'] = {}
        self.categories['[main]']['examples'] = []
        self.categories['[main]']['color'] = QtGui.QColor("#FF3B3B")

        self.readCategoryDescription(dir_, '[main]')
        self.qtLogo.load(self.imagesDir.absoluteFilePath("sklogow.png"))
        self.rbLogo.load(self.imagesDir.absoluteFilePath("qt4-logo.png"))

        for i in range(categoryNodes.length()):
            elem = categoryNodes.item(i).toElement()
            categoryName = QtCore.QString(elem.attribute("name"))
            categoryDirName = QtCore.QString(elem.attribute("dirname"))
            categoryDocName = QtCore.QString(elem.attribute("docname"))
            categoryColor = QtGui.QColor(elem.attribute("color", "#eeeeee"))

            categoryDir = QtCore.QDir(dir_)

            if categoryDir.cd(categoryDirName):
                self.categories[categoryName] = {}

                self.readCategoryDescription(categoryDir, categoryName)

                self.categories[categoryName]['examples'] = []

                exampleNodes = elem.elementsByTagName("example")
                self.maximumLabels = max(self.maximumLabels, exampleNodes.length())

                # Only add those examples we can find.
                for j in range(exampleNodes.length()):
                    exampleDir = QtCore.QDir(categoryDir)

                    exampleNode = exampleNodes.item(j)
                    element = exampleNode.toElement()
                    exampleName = element.attribute("name")
                    exampleFileName = element.attribute("filename")

                    uniqueName = categoryName + "-" + exampleName

                    self.examples[uniqueName] = {}

                    if not categoryDocName.isEmpty():
                        docName = categoryDocName + "-" + exampleFileName + ".html"
                    else:
                        docName = categoryDirName + "-" + exampleFileName + ".html"

                    self.examples[uniqueName]['name'] = exampleName
                    self.examples[uniqueName]['document path'] = ""
                    self.findDescriptionAndImages(uniqueName, docName)

                    self.examples[uniqueName]['changedirectory'] = element.attribute("changedirectory", "true")
                    self.examples[uniqueName]['color'] = QtGui.QColor(element.attribute("color", "#C8C2F0"))

                    if element.attribute("executable", "true") != "true":
                        del self.examples[uniqueName]
                        continue

                    examplePath = None

                    if sys.platform == "win32":
                        examplePyName = exampleFileName + ".pyw"
                    else:
                        examplePyName = exampleFileName + ".py"

                    if exampleDir.exists(examplePyName):
                        examplePath = exampleDir.absoluteFilePath(examplePyName)
                    elif exampleDir.cd(exampleFileName):
                        if exampleDir.exists(examplePyName):
                            examplePath = exampleDir.absoluteFilePath(examplePyName)

                    if examplePath and not examplePath.isNull():
                        self.examples[uniqueName]['absolute path'] = exampleDir.absolutePath()
                        self.examples[uniqueName]['path'] = examplePath

                        self.categories[categoryName]['examples'].append(exampleName)
                    else:
                        del self.examples[uniqueName]

                self.categories[categoryName]['color'] = categoryColor

        return len(self.categories)

    def addVersionAndCopyright(self, rect):
        versionCaption = TitleShape(QtCore.QString("freedomtoaster@slobodnakultura.org"),
                                    self.font(), QtGui.QPen(QtGui.QColor(255,255,255,120)),
                                    QtCore.QPointF(rect.center().x(), rect.top()),
                                    QtCore.QSizeF(0.5*rect.width(), rect.height()),
                                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        versionCaption.metadata["fade"] = 15
        self.display.appendShape(versionCaption)

        copyrightCaption = TitleShape(QtCore.QString("Copyleft  2008 slobodnakultura.org"),
                                    self.font(), QtGui.QPen(QtGui.QColor(255,255,255,120)),
                                    QtCore.QPointF(rect.topLeft()),
                                    QtCore.QSizeF(0.5*rect.width(), rect.height()),
                                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        copyrightCaption.metadata["fade"] = 15
        self.display.appendShape(copyrightCaption)

    def fadeShapes(self):
        for i in range(0, self.display.shapesCount()):
            shape = self.display.shape(i)
            shape.metadata["fade"] = -15
            shape.metadata["fade minimum"] = 0

    def findDescriptionAndImages(self, uniqueName, docName):
        if self.documentationDir.exists(docName):
            self.examples[uniqueName]['document path'] = self.documentationDir.absoluteFilePath(docName)

            exampleDoc = QtXml.QDomDocument()

            exampleFile = QtCore.QFile(self.examples[uniqueName]['document path'])
            exampleDoc.setContent(exampleFile)

            paragraphs = exampleDoc.elementsByTagName("p")

            for p in range(paragraphs.length()):
                descriptionNode = paragraphs.item(p)
                description = self.readExampleDescription(descriptionNode)

                if QtCore.QString(description).indexOf(QtCore.QRegExp(QtCore.QString("((The|This) )?(%1 )?.*(example|demo)").arg(self.examples[uniqueName]['name']), QtCore.Qt.CaseInsensitive)) != -1:
                    self.examples[uniqueName]['description'] = description
                    break

            images = exampleDoc.elementsByTagName("img")
            imageFiles = []

            for i in range(images.length()):
                imageElement = images.item(i).toElement()
                source = QtCore.QString(imageElement.attribute("src"))
                if "-logo" not in source:
                    imageFiles.append(self.documentationDir.absoluteFilePath(source))

            if len(imageFiles) > 0:
                self.examples[uniqueName]['image files'] = imageFiles

    def newPage(self):
        self.slideshowTimer.stop()
        self.disconnect(self.slideshowTimer, QtCore.SIGNAL("timeout()"), self.updateExampleSummary)
        self.disconnect(self.display, QtCore.SIGNAL("displayEmpty()"), self.resizeWindow)

    def readCategoryDescription(self, categoryDir, categoryName):
##        categoryDirName = categoryDir.absolutePath()
##        if categoryDirName.find("examples") != -1:
##            categoryDirName = re.sub(".*/examples(.*)", r"%s\1" % QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.ExamplesPath), categoryDirName)
##        else:
##            categoryDirName = re.sub(".*/demos(.*)", r"%s\1" % QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.DemosPath), categoryDirName)
##        categoryDir = QtCore.QDir(categoryDirName)
        if categoryDir.exists("README"):
            file = QtCore.QFile(categoryDir.absoluteFilePath("README"))

            if not file.open(QtCore.QFile.ReadOnly):
                return

            inputStream = QtCore.QTextStream(file)

            paragraphs = []
            currentPara = []
            openQuote = True

            while not inputStream.atEnd():
                line = inputStream.readLine()

                at = line.indexOf("\"", 0)

                while at != -1:
                    if openQuote:
                        line.replace(at, 1, QtCore.QChar(QtCore.QChar.Punctuation_InitialQuote))
                    else:
                        line.replace(at, 1, QtCore.QChar(QtCore.QChar.Punctuation_FinalQuote))
                    openQuote = not openQuote
                    at = line.indexOf("\"", at)

                if not line.trimmed().isEmpty():
                    currentPara.append(str(line.trimmed()))
                elif len(currentPara) > 0:
                    paragraphs.append(" ".join(currentPara))
                    currentPara = []
                else:
                    break


            if len(currentPara) > 0:
                paragraphs.append(" ".join(currentPara))

            self.categories[categoryName]['description'] = "<p>"+"\n</p><p>".join(paragraphs)+"</p>"

    def slotShowPage(self):
        self.emit(QtCore.SIGNAL("showPage()"))
