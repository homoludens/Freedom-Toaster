import sys
from PyQt4.QtGui import QApplication, QGridLayout, QLineEdit, \
               QPushButton,  QTextBrowser, \
               QWidget, QProgressBar
from PyQt4.QtCore import QProcess, \
                QString, QStringList,  QTimer, \
               SIGNAL, SLOT,QRegExp
import re
class Window(QWidget):
 
    def __init__(self):

        QWidget.__init__(self)
        self.rawstr = r"""(?:^.*Track .*?\d*\D*)(\d{1,})(?:\D*of.*?)(\d{1,})(?:.*?MB written.*$)"""
        self.compile_obj = re.compile(self.rawstr, re.MULTILINE)
        
        self.textBrowser = QTextBrowser(self)
        self.lineEdit = QLineEdit(self)
        self.startButton = QPushButton(self.tr("Start"), self)
        self.stopButton = QPushButton(self.tr("Stop"), self)
        self.stopButton.setEnabled(False)
        
        self.list1 = QStringList()
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.startCommand)
        self.connect(self.startButton, SIGNAL("clicked()"), self.startCommand)
        self.connect(self.stopButton, SIGNAL("clicked()"), self.stopCommand)

        layout = QGridLayout(self)
        layout.setSpacing(8)
        layout.addWidget(self.textBrowser, 0, 0)
        layout.addWidget(self.lineEdit, 1, 0)
        layout.addWidget(self.startButton, 1, 1)
        layout.addWidget(self.stopButton, 1, 2)

 
        self.process = QProcess()
        self.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput)
        self.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors)
        self.connect(self.process, SIGNAL("finished(int)"), self.resetButtons)

    def startCommand(self):
        a=self.lineEdit.text().split(" ")
        self.process.start(a.first(), a.mid(1))

        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.textBrowser.clear()

         
        if  self.process.exitCode():
            self.textBrowser.setText(
                QString("*** Failed to run %1 ***").arg(self.lineEdit.text())
                )
            self.resetButtons()
            return

    def stopCommand(self):
        self.resetButtons()
        self.process.terminate()
        QTimer.singleShot(5000, self.process, SLOT("kill()"))


    def readOutput(self):
        a= self.process.readAllStandardOutput().data()
        match_obj = self.compile_obj.search(a)
        
        if match_obj:
            all_groups = match_obj.groups()
            group_1 = float(match_obj.group(1))
            group_2 = float(match_obj.group(2))
            g=int(group_1*100.0/group_2)
            if group_1:
                self.textBrowser.append(QString(str(g)))

    def readErrors(self):
        a= self.process.readAllStandardError().data()
        self.textBrowser.append("error: " + QString(a))
        
    def resetButtons(self,  i):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = Window()
    #app.setMainWidget(window)
    window.show()

    sys.exit(app.exec_())
