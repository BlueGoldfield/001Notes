import sys
import os
import re
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

icons_dir = resource_path("icons")
print(icons_dir)

class mainWindow(QMainWindow):

    minimize = pyqtSignal()
    
    def __init__(self) -> None:
        super().__init__()
        global flags
        flags = self.windowFlags()
        self.file = None
        self.initUI()
        configs = self.load_config()
        print(configs)
        global worker
        worker = None
        RUN_PATH = "HKEY_CURRENT_USER\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run"
        self.settings = QSettings(RUN_PATH, QSettings.NativeFormat)
        try:
            if int(configs[0]) > 0:
                self.thread = QThread()
                worker = Worker(int(configs[0]), self.file)
                worker.moveToThread(self.thread)
                self.thread.started.connect(worker.run)
                self.thread.start()
            else:
                worker = None
            if configs[1] == "True":
                self.settings.setValue("mainWindow",sys.argv[0])
            else:
                self.settings.remove("mainWindow")
            if configs[4] == "True":
                try:
                    f = open('lastnote.txt', 'r')
                    temp = f.read()
                    Notepad.setText(temp)
                except Exception as e:
                    print(e)
            if configs[3] == "True":
                self.setWindowFlags(flags | Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        except Exception as e:
            print(e)
        self.show()

    def initUI(self) -> None:
        global Notepad
        Notepad = QTextEdit()
        self.setCentralWidget(Notepad)

        newAct = QAction(QIcon(icons_dir+'\\new.ico'), '&New Note', self)
        newAct.setShortcut('Ctrl+N')
        newAct.setStatusTip('Create a new note')
        newAct.triggered.connect(lambda: self.new())

        saveAct = QAction(QIcon(icons_dir+'\save.ico'), '&Save Note', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.setStatusTip('Save note')
        saveAct.triggered.connect(lambda: self.save())

        saveasAct = QAction(QIcon(icons_dir+'\save.ico'), '&Save Note As...', self)
        saveasAct.setShortcut('Ctrl+Shift+S')
        saveasAct.setStatusTip('Save note as...')
        saveasAct.triggered.connect(lambda: self.save_as())

        exitAct = QAction(QIcon(icons_dir+'\exit.ico'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit the application')
        exitAct.triggered.connect(qApp.quit)

        configAct = QAction(QIcon(icons_dir+'\edit.ico'), '&Preferences', self)
        configAct.setShortcut('Ctrl+P')
        configAct.setStatusTip('Change application settings')
        configAct.triggered.connect(lambda: self.show_config())

        themeAct = QAction(QIcon(icons_dir+'\\theme.ico'), '&Theme', self)
        themeAct.setShortcut('Ctrl+T')
        themeAct.setStatusTip('Stylize application')
        themeAct.triggered.connect(lambda: self.show_theme())

        helpAct = QAction(QIcon(icons_dir+'\help.ico'), '&Help', self)
        helpAct.setShortcut('F1')
        helpAct.setStatusTip('Get help')
        helpAct.triggered.connect(lambda: self.show_help())

        aboutAct = QAction(QIcon(icons_dir+'\\about.ico'), '&About...', self)
        aboutAct.setShortcut('Ctrl+B')
        aboutAct.setStatusTip('Know more about the application')
        aboutAct.triggered.connect(lambda: self.show_about())

        self.load_theme()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(newAct)
        fileMenu.addAction(saveAct)
        fileMenu.addAction(saveasAct)
        fileMenu.addAction(exitAct)
        ConfigMenu = menubar.addMenu('&Config')
        ConfigMenu.addAction(configAct)
        ConfigMenu.addAction(themeAct)
        HelpMenu = menubar.addMenu('&Help')
        HelpMenu.addAction(helpAct)
        HelpMenu.addAction(aboutAct)

        self.setGeometry(500, 500, 275, 325)
        self.setWindowTitle('001Notes')
        self.setWindowIcon(QIcon(icons_dir+'\main.ico'))

    def new(self) -> None:
        buttonReply = QMessageBox.question(
            self, 'Save Note', "Would you like to save your current note?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.save_as()
        self.setWindowTitle('001Notes - Untitled')
        self.file = None
        Notepad.clear()

    def save(self) -> None:
        if (self.file == None or self.file == 0):
            self.save_as()
        else:
            f = open(self.file, 'w')
            text = Notepad.toPlainText()
            f.write(text)
            f.close()

    def save_as(self) -> None:
        name = QFileDialog.getSaveFileName(self, 'Save File')
        try:
            f = open(name[0], 'w')
            text = Notepad.toPlainText()
            f.write(text)
            f.close()
            self.file = name[0]
            if worker is not None:
                worker.update(None, name[0])
            self.setWindowTitle(f"001Notes - {name[0].split('/')[-1]}")
        except Exception as e:
            print(e)

    def show_config(self) -> None:
        self.cfg = configWindow()
        self.cfg.closed.connect(lambda:self.update_config_live())
        self.cfg.closed.connect(lambda:self.load_config())

    def show_theme(self) -> None:
        self.theme = themeWindow()

    def show_help(self) -> None:
        self.help = helpWindow()

    def show_about(self) -> None:
        QMessageBox.about(self, 'About 001Notes', "001Notes is a simple, straightforward sticky notes program, made just because the developer felt Windows' Sticky Notes were trash.\n\n001Notes was developed by Rafael Zaccaro using Python and PyQt5.")

    def load_theme(self) -> None:
        try:
            f = open("user.theme", 'r')
            temp = f.read()
            final = temp.split('\n')
            Notepad.setTextColor(QColor(final[0]))
            Notepad.setStyleSheet("background-color: %s" % final[1])
            Notepad.setFont(QFont(final[2]))
        except Exception as e:
            print(e)
    
    def safe_save(self) -> None:
        f = open('lastnote.txt', 'w')
        text = Notepad.toPlainText()
        f.write(text)
        f.close()        
        sys.exit()
    
    def load_config(self) -> list:
        final = []
        try:
            f = open("config.cfg", 'r')
            temp = f.read()
            temp = temp.strip()
            temp = re.split('\n| : ', temp)
            for i in range(1, 11, 2):
                final.append(temp[i])
        except Exception as e:
            print(e)
        return final

    def update_config_live(self) -> None:
        configs = self.load_config()
        try:
            if worker is not None:
                    worker.update(int(configs[0]), None)
            if configs[3] == "True":
                self.setWindowFlags(flags | Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(flags)
            self.show()
        except Exception as e:
            print(e)

    def closeEvent(self, event) -> None:
        configs = self.load_config()

        try:
            if configs[2] == "True":
                self.setWindowFlags(self.windowFlags() | Qt.Tool)
                self.show()
                self.setFocus()
                self.minimize.emit()
                event.ignore()
            else: 
                event.accept()
        except Exception as e:
            print(e)
            event.accept()


class Worker(QThread):

        def __init__(self, interval, file):
            super().__init__()
            self.interval = interval
            self.file = file

        def run(self):
            print("running")
            i = 0
            while i < self.interval+1:
                time.sleep(60)
                print(i)
                i += 1
                if i == self.interval:
                    print("saved!")
                    if (self.file == None or self.file == 0):
                        f = open('autosave.txt', 'w')
                    else:
                        f = open(self.file, 'w')
                    text = Notepad.toPlainText()
                    f.write(text)
                    f.close()
                    i = 0
        
        def stop(self):
            print("stopping")
            self.running = False
        
        def update(self, interval=None, file=None):
            if interval != None:
                self.interval = interval
            if file != None:
                self.file = file


class configWindow(QWidget):

    closed = pyqtSignal()
    
    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):

        configs = self.load_config()

        autosave = QLabel()
        autosave.setText("Autosave Interval:\n(set 0 to disable autosaving)")
        self.autosaveField = QSpinBox()
        self.autosaveField.setRange(0, 120)
        self.autosaveField.setSuffix(' minutes')
        self.autostart = QCheckBox("Autostart with Windows?")
        self.minimize = QCheckBox("Minimize to tray on close?")
        self.staytop = QCheckBox("Stay on top?")
        self.lastfile = QCheckBox("Open last note on start?")
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(lambda: self.save_changes())
        discardButton = QPushButton("Discard")
        discardButton.clicked.connect(lambda: self.destroy())

        if configs == []:
            self.autosaveField.setValue(5)
            self.autostart.setChecked(False)
            self.minimize.setChecked(False)
            self.staytop.setChecked(False)
            self.lastfile.setChecked(False)
        else:
            self.autosaveField.setValue(int(configs[0]))
            self.autostart.setChecked(configs[1] == "True")
            self.minimize.setChecked(configs[2] == "True")
            self.staytop.setChecked(configs[3] == "True")
            self.lastfile.setChecked(configs[4] == "True")

        grid = QGridLayout()
        grid.addWidget(autosave, 0, 0, 1, 2)
        grid.addWidget(self.autosaveField, 1, 0, 1, 2)
        grid.addWidget(self.autostart, 2, 0, 1, 2)
        grid.addWidget(self.minimize, 3, 0, 1, 2)
        grid.addWidget(self.staytop, 4, 0, 1, 2)
        grid.addWidget(self.lastfile, 5, 0, 1, 2)
        grid.addWidget(saveButton, 6, 0, 1, 1)
        grid.addWidget(discardButton, 6, 1, 1, 1)

        self.setLayout(grid)
        self.setWindowTitle('001Notes Settings')
        self.setWindowIcon(QIcon(icons_dir+'\edit.ico'))
        
    def save_changes(self) -> None:
        try:
            f = open("config.cfg", 'w')
            text = (f"AutoSaveInterval : {self.autosaveField.value()}\n"
                    f"AutoStartWithWindows : {self.autostart.isChecked()}\n"
                    f"MinimizeOnClose : {self.minimize.isChecked()}\n"
                    f"StayOnTop : {self.staytop.isChecked()}\n"
                    f"OpenLastFile : {self.lastfile.isChecked()}"
                    )
            f.write(text)
            f.close()
        except Exception as e:
            print(e)
        self.close()
    
    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)

    def load_config(self) -> list:
        final = []
        try:
            f = open("config.cfg", 'r')
            temp = f.read()
            temp = temp.strip()
            temp = re.split('\n| : ', temp)
            for i in range(1, 11, 2):
                final.append(temp[i])
        except Exception as e:
            print(e)
        return final
    

class themeWindow(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.initUI()

    def initUI(self) -> None:
        CPLabel = QLabel()
        CPLabel.setText("Select font color:")
        self.bgcolorPreview = ColorButton()
        FCLabel = QLabel()
        FCLabel.setText("Select background color:")
        self.fcolorPreview = ColorButton()
        self.fontButton = QPushButton("Font")
        self.fontButton.clicked.connect(lambda: self.chooseFont())
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(lambda: self.save_changes())
        discardButton = QPushButton("Discard")
        discardButton.clicked.connect(lambda: self.destroy())

        self.load_theme()

        grid = QGridLayout()
        grid.addWidget(CPLabel, 0, 0)
        grid.addWidget(self.bgcolorPreview, 0, 1)
        grid.addWidget(FCLabel, 1, 0)
        grid.addWidget(self.fcolorPreview, 1, 1)
        grid.addWidget(self.fontButton, 2, 0, 1, 2)
        grid.addWidget(saveButton, 6, 0, 1, 1)
        grid.addWidget(discardButton, 6, 1, 1, 1)

        self.setLayout(grid)
        self.setWindowTitle('001Notes Theme')
        self.setWindowIcon(QIcon(icons_dir+'\theme.ico'))
        self.show()

    def chooseFont(self) -> None:
        font, valid = QFontDialog.getFont()
        if valid:
            name = font.toString().split(',')
            self.fontButton.setText(name[0])
            Notepad.setFont(font)

    def save_changes(self) -> None:
        try:
            f = open("user.theme", 'w')
            text = (f"{self.bgcolorPreview.color()}\n"
                    f"{self.fcolorPreview.color()}\n"
                    f"{Notepad.font().toString()}")
            f.write(text)
            f.close()
            Notepad.setTextColor(QColor(self.bgcolorPreview.color()))
            Notepad.setStyleSheet("background-color: %s" % self.fcolorPreview.color())
        except Exception as e:
            print(e)
        self.close()

    def load_theme(self) -> None:
        try:
            f = open("user.theme", 'r')
            temp = f.read()
            final = temp.split('\n')
            self.bgcolorPreview.setColor(final[0])
            self.fcolorPreview.setColor(final[1])
            self.fontButton.setText(final[2].split(',')[0])
        except Exception as e:
            print(e)


class helpWindow(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        self.treeView = QTreeView()
        self.treeView.setHeaderHidden(True)

        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()

        help = StandardItem('Help', 16, set_bold=True)

        hotkeys = StandardItem('Hotkeys', 14)
        configs = StandardItem('Settings', 14)
        saving = StandardItem('Saving', 14)
        contact = StandardItem('Contact', 14)
        help.appendRows([hotkeys, configs, saving, contact])

        autosaveinterval = StandardItem('• Autosave Interval')
        autostart = StandardItem('• Autostart with Windows')
        minimize = StandardItem('• Minimize to tray on close')
        staytop = StandardItem('• Stay on top')
        openlast = StandardItem('• Open last Note on start')
        configs.appendRows([autosaveinterval, autostart, minimize, staytop, openlast])
        
        autosave = StandardItem('• Autosaving')
        lastnote = StandardItem('• Last Note')
        saving.appendRows([autosave, lastnote])

        developer = StandardItem('• Developer Contact')
        contact.appendRow(developer)

        rootNode.appendRow(help)
        self.treeView.setModel(treeModel)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.treeView.selectionModel().selectionChanged.connect(lambda:self.show_info())

        grid = QGridLayout()
        grid.addWidget(self.treeView, 0, 0, 2, 1)
        grid.addWidget(self.details, 0, 1, 2, 1)

        self.setLayout(grid)
        self.setWindowTitle('001Notes Help')
        self.setWindowIcon(QIcon(icons_dir+'\help.ico'))

    def show_info(self) -> None:
        index = self.treeView.currentIndex()
        if index.model().data(index) == "Hotkeys":
            self.details.setHtml("<h1>001Notes Hotkeys</h1><hr><ul><li><h3>New Note: <code>Ctrl + N</code>;</h4></li><li><h3>Save Note: <code>Ctrl + S</code>;</h4></li><li><h3>Save Note as: <code>Ctrl + Shift + S</code>;</h4></li><li><h3>Quit: <code>Ctrl + Q</code>;</h4></li></ul><hr><ul><li><h3>Open Config Menu: <code>Ctrl + P</code>;</h4></li><li><h3>Open Theme Menu: <code>Ctrl + T</code>;</h4></li></ul><hr><ul><li><h3>Open Help Menu: <code>F1</code>;</h4></li><li><h3>Open About Message: <code>Ctrl + B</code>;</h4></li></ul>")
        elif index.model().data(index) == "• Autosave Interval":
            self.details.setHtml("<h1>Autosave Interval</h1><hr><h3>The Autosave Interval defines the rate at which your Note will be automatically saved. Keep in mind the input number represents minutes. Set the number to 0 in order to disable the Autosave feature.<br>Minimum time: 1 minute;<br>Maximum time: 2 hours (120 minutes);</h3>")
        elif index.model().data(index) == "• Autostart with Windows":
            self.details.setHtml("<h1>Autostart with Windows</h1><hr><h3>If enabled, 001Notes will start everytime you boot Windows.</h3><h4>This feature might slow down the startup process of older or less potent computers.</h4>")
        elif index.model().data(index) == "• Minimize to tray on close":
            self.details.setHtml("<h1>Minimize to tray on close</h1><hr><h3>Instead of closing the application, its taskbar icon gets hidden on the system tray. After that, you can right click it to either open it up again or close the application entirely.</h3>")
        elif index.model().data(index) == "• Stay on top":
            self.details.setHtml("<h1>Stay on top</h1><hr><h3>Forces the application to stay on top of other windows.</h3>")
        elif index.model().data(index) == "• Open last Note on start":
            self.details.setHtml("<h1>Open last Note on start</h1><hr><h3>Saves what you had written on the application temporarily, so you don't lose it if the app closed unexpectedly, and opens it at start when you get back.</h3>")
        elif index.model().data(index) == "• Autosaving":
            self.details.setHtml("<h1>Autosaving</h1><hr><h3>Automatically saves the Note you're currently writing. If it has not been saved yet, it will be saved as \"autosave.txt\". You can choose the rate of autosave in the configuration menu.</h3>")
        elif index.model().data(index) == "• Last Note":
            self.details.setHtml("<h1>Last Note</h1><hr><h3>Stores the Note you're currently writing and opens it up again at start. Useful if you don't want to actually save the Note but continue editing it later.</h3>")
        elif index.model().data(index) == "• Developer Contact":
            self.details.setHtml("<h1>Contact the Developer</h1><hr /><ul><li><h3>E-mail: <a href=\"mailto:rafael.zaccaro@yahoo.com\">rafael.zaccaro@yahoo.com</a></h3></li><li><h3>Discord: Rafaeł#9171</h3></li><li><h3>GitHub: <a href=\"https://github.com/BlueGoldfield\">www.github.com/BlueGoldfield</a></h3></li><li><h3>LinkedIn: <a href=\"https://www.linkedin.com/in/rafael-zaccaro\">www.linkedin.com/in/rafael-zaccaro</a></h3></li><li><h3>Portfolio: <a href=\"https://rafael-zaccaro.cloudno.de\">rafael-zaccaro.cloudno.de</a></h3></li></ul>")


class StandardItem(QStandardItem):
    def __init__(self, txt='', font_size=12, set_bold=False, color=QColor(0, 0, 0)):
        super().__init__()

        fnt = QFont('Open Sans', font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setForeground(color)
        self.setFont(fnt)
        self.setText(txt)


class ColorButton(QPushButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    '''

    colorChanged = pyqtSignal(object)

    def __init__(self, *args, color=None, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self._default = color
        self.pressed.connect(self.onColorPicker)

        # Set the initial/default state.
        self.setColor(self._default)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        self.setStyleSheet("")
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        dlg = QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.setColor(self._default)

        return super(ColorButton, self).mousePressEvent(e)

def main() -> None:
    app = QApplication(sys.argv)
    mw = mainWindow()
    app.aboutToQuit.connect(lambda:mw.safe_save())

    tray = QSystemTrayIcon()
    tray.setIcon(QIcon(icons_dir+'\main.ico'))
    mw.minimize.connect(lambda:tray.setVisible(True))
    
    menu = QMenu()
    open = QAction("Open 001Notes")
    open.triggered.connect(lambda:mw.setWindowFlags(flags))
    open.triggered.connect(lambda:mw.show())
    open.triggered.connect(lambda:tray.setVisible(False))
    menu.addAction(open)
    
    quit = QAction("Quit 001Notes")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)
    
    tray.setContextMenu(menu)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()