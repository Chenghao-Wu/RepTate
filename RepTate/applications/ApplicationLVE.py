from Application import *
import numpy as np
#from TheoryMaxwellModes import TheoryMaxwellModesTime

class ApplicationLVE(Application):
    """Application to Analyze Linear Viscoelastic Data
       TODO: DO WE NEED A SEPARATE APPLICATION FROM TTS???
    """
    name="LVE"
    description="Linear Viscoelasticity"
    
    def __init__(self, name="LVE", parent = None):
        super(ApplicationLVE, self).__init__(name, parent)

        # VIEWS
        self.views.append(View("Log(G',G''(w))", "Log Storage,Loss moduli", "Log($\omega$)", "Log(G'($\omega$),G''($\omega$))", False, False, self.viewLogG1G2, 2, ["G'(w)","G''(w)"]))
        self.views.append(View("G',G''(w)", "Storage,Loss moduli", "$\omega$", "G'($\omega$),G''($\omega$)", True, True, self.viewG1G2, 2, ["G'(w)","G''(w)"]))
        self.views.append(View("delta", "delta", "$\omega$", "$\delta(\omega)$", True, False, self.viewDelta, 1, ["delta(w)"]))
        self.views.append(View("tan(delta)", "tan(delta)", "$\omega$", "tan($\delta$)", True, True, self.viewTanDelta, 1, ["tan(delta((w))"]))
        self.current_view=self.views[0]

        # FILES
        ftype=TXTColumnFile("LVE files", "tts", "LVE files", 0, -1, ['w','G\'','G\'\''], [0, 1, 2], ['Mw','T'], ['rad/s','Pa','Pa'])
        self.filetypes[ftype.extension]=ftype

        # THEORIES
        #self.theories[TheoryMaxwellModesTime.thname]=TheoryMaxwellModesTime

    def viewLogG1G2(self, vec, file_parameters):
        x=np.zeros((1,1))
        y=np.zeros((1,2))
        x[0]=np.log10(vec[0])
        y[0,0]=np.log10(vec[1])
        y[0,1]=np.log10(vec[2])
        return x, y, True

    def viewG1G2(self, vec, file_parameters):
        x=np.zeros((1,1))
        y=np.zeros((1,2))
        x[0]=vec[0]
        y[0,0]=vec[1]
        y[0,1]=vec[2]
        return x, y, True

    def viewDelta(self, vec, file_parameters):
        x=np.zeros((1,1))
        y=np.zeros((1,1))
        x[0]=vec[0]
        y[0,0]=np.arctan2(vec[2],vec[1])*180/np.pi
        return x, y, True
    
    def viewTanDelta(self, vec, file_parameters):
        x=np.zeros((1,1))
        y=np.zeros((1,1))
        x[0]=vec[0]
        y[0,0]=np.log10(vec[1]/vec[0])
        return x, y, True