# RepTate: Rheology of Entangled Polymers: Toolkit for the Analysis of Theory and Experiments
# http://blogs.upm.es/compsoftmatter/software/reptate/
# https://github.com/jorge-ramirez-upm/RepTate
# http://reptate.readthedocs.io
# Jorge Ramirez, jorge.ramirez@upm.es
# Victor Boudara, mmvahb@leeds.ac.uk
# Copyright (2017) Universidad Politécnica de Madrid, University of Leeds
# This software is distributed under the GNU General Public License.
"""Module QTheory

Module that defines the GUI counterpart of the class Theory.

"""
#from PyQt5.QtCore import *
import sys
from PyQt5.uic import loadUiType
from CmdBase import CmdBase, CalcMode
from Theory import Theory
from os.path import dirname, join, abspath
from PyQt5.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QFrame, QHeaderView, QMessageBox, QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QButtonGroup
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from Parameter import OptType

PATH = dirname(abspath(__file__))
Ui_TheoryTab, QWidget = loadUiType(join(PATH, 'theorytab.ui'))

# def trap_exc_during_debug(*args):
#     # when app raises uncaught exception, print info
#     print(args)

# # install exception hook: without this, uncaught exception would cause application to exit
# sys.excepthook = trap_exc_during_debug


class CalculationThread(QObject):
    sig_done = pyqtSignal()

    def __init__(self, fthread, *args):
        super().__init__()
        self.args = args
        self.function = fthread

    def work(self):
        self.function(*self.args)
        self.sig_done.emit()


class GetModesDialog(QDialog):
    def __init__(self, parent=None, th_dict={}):
        super(GetModesDialog, self).__init__(parent)

        self.setWindowTitle("Get Maxwell modes")
        layout = QVBoxLayout(self)

        self.btngrp = QButtonGroup()

        for item in th_dict.keys():
            rb = QRadioButton(item, self)
            layout.addWidget(rb)
            self.btngrp.addButton(rb)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # static method to create the dialog and return (date, time, accepted)
    #@staticmethod
    #def getMaxwellModesProvider(self, parent = None, th_dict = {}):
    #    dialog = GetModesDialog(parent, th_dict)
    #    result = dialog.exec_()
    #    return (self.btngrp.checkedButton().text(), result == QDialog.Accepted)


