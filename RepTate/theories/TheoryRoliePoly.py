# RepTate: Rheology of Entangled Polymers: Toolkit for the Analysis of Theory and Experiments
# http://blogs.upm.es/compsoftmatter/software/reptate/
# https://github.com/jorge-ramirez-upm/RepTate
# http://reptate.readthedocs.io
# Jorge Ramirez, jorge.ramirez@upm.es
# Victor Boudara, mmvahb@leeds.ac.uk
# Copyright (2017) Universidad Politécnica de Madrid, University of Leeds
# This software is distributed under the GNU General Public License. 
"""Module TheoryRoliePoly

Module for the Rolie-Poly theory for the non-linear flow of entangled polymers.

""" 
import numpy as np
from scipy.integrate import ode, odeint
from CmdBase import CmdBase, CmdMode
from Parameter import Parameter, ParameterType
from Theory import Theory
from QTheory import QTheory
from DataTable import DataTable
from PyQt5.QtWidgets import QToolBar, QToolButton, QMenu, QStyle, QSpinBox
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from Theory_rc import *

class TheoryRoliePoly(CmdBase):
    """Rolie-Poly
    
    [description]
    """
    thname="RoliePoly"
    description="RoliePoly"
    citations="Likhtman, A.E. & Graham, R.S.\n\
Simple constitutive equation for linear polymer melts derived from molecular theory: Rolie-Poly equation\n\
J. Non-Newtonian Fluid Mech., 2003, 114, 1-12"
    single_file = False

    def __new__(cls, name="ThRoliePoly", parent_dataset=None, ax=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {"ThMaxwellFrequency"})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        
        Returns:
            [type] -- [description]
        """
        return GUITheoryRoliePoly(name, parent_dataset, ax) if (CmdBase.mode==CmdMode.GUI) else CLTheoryRoliePoly(name, parent_dataset, ax)


class BaseTheoryRoliePoly:
    """[summary]
    
    [description]
    """
    def __init__(self, name="ThRoliePoly", parent_dataset=None, ax=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {"ThRoliePoly"})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, ax)
        self.function = self.RoliePoly
        self.has_modes = True
        self.parameters["beta"]=Parameter(name="beta", value=0.5, description="CCR coefficient", 
                                          type=ParameterType.real, min_flag=False)
        self.parameters["delta"]=Parameter(name="delta", value=-0.5, description="CCR exponent", 
                                           type=ParameterType.real, min_flag=False)
        self.parameters["lmax"]=Parameter(name="lmax", value=10.0, description="Maximum extensibility", 
                                          type=ParameterType.real, min_flag=False)
        self.parameters["nmodes"]=Parameter(name="nmodes", value=2, description="Number of modes", 
                                          type=ParameterType.integer, min_flag=False, display_flag=False)
        self.parameters["nstretch"]=Parameter(name="nstretch", value=2, description="Number of strecthing modes", 
                                          type=ParameterType.integer, min_flag=False, display_flag=False)
        for i in range(self.parameters["nmodes"].value):
            self.parameters["G%02d"%i]=Parameter(name="G%02d"%i, value=1000.0, description="Modulus of mode %02d"%i, 
                                               type=ParameterType.real, min_flag=False, display_flag=False, 
                                               bracketed=True, min_value=0)
            self.parameters["tauD%02d"%i]=Parameter(name="tauD%02d"%i, value=10.0, description="Terminal time of mode %02d"%i,
                                                  type=ParameterType.real, min_flag=False, display_flag=False,
                                                  bracketed=True, min_value=0)
            self.parameters["tauR%02d"%i]=Parameter(name="tauR%02d"%i, value=0.5, description="Rouse time of mode %02d"%i,
                                                  type=ParameterType.real, min_flag=True, 
                                                  bracketed=True, min_value=0)

        self.view_LVEenvelope = False
        auxseries = ax.plot([], [], label='')
        self.LVEenvelopeseries = auxseries[0]
        self.LVEenvelopeseries.set_marker('')
        self.LVEenvelopeseries.set_linestyle('--')
        self.LVEenvelopeseries.set_visible(self.view_LVEenvelope)
        self.LVEenvelopeseries.set_color('green')
        self.LVEenvelopeseries.set_linewidth(5)
        self.LVEenvelopeseries.set_label('')

        self.MAX_MODES = 40

    def get_modes(self):
        """[summary]
        
        [description]
        
        Returns:
            [type] -- [description]
        """
        nmodes=self.parameters["nmodes"].value
        tau=np.zeros(nmodes)
        G=np.zeros(nmodes)
        for i in range(nmodes):
            tau[i]=self.parameters["tauD%02d"%i].value
            G[i]=self.parameters["G%02d"%i].value
        return tau, G

    def set_modes(self, tau, G):
        """[summary]
        
        [description]
        
        Arguments:
            tau {[type]} -- [description]
            G {[type]} -- [description]
        """
        nmodes=len(tau)
        self.set_param_value("nmodes", nmodes)
        self.set_param_value("nstretch", nmodes)

        for i in range(nmodes):
            self.set_param_value("tauD%02d"%i,tau[i])
            self.set_param_value("G%02d"%i,G[i])
            self.set_param_value("tauR%02d"%i,0.5)

    def sigmadotshear(self, sigma, t, p):
        """Rolie-Poly differential equation under shear flow
        
        [description]
        
        Arguments:
            sigma {array} -- vector of state variables, sigma = [sxx, syy, sxy]
            t {float} -- time
            p {array} -- vector of the parameters, p = [tauD, tauR, beta, delta, gammadot]
        """
        sxx, syy, sxy = sigma
        tauD, tauR, beta, delta, gammadot = p
    
        # Create the vector with the time derivative of sigma
        trace_sigma = sxx + 2*syy
        aux1 = 2*(1-np.sqrt(3/trace_sigma))/tauR
        aux2 = beta*(trace_sigma/3)**delta
        return [2*gammadot*sxy - (sxx-1)/tauD - aux1*(sxx + aux2*(sxx-1)), -1.0*(syy-1)/tauD - aux1*(syy + aux2*(syy-1)), gammadot*syy - sxy/tauD - aux1*(sxy + aux2*sxy)]

        
    def RoliePoly(self, f=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            f {[type]} -- [description] (default: {None})
        
        Returns:
            [type] -- [description]
        """
        ft=f.data_table
        tt=self.tables[f.file_name_short]
        tt.num_columns=ft.num_columns
        tt.num_rows=ft.num_rows
        tt.data=np.zeros((tt.num_rows, tt.num_columns))
        tt.data[:,0]=ft.data[:,0]
        
        # ODE solver parameters
        abserr = 1.0e-8
        relerr = 1.0e-6
        t = ft.data[:,0]
        t = np.concatenate([[0],t])
        sigma0 = [1.0, 1.0, 0.0] # sxx, syy, sxy 
        beta = self.parameters["beta"].value
        delta = self.parameters["delta"].value
        gammadot = float(f.file_parameters["gdot"])
        nmodes = self.parameters["nmodes"].value
        for i in range(nmodes):
            tauD = self.parameters["tauD%02d"%i].value
            tauR = self.parameters["tauR%02d"%i].value
            p = [tauD, tauR, beta, delta, gammadot]
            sig = odeint(self.sigmadotshear, sigma0, t, args=(p,), atol=abserr, rtol=relerr)
            tt.data[:,1] += self.parameters["G%02d"%i].value*np.delete(sig[:,2],[0]) #return sxy
        
        # return stress to agree with input data file (t, eta)
        #tt.data[:,1] = tt.data[:,1]/gammadot

