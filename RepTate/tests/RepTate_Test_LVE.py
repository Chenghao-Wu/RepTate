# RepTate: Rheology of Entangled Polymers: Toolkit for the Analysis of Theory and Experiments
# http://blogs.upm.es/compsoftmatter/software/reptate/
# https://github.com/jorge-ramirez-upm/RepTate
# http://reptate.readthedocs.io
# Jorge Ramirez, jorge.ramirez@upm.es
# Victor Boudara, mmvahb@leeds.ac.uk
# Copyright (2017) Universidad Politécnica de Madrid, University of Leeds
# This software is distributed under the GNU General Public License. 
"""Module Reptate

Main program that launches the GUI.

""" 
import os
import sys
import getopt
sys.path.append('core')
sys.path.append('gui')
sys.path.append('console')
sys.path.append('applications')
sys.path.append('theories')
sys.path.append('visual')
from QApplicationManager import QApplicationManager
#from ApplicationManager import * #solved the issue with the matplot window not opening on Mac
from PyQt5.QtWidgets import QApplication
from SplashScreen import SplashScreen
from time import time, sleep

def start_RepTate(argv):
    """
    Main RepTate application. 
    
    :param list argv: Command line parameters passed to Reptate
    """
    GUI = True
    QApplication.setStyle("Fusion") #comment that line for a native look
    #for a list of available styles: "from PyQt5.QtWidgets import QStyleFactory; print(QStyleFactory.keys())"
    
    app = QApplication(sys.argv)
    ex = QApplicationManager()
    ex.show()
    
    ########################################################
    # THE FOLLOWING LINES ARE FOR TESTING A PARTICULAR CASE
    # Open a particular application
    ex.new_lve_window()
    
    #####################
    # TEST Likhtman-McLeish
    # Open a Dataset
    pi_dir = "data%sPI_LINEAR%s"%((os.sep,)*2)
    ex.applications["LVE1"].new_tables_from_files([
                                                   pi_dir + "PI_23.4k_T-35.tts",
                                                   pi_dir + "PI_33.6k_T-35.tts",
                                                   pi_dir + "PI_94.9k_T-35.tts",
                                                   pi_dir + "PI_225.9k_T-35.tts",
                                                   pi_dir + "PI_483.1k_T-35.tts",
                                                   pi_dir + "PI_634.5k_T-35.tts",
                                                   pi_dir + "PI_1131k_T-35.tts",
                                                   ])
    # Open a theory
    ex.applications["LVE1"].datasets["Set1"].new_theory("Likhtman-McLeish")
    # Minimize the theory
    ex.applications["LVE1"].datasets["Set1"].handle_actionMinimize_Error()


    #####################
    # TEST Carreau-Yasuda
    # Open a Dataset
    ex.new_lve_window()
    ex.applications["LVE2"].new_tables_from_files([
                                                   pi_dir + "PI_483.1k_T-35.tts",
                                                   ])
    # Switch the view
    ex.applications["LVE2"].view_switch("logetastar")
    # Open a theory
    ex.applications["LVE2"].datasets["Set1"].new_theory("CarreauYasudaTheory")
    # Minimize the theory
    ex.applications["LVE2"].datasets["Set1"].handle_actionMinimize_Error()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    start_RepTate(sys.argv[1:])