class QTheory(Ui_TheoryTab, QWidget, Theory):
    """[summary]
    
    [description]
    """

    def __init__(self, name="QTheory", parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {"QTheory"})
            parent_dataset {[type]} -- [description] (default: {None})
            axarr {[type]} -- [description] (default: {None})
        """
        super().__init__(name=name, parent_dataset=parent_dataset, axarr=axarr)
        self.setupUi(self)

        #build the therory widget
        self.thParamTable.setIndentation(0)
        self.thParamTable.setColumnCount(3)
        self.thParamTable.setHeaderItem(
            QTreeWidgetItem(["Parameter", "Value", "Error"]))
        # self.thParamTable.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.thParamTable.header().resizeSections(QHeaderView.ResizeToContents)
        self.thParamTable.setAlternatingRowColors(True)
        self.thParamTable.setFrameShape(QFrame.NoFrame)
        self.thParamTable.setFrameShadow(QFrame.Plain)
        self.thParamTable.setEditTriggers(self.thParamTable.NoEditTriggers)

        self.thTextBox.setReadOnly(True)

        self.stop_theory_calc_flag = False
        self.thread_calc_busy = False
        self.thread_fit_busy = False

        connection_id = self.thParamTable.itemDoubleClicked.connect(
            self.onTreeWidgetItemDoubleClicked)
        connection_id = self.thParamTable.itemChanged.connect(
            self.handle_parameterItemChanged)

    def handle_actionCalculate_Theory(self):
        self.thread_calc_busy = True
        #disable buttons
        self.parent_dataset.actionCalculate_Theory.setDisabled(True)
        self.parent_dataset.actionNew_Theory.setDisabled(True)
        try:
            self.theory_buttons_disabled(
                True)  # TODO: Add that function to all theories
        except AttributeError:  #the function is not defined in the current theory
            pass
        if CmdBase.calcmode == CalcMode.multithread:
            self.worker = CalculationThread(
                self.do_calculate,
                "",
            )
            self.worker.sig_done.connect(self.end_thread_calc)
            self.thread_calc = QThread()
            self.worker.moveToThread(self.thread_calc)
            self.thread_calc.started.connect(self.worker.work)
            self.thread_calc.start()
        elif CmdBase.calcmode == CalcMode.singlethread:
            self.do_calculate("")
            self.end_thread_calc()

    def end_thread_calc(self):
        if CmdBase.calcmode == CalcMode.multithread:
            try:
                self.thread_calc.quit()
            except:
                pass
        if self.stop_theory_calc_flag:  #calculation stopped by user
            self.stop_theory_calc_flag = False  #reset flag
        else:
            self.update_parameter_table()
            for file in self.theory_files(
            ):  #copy theory data to the plot series
                tt = self.tables[file.file_name_short]
                for nx in range(self.parent_dataset.nplots):
                    view = self.parent_dataset.parent_application.multiviews[
                        nx]
                    x, y, success = view.view_proc(tt, file.file_parameters)
                    for i in range(tt.MAX_NUM_SERIES):
                        if (i < view.n):
                            tt.series[nx][i].set_data(x[:, i], y[:, i])

            self.parent_dataset.parent_application.update_Qplot()

        self.thread_calc_busy = False
        #enable buttons
        self.parent_dataset.actionCalculate_Theory.setDisabled(False)
        self.parent_dataset.actionNew_Theory.setDisabled(False)
        try:
            self.theory_buttons_disabled(
                False)  # TODO: Add that function to all theories
        except AttributeError:  #the function is not defined in the current theory
            pass

    def handle_actionMinimize_Error(self):
        """Minimize the error
        
        [description]
        """
        self.thread_fit_busy = True
        #disable buttons
        self.parent_dataset.actionMinimize_Error.setDisabled(True)
        self.parent_dataset.actionNew_Theory.setDisabled(True)
        try:
            self.theory_buttons_disabled(
                True)  # TODO: Add that function to all theories
        except AttributeError:  #the function is not defined in the current theory
            pass
        if CmdBase.calcmode == CalcMode.multithread:
            self.worker = CalculationThread(
                self.do_fit,
                "",
            )
            self.worker.sig_done.connect(self.end_thread_fit)
            self.thread_fit = QThread()
            self.worker.moveToThread(self.thread_fit)
            self.thread_fit.started.connect(self.worker.work)
            self.thread_fit.start()
        elif CmdBase.calcmode == CalcMode.singlethread:
            self.do_fit("")
            self.end_thread_fit()

    def end_thread_fit(self):
        if CmdBase.calcmode == CalcMode.multithread:
            try:
                self.thread_fit.quit()
            except:
                pass
        self.update_parameter_table()
        self.parent_dataset.parent_application.update_Qplot()
        self.thread_fit_busy = False
        #enable buttons
        self.parent_dataset.actionMinimize_Error.setDisabled(False)
        self.parent_dataset.actionNew_Theory.setDisabled(False)
        try:
            self.theory_buttons_disabled(
                False)  # TODO: Add that function to all theories
        except AttributeError:  #the function is not defined in the current theory
            pass

    def update_parameter_table(self):
        """Update the theory parameter table
        
        [description]
        """
        #clean table
        self.thParamTable.clear()

        #populate table
        for param in self.parameters:
            p = self.parameters[param]
            if p.display_flag:  #only allowed param enter the table
                if p.opt_type == OptType.const:
                    item = QTreeWidgetItem(
                        self.thParamTable,
                        [p.name, "%0.3g" % p.value, "N/A"])
                    item.setCheckState(0, Qt.PartiallyChecked)
                    item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                else:
                    try:
                        err = "%0.3g" % p.error
                    except:
                        err = "-"
                    item = QTreeWidgetItem(
                        self.thParamTable,
                        [p.name, "%0.3g" % p.value, err])
                    if p.opt_type == OptType.opt:
                        item.setCheckState(0, Qt.Checked)
                    elif p.opt_type == OptType.nopt:
                        item.setCheckState(0, Qt.Unchecked)

                item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.thParamTable.header().resizeSections(QHeaderView.ResizeToContents)

    def onTreeWidgetItemDoubleClicked(self, item, column):
        """Start editing text when a table cell is double clicked
        
        [description]
        
        Arguments:
            item {[type]} -- [description]
            column {[type]} -- [description]
        """
        if (column == 1):
            self.thParamTable.editItem(item, column)
            # thcurrent = self.parent_dataset.TheorytabWidget.currentWidget()
            # thcurrent.editItem(item, column)

    def handle_parameterItemChanged(self, item, column):
        """Modify parameter values when changed in the theory table
        
        [description]
        
        Arguments:
            item {[type]} -- [description]
            column {[type]} -- [description]
        """
        param_changed = item.text(0)
        if column == 0:  #param was checked/unchecked
            if item.checkState(0) == Qt.Checked:
                self.parameters[param_changed].opt_type = OptType.opt
            elif item.checkState(0) == Qt.Unchecked:
                self.parameters[param_changed].opt_type = OptType.nopt
            return
        #else, assign the entered value
        new_value = item.text(1)
        message, success = self.set_param_value(param_changed, new_value)
        if (not success):
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            if message != '':
                msg.setText("Not a valid value\n" + message)
            else:
                msg.setText("Not a valid value")
            msg.exec_()
            item.setText(1, str(self.parameters[param_changed].value))

    def Qcopy_modes(self):
        """[summary]
        
        [description]
        """
        apmng = self.parent_dataset.parent_application.parent_manager
        G, S = apmng.list_theories_Maxwell(th_exclude=self)
        if G:
            d = GetModesDialog(self, G)
            if (d.exec_() and d.btngrp.checkedButton() != None):
                item = d.btngrp.checkedButton().text()
                tau, G0 = G[item]()
                tauinds = (-tau).argsort()
                tau = tau[tauinds]
                G0 = G0[tauinds]
                self.set_modes(tau, G0)

            #item, success = GetModesDialog.getMaxwellModesProvider(parent=self, th_dict=G)
            #print(item)

            #d = QDialog(self, )
            #layout = QVBoxLayout(d)
            #d.setLayout(layout)
            #for item in G.keys():
            #    rb = QRadioButton(item, d)
            #    layout.addWidget(rb)
            #d.setWindowTitle("Select provider of Maxwell modes:")
            #d.setWindowModality(Qt.ApplicationModal)
            #d.exec_()