class CLTheoryRoliePoly(BaseTheoryRoliePoly, Theory):
    """[summary]
    
    [description]
    """
    def __init__(self, name="ThRoliePoly", parent_dataset=None, ax=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {"ThMaxwellFrequency"})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, ax)

class GUITheoryRoliePoly(BaseTheoryRoliePoly, QTheory):
    """[summary]
    
    [description]
    """
    def __init__(self, name="ThRoliePoly", parent_dataset=None, ax=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            name {[type]} -- [description] (default: {"ThMaxwellFrequency"})
            parent_dataset {[type]} -- [description] (default: {None})
            ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, ax)

        # add widgets specific to the theory
        tb = QToolBar()
        tb.setIconSize(QSize(24,24))

        self.tbutflow = QToolButton()
        self.tbutflow.setPopupMode(QToolButton.MenuButtonPopup)
        menu = QMenu()
        self.shear_flow_action = menu.addAction(QIcon(':/Icon8/Images/new_icons/icons8-garden-shears.png'), "Shear Flow")
        self.extensional_flow_action = menu.addAction(QIcon(':/Icon8/Images/new_icons/icons8-socks.png'), "Extensional Flow")
        self.tbutflow.setDefaultAction(self.shear_flow_action)
        self.tbutflow.setMenu(menu)
        tb.addWidget(self.tbutflow)

        self.tbutmodes = QToolButton()
        self.tbutmodes.setPopupMode(QToolButton.MenuButtonPopup)
        menu = QMenu()
        self.get_modes_action = menu.addAction(self.style().standardIcon(getattr(QStyle, 'SP_DialogYesButton')), "Get Modes")
        self.edit_modes_action = menu.addAction(QIcon(':/Icon8/Images/new_icons/icons8-edit-file.png'), "Edit Modes")
        self.plot_modes_action = menu.addAction(QIcon(':/Icon8/Images/new_icons/icons8-scatter-plot.png'), "Plot Modes")
        self.tbutmodes.setDefaultAction(self.get_modes_action)
        self.tbutmodes.setMenu(menu)
        tb.addWidget(self.tbutmodes)

        self.linearenvelope = tb.addAction(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogListView')), 'Show Linear Envelope')
        self.linearenvelope.setCheckable(True)
        self.linearenvelope.setChecked(False)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, self.MAX_MODES) # min and max number of modes
        self.spinbox.setSuffix(" Rmodes")
        self.spinbox.setValue(self.parameters["nmodes"].value) #initial value
        tb.addWidget(self.spinbox)

        self.thToolsLayout.insertWidget(0, tb)

        connection_id = self.shear_flow_action.triggered.connect(self.select_shear_flow)
        connection_id = self.extensional_flow_action.triggered.connect(self.select_extensional_flow)
        connection_id = self.get_modes_action.triggered.connect(self.get_modes_reptate)
        connection_id = self.edit_modes_action.triggered.connect(self.edit_modes_window)
        connection_id = self.plot_modes_action.triggered.connect(self.plot_modes_graph)
        connection_id = self.linearenvelope.triggered.connect(self.show_linear_envelope)

    def show_linear_envelope(self):
        self.LVEenvelopeseries.set_visible(self.linearenvelope.isChecked())
        self.plot_theory_stuff()
        self.parent_dataset.parent_application.update_plot()
       
    def plot_theory_stuff(self):
        """[summary]
        
        [description]
        """
        data_table_tmp = DataTable(self.ax)
        data_table_tmp.num_columns = 2
        data_table_tmp.num_rows = 100
        data_table_tmp.data=np.zeros((100, 2))
        
        times=np.logspace(-2, 3, 100)
        data_table_tmp.data[:,0] = times
        nmodes = self.parameters["nmodes"].value
        data_table_tmp.data[:,1] = 0
        fparamaux={}
        fparamaux["gdot"]=1e-6;
        for i in range(nmodes):
            G = self.parameters["G%02d"%i].value 
            tauD = self.parameters["tauD%02d"%i].value
            data_table_tmp.data[:,1] += G * tauD * (1-np.exp(-times/tauD)) * 1e-6
        view = self.parent_dataset.parent_application.current_view
        try:
            x, y, success = view.view_proc(data_table_tmp, fparamaux)
        except TypeError as e:
            print(e)
            return
        self.LVEenvelopeseries.set_data(x[:,0], y[:,0])      

        
    def select_shear_flow(self):
        self.tbutflow.setDefaultAction(self.shear_flow_action)

    def select_extensional_flow(self):
        self.tbutflow.setDefaultAction(self.extensional_flow_action)

    def get_modes_reptate(self):
        self.Qcopy_modes()

    def edit_modes_window(self):
        pass

    def plot_modes_graph(self):
        pass

    def set_param_value(self, name, value):
        """[summary]
        
        [description]
        
        Arguments:
            name {[type]} -- [description]
            value {[type]} -- [description]
        """
        if (name=="nmodes"):
            oldn=self.parameters["nmodes"].value
        super(GUITheoryRoliePoly, self).set_param_value(name, value)
        if (name=="nmodes"):
            for i in range(self.parameters["nmodes"].value):
                self.parameters["G%02d"%i]=Parameter(name="G%02d"%i, value=1000.0, description="Modulus of mode %02d"%i, 
                                                   type=ParameterType.real, min_flag=False, display_flag=False, 
                                                   bracketed=True, min_value=0)
                self.parameters["tauD%02d"%i]=Parameter(name="tauD%02d"%i, value=10.0, description="Terminal time of mode %02d"%i,
                                                      type=ParameterType.real, min_flag=False, display_flag=False,
                                                      bracketed=True, min_value=0)
                self.parameters["tauR%02d"%i]=Parameter(name="tauR%02d"%i, value=0.5, description="Rouse time of mode %02d"%i,
                                                      type=ParameterType.real, min_flag=True, 
                                                      bracketed=True, min_value=0)
            if (oldn>self.parameters["nmodes"].value):
                for i in range(self.parameters["nmodes"].value,oldn):
                    del self.parameters["G%02d"%i]
                    del self.parameters["tauD%02d"%i]
                    del self.parameters["tauR%02d"%i]
