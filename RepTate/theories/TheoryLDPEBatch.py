# RepTate: Rheology of Entangled Polymers: Toolkit for the Analysis of Theory and Experiments
# http://blogs.upm.es/compsoftmatter/software/reptate/
# https://github.com/jorge-ramirez-upm/RepTate
# http://reptate.readthedocs.io
# Jorge Ramirez, jorge.ramirez@upm.es
# Victor Boudara, mmvahb@leeds.ac.uk
# Daniel Read, d.j.read@leeds.ac.uk
# Copyright (2017) Universidad Politécnica de Madrid, University of Leeds
# This software is distributed under the GNU General Public License.
"""Module TheoryTobitaBatch

TobitaBatch file for creating a new theory
"""
import sys
import numpy as np
import time
from CmdBase import CmdBase, CmdMode
from Parameter import Parameter, ParameterType, OptType
from Theory import Theory
from QTheory import QTheory
from DataTable import DataTable
from PyQt5.QtWidgets import QToolBar, QTableWidget, QDialog, QVBoxLayout, QDialogButtonBox, QTableWidgetItem, QSizePolicy, QFileDialog, QLineEdit, QGroupBox, QFormLayout
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication
from collections import OrderedDict

import ctypes as ct
import react_ctypes_helper as rch
import react_gui_tools as rgt


