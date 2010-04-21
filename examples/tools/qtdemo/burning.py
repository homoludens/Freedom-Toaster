import sys
from PyQt4.QtGui import QApplication, QGridLayout, QLineEdit, \
               QPushButton,  QTextBrowser, \
               QWidget, QProgressBar
from PyQt4.QtCore import QProcess, \
                QString, QStringList,  QTimer, \
               SIGNAL, SLOT,QRegExp
import re
class Window(QWidget):
    __pyqtSignals__ = ("burningProgress(int)")
    __pyqtSignals__ = ("burningFinished()")
    __pyqtSignals__ = ("burningStartingIn(int)")
    __pyqtSignals__ = ("burningError(int)")
    
    def __init__(self):
        QWidget.__init__(self)
        self.rawstr3 = r"""(?:^Current:\s)(.*)"""
        self.rawstr2 = r"""(?:^.*?)(\d)(?:\sseconds\.$)"""
        self.rawstr = r"""(?:^.*Track .*?\d*\D*)(\d{1,})(?:\D*of.*?)(\d{1,})(?:.*?MB written.*$)"""
        self.compile_obj = re.compile(self.rawstr, re.MULTILINE)
        self.compile_obj_2 = re.compile(self.rawstr2, re.MULTILINE)
        self.compile_obj_3 = re.compile(self.rawstr3, re.MULTILINE)
        self.process = QProcess()
        self.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput)
        self.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors)
        self.connect(self.process, SIGNAL("finished(int)"), self.resetButtons)
        self.connect(self, SIGNAL("burningProgress(int)"), self.readProgress)
        
        self.noError=True
    
    def blankCommand(self):
        print "blankCDRW"
        b=QString("cdrecord -v dev=1000,0,0 --blank=fast") 
        a=b.split(" ")
        self.process.start(a.first(), a.mid(1))

         
        if  self.process.exitCode():
            print "exitCode"
            self.resetButtons()
            return
    
    
    
    def startCommand(self, isofile):
        print "startCommand"
        b=QString("cdrecord -v -pad speed=8 dev=/dev/cdrom "+isofile) 
        a=b.split(" ")
        self.process.start(a.first(), a.mid(1))

         
        if  self.process.exitCode():
            print "exitCode"
            self.resetButtons()
            return

    def stopCommand(self, i):
        self.resetButtons(i)
        self.process.terminate()
        QTimer.singleShot(5000, self.process, SLOT("kill()"))


    def readOutput(self):
        a= self.process.readAllStandardOutput().data()
        match_obj = self.compile_obj.search(a)
        match_obj_2 = self.compile_obj_2.search(a)
        match_obj_3 = self.compile_obj_3.search(a)
        print a
        if match_obj:
            all_groups = match_obj.groups()
            group_1 = float(match_obj.group(1))
            group_2 = float(match_obj.group(2))
            g=int(group_1*100.0/group_2)
            if group_1:
                self.emit(SIGNAL("burningProgress(int)"), g)
        
        if match_obj_2:
            group_1 = int(match_obj_2.group(1))
            print "group_1: "+str(group_1)
            if group_1: 
                self.emit(SIGNAL("burningStartingIn(int)"), group_1)
                
        if match_obj_3:
            group_1 = match_obj_3.group(1)
            if group_1 == "none":
                print "NO MEDIA"
                self.stopCommand(334)
            
        if a=="Re-load disk and hit \<CR\>":
            print "Non writable disc"
            self.stopCommand()

    def readProgress(self, g):
        print g


    def readErrors(self):
        a= self.process.readAllStandardError().data()
        print "ERORR: "+a
        if a.startswith("cdrecord: Try to load media by hand"):
            print "ERROR: Non writable disc"
            self.stopCommand(333)
        
    def resetButtons(self,  i):
        print "resetButtons"
        print i
        if i==0:
            if self.noError:
                self.emit(SIGNAL("burningFinished()"))
        if i==333:
            self.noError=False
            self.emit(SIGNAL("burningError(int)"), i)
        if i==334:
            self.noError=False
            self.emit(SIGNAL("burningError(int)"), i)
        if i==335:
            self.noError=False
            self.emit(SIGNAL("burningCanceled(int)"), i)
