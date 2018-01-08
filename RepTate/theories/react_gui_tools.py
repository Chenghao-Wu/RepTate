import numpy as np
from ctypes import *
from react_ctypes_helper import *
#BoB form
from PyQt5.QtWidgets import QDialog, QToolBar, QVBoxLayout, QDialogButtonBox, QLineEdit, QGroupBox, QFormLayout, QLabel, QFileDialog
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt5.QtCore import QSize

def initialise_tool_bar(self):
    #disable buttons 
    self.parent_dataset.actionMinimize_Error.setDisabled(True)
    # self.parent_dataset.actionCalculate_Theory.setDisabled(True)
    self.parent_dataset.actionShow_Limits.setDisabled(True)
    self.parent_dataset.actionVertical_Limits.setDisabled(True)
    self.parent_dataset.actionHorizontal_Limits.setDisabled(True)

    ######toolbar
    tb = QToolBar()
    tb.setIconSize(QSize(24,24))
    self.thToolsLayout.insertWidget(0, tb)

    #BOB settings buttons
    self.bob_settings_button = tb.addAction(QIcon(':/Icon8/Images/new_icons/icons8-bob-hat.png'), 'Edit BoB Binning Settings')
    self.save_bob_configuration_button = tb.addAction(QIcon(':/Icon8/Images/new_icons/icons8-money-box.png'), 'Save Polymer Configuration for BoB')
    #stop calculation button
    self.stop_calulation_button = tb.addAction(QIcon(':/Icon8/Images/new_icons/icons8-road-closure.png'), 'Stop Current Calulation')
    self.stop_calulation_button.setDisabled(True)

    #signals
    connection_id = self.bob_settings_button.triggered.connect(self.handle_edit_bob_settings)
    connection_id = self.save_bob_configuration_button.triggered.connect(self.handle_save_bob_configuration)
    connection_id = self.stop_calulation_button.triggered.connect(self.handle_stop_calulation)

def theory_buttons_disabled(self, state):
    self.bob_settings_button.setDisabled(state)
    self.save_bob_configuration_button.setDisabled(state)
    self.stop_calulation_button.setDisabled(not state)


def handle_stop_calulation(self):
    self.Qprint("Stop current calculation requested")
    self.stop_theory_calc_flag = True
    self.stop_calulation_button.setDisabled(True)



def handle_save_bob_configuration(parent):
    stars = '*************************\n'
    if parent.simexists:
        ndist = parent.ndist
        react_dist[ndist].contents.M_e = parent.parameters['Me'].value
        react_dist[ndist].contents.monmass = parent.parameters['mon_mass'].value

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_start = "data/React/polyconf.dat"
        dilogue_name = "Save"
        ext_filter = "Data Files (*.dat)"
        out_file = QFileDialog.getSaveFileName(parent, dilogue_name, dir_start, options=options)
        if out_file[0] == "":
            return
        # output polymers
        b_out_file = out_file[0].encode('utf-8')
        polyconfwrite(c_int(ndist), c_char_p(b_out_file))
        message = stars + 'Saved %d polymers in %s\n'%(react_dist[ndist].contents.nsaved, out_file[0]) + stars
    else:    
        message = stars + 'No simulation performed yet\n' + stars
    parent.Qprint(message)

def handle_edit_bob_settings(parent):
        ndist = parent.ndist
        numbobbins = react_dist[ndist].contents.numbobbins
        bobmax = np.power(10, react_dist[ndist].contents.boblgmax)
        bobmin = np.power(10, react_dist[ndist].contents.boblgmin)
        bobbinmax = react_dist[ndist].contents.bobbinmax

        d = EditBobSettingsDialog(parent, numbobbins, bobmax, bobmin, bobbinmax)
        if d.exec_():
            try:
                numbobbins = int(d.e1.text())
                bobmax = float(d.e2.text())
                bobmin = float(d.e3.text())
                bobbinmax = int(d.e4.text())
            except ValueError:
                pass
            react_dist[ndist].contents.numbobbins = c_int(numbobbins)
            react_dist[ndist].contents.boblgmax = c_double(np.log10(bobmax))
            react_dist[ndist].contents.boblgmin = c_double(np.log10(bobmin))
            react_dist[ndist].contents.bobbinmax = c_int(bobbinmax)

class EditBobSettingsDialog(QDialog):
    """Create the form that is used to modify the BoB binning settings"""

    def __init__(self, parent, numbobbins, bobmax, bobmin, bobbinmax):
        super().__init__(parent)
        self.createFormGroupBox(numbobbins, bobmax, bobmin, bobbinmax)
 
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
 
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setWindowTitle("Edit")
 
    def createFormGroupBox(self, numbobbins, bobmax, bobmin, bobbinmax):
        self.formGroupBox = QGroupBox("Edit BoB Binning Settings")
        layout = QFormLayout()
        
        val_double = QDoubleValidator()
        val_double.setBottom(0) #set smalled double allowed in the form
        val_int = QIntValidator()
        val_int.setBottom(0) #set smalled int allowed in the form
        
        self.e1 = QLineEdit()
        self.e1.setValidator(val_int)
        self.e1.setMaxLength(6)
        self.e1.setText("%d"%numbobbins)

        self.e2 = QLineEdit()
        self.e2.setValidator(val_double)
        self.e2.setText("%.2e"%bobmax)
        
        self.e3 = QLineEdit()
        self.e3.setValidator(val_double)
        self.e3.setText("%.2e"%bobmin)

        self.e4 = QLineEdit()
        self.e4.setValidator(val_int)
        self.e4.setMaxLength(6)
        self.e4.setText("%d"%bobbinmax)

        layout.addRow(QLabel("Number of bins for Bob:"), self.e1)
        layout.addRow(QLabel("Maximum bin Mw (g/mol):"), self.e2)
        layout.addRow(QLabel("Minimum bin Mw (g/mol):"), self.e3)
        layout.addRow(QLabel("Maximum no. of polymers per bin:"), self.e4)
        self.formGroupBox.setLayout(layout)