class TheoryTobitaBatch(CmdBase):
    """LDPE batch reaction theory
    
    The LDPE batch reaction theory uses an algorithm described in the paper by H.
Tobita (J. Pol. Sci. Part B, 39, 391-403 (2001)). It is designed for a batch
reaction - in which the reagents are well mixed at the beginning and monomer
is consumed as the reaction proceeds. It is equivalent to the "plug-flow"
approximation for a tubular reactor. One possibility when modelling a real
tubular reactor is to mix several batch reactions with different conversions.
    """
    thname = 'TobitaBatchTheory'
    description = 'The LDPE batch reaction theory'
    citations = 'J. Pol. Sci. Part B, 39, 391-403 (2001)'

    def __new__(cls, name='ThTobitaBatch', parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {'ThTobitaBatch'})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        
        Returns:
            [type] -- [description]
        """
        return GUITheoryTobitaBatch(
            name, parent_dataset,
            axarr) if (CmdBase.mode == CmdMode.GUI) else CLTheoryTobitaBatch(
                name, parent_dataset, axarr)


class BaseTheoryTobitaBatch():
    """[summary]
    
    [description]
    """
    single_file = True  # False if the theory can be applied to multiple files simultaneously
    signal_request_dist = pyqtSignal(object)
    signal_request_polymer = pyqtSignal(object)
    signal_request_arm = pyqtSignal(object)

    def __init__(self, name='ThTobitaBatch', parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {'ThTobitaBatch'})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)

        self.reactname = "LDPE batch %d" % (rch.tb_global.tobbatchnumber)
        rch.tb_global.tobbatchnumber += 1
        self.function = self.Calc
        self.simexists = False
        self.dist_exists = False
        self.ndist = 0
        self.has_modes = False  # True if the theory has modes

        self.parameters = OrderedDict(
        )  # keep the dictionary key in order for the parameter table
        self.parameters['tau'] = Parameter(
            name='tau',
            value=0.002,
            description='tau',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['beta'] = Parameter(
            name='beta',
            value=0.0,
            description='beta',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['Cb'] = Parameter(
            name='Cb',
            value=0.02,
            description='Cb',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['Cs'] = Parameter(
            name='Cs',
            value=0.0005,
            description='Cs',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['fin_conv'] = Parameter(
            name='fin_conv',
            value=0.4,
            description='fin_conv',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['num_to_make'] = Parameter(
            name='num_to_make',
            value=1000,
            description='number of molecules made in the simulation',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['mon_mass'] = Parameter(
            name='mon_mass',
            value=28,
            description=
            'this is the mass, in a.m.u., of a monomer (usually set to 28 for PE)',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['Me'] = Parameter(
            name='Me',
            value=1000,
            description='the entanglement molecular weight',
            type=ParameterType.real,
            opt_type=OptType.const)
        self.parameters['nbin'] = Parameter(
            name='nbin',
            value=100,
            description='number of bins',
            type=ParameterType.real,
            opt_type=OptType.const)

        self.signal_request_dist.connect(rgt.request_more_dist)
        self.signal_request_polymer.connect(rgt.request_more_polymer)
        self.signal_request_arm.connect(rgt.request_more_arm)

    def Calc(self, f=None):
        # var
        # i,nbins,numtomake,m:integer
        # fin_conv, tau, beta, Cb, Cs, monmass, Me:double

        # get parameters
        tau = self.parameters['tau'].value
        beta = self.parameters['beta'].value
        Cb = self.parameters['Cb'].value
        Cs = self.parameters['Cs'].value
        fin_conv = self.parameters['fin_conv'].value
        numtomake = np.round(self.parameters['num_to_make'].value)
        monmass = self.parameters['mon_mass'].value
        Me = self.parameters['Me'].value
        nbins = int(np.round(self.parameters['nbin'].value))

        c_ndist = ct.c_int()

        #resize theory datatable
        ft = f.data_table
        ft = f.data_table
        tt = self.tables[f.file_name_short]
        tt.num_columns = ft.num_columns
        tt.num_rows = 1
        tt.data = np.zeros((tt.num_rows, tt.num_columns))

        if not self.dist_exists:
            success = rch.request_dist(ct.byref(c_ndist))
            self.ndist = c_ndist.value
            if not success:  # no dist available
                #launch dialog asking for more dist
                self.signal_request_dist.emit(
                    self)  #use signal to open QDialog in the main GUI window
                return
            else:
                self.dist_exists = True
        ndist = self.ndist
        # rch.react_dist[ndist].name = self.reactname #TODO: set the dist name in the C library
        rch.react_dist[ndist].contents.polysaved = False

        if self.simexists:
            rch.return_dist_polys(ct.c_int(ndist))

        # initialise tobita batch
        rch.tobbatchstart(
            ct.c_double(fin_conv), ct.c_double(tau), ct.c_double(beta),
            ct.c_double(Cs), ct.c_double(Cb), ct.c_int(ndist))
        rch.react_dist[ndist].contents.npoly = 0

        rch.react_dist[ndist].contents.M_e = Me
        rch.react_dist[ndist].contents.monmass = monmass
        rch.react_dist[ndist].contents.nummwdbins = nbins
        c_m = ct.c_int()

        # make numtomake polymers
        i = 0
        while i < numtomake:
            if self.stop_theory_calc_flag:
                self.print_signal.emit('Polymer creation stopped by user')
                break
            # get a polymer
            success = rch.request_poly(ct.byref(c_m))
            m = c_m.value
            if success:  # check availability of polymers
                # put it in list

                if rch.react_dist[
                        ndist].contents.npoly == 0:  # case of first polymer made
                    rch.react_dist[ndist].contents.first_poly = m
                    rch.set_br_poly_nextpoly(
                        ct.c_int(m),
                        ct.c_int(0))  # br_poly[m].contents.nextpoly = 0
                else:  # next polymer, put to top of list
                    rch.set_br_poly_nextpoly(
                        ct.c_int(m),
                        ct.c_int(rch.react_dist[ndist].contents.first_poly)
                    )  # br_poly[m].contents.nextpoly = rch.react_dist[ndist].contents.first_poly
                    rch.react_dist[ndist].contents.first_poly = m

                # make a polymer
                if rch.tobbatch(ct.c_int(m), ct.c_int(
                        ndist)):  # routine returns false if arms ran out
                    rch.react_dist[ndist].contents.npoly += 1
                    i += 1
                    # check for error
                    if rch.tb_global.tobitabatcherrorflag:
                        self.print_signal.emit(
                            'Polymers too large: gelation occurs for these parameters'
                        )
                        i = numtomake
                else:  # error message if we ran out of arms
                    self.success_increase_memory = None
                    self.signal_request_arm.emit(self)
                    while self.success_increase_memory is None:  # wait for the end of QDialog
                        time.sleep(
                            0.5
                        )  # TODO: find a better way to wait for the dialog thread to finish
                    if self.success_increase_memory:
                        continue  # back to the start of while loop
                    else:
                        i = numtomake
                        rch.tb_global.tobitabatcherrorflag = True

                # update on number made
                if rch.react_dist[ndist].contents.npoly % np.trunc(
                        numtomake / 20) == 0:
                    self.print_signal.emit(
                        'Made %d polymers' %
                        rch.react_dist[ndist].contents.npoly)
                    QApplication.processEvents(
                    )  # needed to use Qprint if in single-thread

            else:  # polymer wasn't available
                self.success_increase_memory = None
                self.signal_request_polymer.emit(self)
                while self.success_increase_memory is None:
                    time.sleep(
                        0.5
                    )  # TODO: find a better way to wait for the dialog thread to finish
                if self.success_increase_memory:
                    continue
                else:
                    i = numtomake
        # end make polymers loop

        calc = 0
        # do analysis of polymers made
        if (rch.react_dist[ndist].contents.npoly >=
                100) and (not rch.tb_global.tobitabatcherrorflag):
            rch.molbin(ndist)
            #resize theory datatable
            ft = f.data_table
            ft = f.data_table
            tt = self.tables[f.file_name_short]
            tt.num_columns = ft.num_columns
            tt.num_rows = rch.react_dist[ndist].contents.nummwdbins
            tt.data = np.zeros((tt.num_rows, tt.num_columns))

            for i in range(1, rch.react_dist[ndist].contents.nummwdbins + 1):
                tt.data[i - 1, 0] = np.power(
                    10, rch.react_dist[ndist].contents.lgmid[i])
                tt.data[i - 1, 1] = rch.react_dist[ndist].contents.wt[i]
                tt.data[i - 1, 2] = rch.react_dist[ndist].contents.avg[i]
                tt.data[i - 1, 3] = rch.react_dist[ndist].contents.avbr[i]

            self.print_signal.emit('*************************')
            # self.print_signal.emit('End of calculation \"%s\"'%rch.react_dist[ndist].contents.name)
            self.print_signal.emit(
                'Made %d polymers' % rch.react_dist[ndist].contents.npoly)
            self.print_signal.emit('Saved %d polymers in memory' %
                                   rch.react_dist[ndist].contents.nsaved)
            self.print_signal.emit(
                'Mn = %.3g' % rch.react_dist[ndist].contents.m_n)
            self.print_signal.emit(
                'Mw = %.3g' % rch.react_dist[ndist].contents.m_w)
            self.print_signal.emit(
                'br/1000C = %.3g' % rch.react_dist[ndist].contents.brav)
            self.print_signal.emit('*************************')

            calc = rch.react_dist[ndist].contents.nummwdbins - 1
            rch.react_dist[ndist].contents.polysaved = True

        self.simexists = True
        self.print_signal.emit(
            '%d arm records left in memory' % rch.pb_global.arms_left)
        return calc

    def destructor(self):
        """Return arms to pool"""
        rch.return_dist(ct.c_int(self.ndist))

    def do_error(self, line):
        pass

    def get_modes(self):
        """[summary]
        
        [description]
        
        Returns:
            [type] -- [description]
        """
        pass

    def set_modes(self):
        """[summary]
        
        [description]
        
        Arguments:

        """
        pass


class CLTheoryTobitaBatch(BaseTheoryTobitaBatch, Theory):
    """[summary]
    
    [description]
    """

    def __init__(self, name='ThTobitaBatch', parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {'ThTobitaBatch'})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)

    # This class usually stays empty


class GUITheoryTobitaBatch(BaseTheoryTobitaBatch, QTheory):
    """[summary]
    
    [description]
    """

    def __init__(self, name='ThTobitaBatch', parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {'ThTobitaBatch'})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)
        rgt.initialise_tool_bar(self)

    def theory_buttons_disabled(self, state):
        """Disable/Enable some theory buttons before/after calculation start."""
        rgt.theory_buttons_disabled(self, state)

    def handle_stop_calulation(self):
        """Kindly request the stop of the calculation thread."""
        rgt.handle_stop_calulation(self)

    def handle_save_bob_configuration(self):
        """Save polymer configuraions to a file"""
        rgt.handle_save_bob_configuration(self)

    def handle_edit_bob_settings(self):
        """Open the BoB binnig settings dialog"""
        rgt.handle_edit_bob_settings(self)
