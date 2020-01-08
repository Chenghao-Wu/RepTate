# RepTate: Rheology of Entangled Polymers: Toolkit for the Analysis of Theory and Experiments
# --------------------------------------------------------------------------------------------------------
#
# Authors:
#     Jorge Ramirez, jorge.ramirez@upm.es
#     Victor Boudara, victor.boudara@gmail.com
#
# Useful links:
#     http://blogs.upm.es/compsoftmatter/software/reptate/
#     https://github.com/jorge-ramirez-upm/RepTate
#     http://reptate.readthedocs.io
#
# --------------------------------------------------------------------------------------------------------
#
# Copyright (2020): Jorge Ramirez, Victor Boudara, Universidad Politécnica de Madrid, University of Leeds
#
# This file is part of RepTate.
#
# RepTate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RepTate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RepTate.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------------------------------------
"""Module TheoryMITlaos

Template file for creating a new theory
"""
import numpy as np
from CmdBase import CmdBase, CmdMode
from Parameter import Parameter, ParameterType, OptType
from Theory import Theory
from QTheory import QTheory
from DataTable import DataTable


class TheoryMITlaos(CmdBase):
    """[summary]
    
    [description]
    """
    thname = 'MIT laos'
    description = 'Process LAOS data using MITlaos-like routines'
    citations = 'R.H. Ewoldt, A.E.Hosoi and G.H. McKinley, J. Rheo. 52, 1427 (2008)'
    doi = 'http://doi.org/10.1122/1.2970095'

    def __new__(cls, name='', parent_dataset=None, axarr=None):
        """[summary]
        
        [description]
        
        Keyword Arguments:
            - name {[type]} -- [description] (default: {''})
            - parent_dataset {[type]} -- [description] (default: {None})
            - ax {[type]} -- [description] (default: {None})
        
        Returns:
            - [type] -- [description]
        """
        return GUITheoryMITlaos(
            name, parent_dataset,
            axarr) if (CmdBase.mode == CmdMode.GUI) else CLTheoryMITlaos(
                name, parent_dataset, axarr)


class BaseTheoryMITlaos:
    """[summary]
    
    [description]
    """
    #help_file = ''
    single_file = False  # False if the theory can be applied to multiple files simultaneously
    thname = TheoryMITlaos.thname
    citations = TheoryMITlaos.citations
    doi = TheoryMITlaos.doi

    def __init__(self, name='', parent_dataset=None, axarr=None):
        """
        **Constructor**
        
        Keyword Arguments:
            - name {[type]} -- [description] (default: {''})
            - parent_dataset {[type]} -- [description] (default: {None})
            - ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)
        self.function = self.MITlaos  # main theory function
        self.has_modes = False  # True if the theory has modes
        self.parameters['n'] = Parameter(
            name='n',
            value=15,
            description='Highest harmonic to consider in stress reconstruction',
            type=ParameterType.integer,
            opt_type=OptType.const)
        self.parameters['pq'] = Parameter(
            name='pq',
            value=50,
            description='Points per quarter cycle in FT reconstruction (20-500)',
            type=ParameterType.integer,
            opt_type=OptType.const)

    def get_modes(self):
        """[summary]
        
        [description]
        
        Returns:
            - [type] -- [description]
        """
        pass

    def set_modes(self):
        """[summary]
        
        [description]
        
        Arguments:

        """
        pass

    def destructor(self):
        """[summary]
        
        [description]
        
        Arguments:

        """
        pass

    def cycletrim_MITlaos(self, gamma, tau):
        d_zero=[]

        k=0 # k is a counter for the number of times gamma changes sign
        sign_gam = np.sign(gamma)
        for i in range(len(gamma)-1):
            if sign_gam[i] != sign_gam[i+1]:
                d_zero.append(i+1)  # index location after sign change
                k+=1

        lgth = len(d_zero)

        if lgth <= 1:
            #if there are 0 or 1 locations of gamma crossing zero,
            #it is impossible to extract the minimum of 1 cycle
        
            # give an output before exiting
            istrain = 0;
            istress = 0;
            N       = 0;
            istart  = 0;
            istop   = 0;
            return istrain, istress, N, istart, istop

        if lgth == 2:
            #if there are 2 locations where gamma crosses zero,
            #a fancy cycle trimming must be performed, which will NOT start with a
            #sine wave
            #SEQUENCE:  estimate points per cycle
            #           check if there are enough points for single cycle (Npts) (error if not)
            #           include final Npts of signal

            #estimate number of points per cycle
            Npts = (d_zero[1] - d_zero[0]) *2 
            
            if (len(gamma) < Npts): # if there are not enough points
                # give an output before exiting
                istrain = 0;
                istress = 0;
                N       = 0;
                istart  = 0;
                istop   = 0;
                return istrain, istress, N, istart, istop
            else: # if there are enough points
                istart = len(gamma) - Npts
                istop  = len(gamma)-1
                N = 1

        if lgth > 2:
            if (lgth/2 != np.round(lgth/2)):   # Check if lgth is odd
                istart = d_zero[0]
                istop  = d_zero[-1]-1
                N = (lgth - 1)/2
            else:
                istart = d_zero[0]
                istop  = d_zero[lgth-2] - 1;
                N = (lgth - 2)/2;

        istrain = gamma[istart:istop]
        istress = tau[istart:istop]

        return istrain, istress, N, istart, istop

    def FTtrig_MITlaos(self, f):
        """
        Find trigonometric Fourier Series components from FFT:
        f = A0 + SUM_n( An*cos(n*2*pi*t/T + Bn*sin(n*2*pi*t/T)

        VARIABLES
        f           vector to be transformed
        A0          essentially mean(f)
        An          cosine terms
        Bn          sine terms

        SEQUENCE
        force input to have EVEN number of data points (reqd for fft.m)
        take FFT > complex vector results
        extract trigonometric terms from complex vector
        """
        if int(len(f)/2) != len(f)/2:
            # trim last data point to force even number of data points
            # f MUST HAVE EVEN NUMBER OF DATA POINTS!
            f = f[0:len(f)-2]

        n=len(f)
        N=int(n/2)       # N will be the number of harmonics to consider

        Fn = np.fft.fft(f)
        # rearrange values such that: Fn_new = [ high < low | low > high ]
        Fn_new = np.array([np.conj(Fn[N])]+Fn[N+1:].tolist()+Fn[1:N].tolist())
        Fn_new /= n  # scale results

        #A0 = Fn_new[N]
        A0 = np.mean(f)
        An = 2*np.real(Fn_new[N+1:])    # cosine terms
        Bn = -2*np.imag(Fn_new[N+1:])   # sine terms

        return A0, An, Bn

    def do_error(self, line):
        self.Qprint('No error calculated in this theory')
        pass

    def MITlaos(self, f=None):
        """Template function that returns the square of y
        
        [description]
        
        Keyword Arguments:
            - f {[type]} -- [description] (default: {None})
        
        Returns:
            - [type] -- [description]
        """
        ft = f.data_table
        tt = self.tables[f.file_name_short]
        tt.num_columns = ft.num_columns

        time_uneven  = ft.data[:,0]  # raw time
        gamma_uneven = ft.data[:,1]  # raw strain
        tau_uneven =   ft.data[:,2]  # raw stress

        # Force strain & stress data to be linearly space in time
        time   = np.linspace(time_uneven[0],time_uneven[-1],len(time_uneven))
        gamma  = np.interp(time, time_uneven,gamma_uneven)  # untrimmed strain
        tauxy  = np.interp(time, time_uneven,tau_uneven)    # untrimmed stress

        # This section is equivilent to cycletrim 

        d_zero=[]

        k=0  # k is a counter for the number of times gamma changes sign
        sign_gam = np.sign(gamma);
        for i in range(len(gamma)-1):
            if sign_gam[i] != sign_gam[i+1]:
                k+=1
                d_zero.append(i+1) # index location after sign change

        # if the sign changed, and the previous point was NEGATIVE (or ZERO)
        # then it's the beginning of the sine wave

        # NB: the following assumes that strain signal is smooth enough so that the
        # cycles can be trimmed by finding the gamma=0 crossover points.

        lgth = len(d_zero)

        if lgth == 0:
            # give an output before exiting
            self.Qprint('ERROR: Selected data never crosses zero.  Unable to find integer number of cycles')
            return
            
        elif lgth == 1:   
            # if there are 0 or 1 locations of gamma crossing zero, it is impossible to extract the minimum of 1 cycle
            self.Qprint('WARNING: It looks like you have only one cycle, but this cannot be confirmed.')
            Ncycles = 1;
            istart  = 0;
            istop   = len(gamma)-1
            
            time = time[istart:istop]
            istrain     = gamma[istart:istop]
            istress     = tauxy[istart:istop]          
            
        elif lgth == 2:
            # if there are 2 locations where gamma crosses zero, a fancy cycle trimming must be performed, which will NOT start with a sine wave
            # SEQUENCE:  estimate points per cycle
            #           check if there are enough points for single cycle (Npts) (error if not)
            #           include final Npts of signal

            Npts = (d_zero[1] - d_zero[0] ) *2 # estimate number of points per cycle
            
            if len(gamma) < (0.95*Npts):  # if there are not enough points
                # give an output before exiting
                self.Qprint('WARNING: It looks like there aren''t enough points for a complete cycle. Proceed with extreme caution.')
                istart  = 0;
                istop   = len(gamma)-1
                Ncycles       = 1;
                
                time = time[istart:istop]
                istrain     = gamma[istart:istop]
                istress     = tauxy[istart:istop]
                
                
            elif len(gamma) > (1.05*Npts): #  check for excess data beyond one cycle (x% tolerance)
                istart = len(gamma) - Npts;
                istop  = len(gamma)-1
                Ncycles = 1;
                
                time = time[istart:istop]
                istrain     = gamma[istart:istop]
                istress     = tauxy[istart:istop]
                
                self.Qprint('WARNING: The beginning of your data was trimmed in order to have exactly one cycle')
            else:
                istart = 0
                istop  = len(gamma)-1
                Ncycles = 1
                
                time = time[istart:istop]
                istrain     = gamma[istart:istop]
                istress     = tauxy[istart:istop]
                self.Qprint('WARNING: It looks like you have exactly one cycle.  It will not be trimmed.')            
            
        elif lgth > 2:
            # perform cycle trimming as usual
            [gam, tau, Ncycles, istart, istop] = self.cycletrim_MITlaos(gamma, tauxy)
            time = time[istart:istop]

        n = self.parameters['n'].value
        self.maxharmonic = 0
        if Ncycles !=0:
            # finds max odd harmonic
            self.maxharmonic = int(np.floor(len(gam)/(2*Ncycles)))
            evencheck = self.maxharmonic/2
            if (evencheck == round(evencheck)):
                self.maxharmonic = self.maxharmonic-1
        self.Qprint('Max odd harminic = %d'%self.maxharmonic)

        n = min(n, self.maxharmonic)

        # FTtrig_MITlaos
        A0, AnS, BnS = self.FTtrig_MITlaos(tau)
        gA0, gAnS, gBnS = self.FTtrig_MITlaos(gam)

        gam_0 = np.sqrt( gBnS[Ncycles-1]**2 + gAnS[Ncycles-1]**2 )  # acknowledge possible phase shift, but neglect h.o.t.
        delta = np.atan( gAnS[Ncycles-1] / gBnS[Ncycles-1])         # raw signal phase shift

        An = np.zeros(len(AnS))
        Bn = np.zeros(len(BnS))
        for q in range(len(AnS)):  # Create NOT SHIFTED Fourier coefficients
            An[q] = AnS[q]*np.cos(q*delta/Ncycles) - BnS[q]*np.sin(q*delta/Ncycles)
            Bn[q] = BnS[q]*np.cos(q*delta/Ncycles) + AnS[q]*np.sin(q*delta/Ncycles)

        if abs(An[Ncycles-1]) > abs(Bn[Ncycles-1]):
            if An[Ncycles-1] < 0:
                An = -An
                Bn = -Bn
        else: # if the fundamental of Bn was larger, use it as the reference
            if Bn[Ncycles-1] < 0:
                An = -An
                Bn = -Bn

        PPC=4*self.parameters['pq'] #Points Per Cycle
        TP=6*PPQC+1 # Total Points: Points for Three Half-Cycles plus one for overlap

        gam_recon=np.zeros(PPC)
        for q in range(PPC): # sum for each point in time, 1 full cycle, no overlap
            gam_recon[q] = gam_0*np.sin(2*np.pi*q/PPC) # Reconstruct WITHOUT phase shift

        # make gam_recon 1.5 cycles with 1 point overlap
        gam_recon = np.array(gam_recon.tolist() + gam_recon[:2*PPQC].tolist())

        # w (omega) is currently a MANUAL input
        # strain-rate is equal to omega*strain-shifted-1/4-cycle
        w = float(f.file_parameters["omega"])
        gamdot_recon=w*gam_recon[PPQC:PPQC+PPC-1]  # One cylce of gamdot
        gamdot_recon = np.array(gamdot_recon.tolist() + gamdot_recon[:2*PPQC].tolist()) # make 1.5 cycles


        # HERE!!!
        tau_recon = zeros(PPC,1); # initialize tau_recon   (m harmonics included)
        FTtau_e = zeros(PPC,1);
        FTtau_v = zeros(PPC,1);

        tau_recon1 = zeros(PPC,1); # initialize tau_recon1 (1st harmonic only)
        tau_recon3 = zeros(PPC,1); # initialize tau_recon3 (1st & 3rd Harmonics)
        tau_e_3    = zeros(PPC,1); # "elastic" stress, from 1st & 3rd Harmonics
        tau_v_3    = zeros(PPC,1); # "viscous" stress, from 1st & 3rd Harmonics

        for q=1:PPC # sum for each point in time for 1 full cycle, no overlap
            for p=1:2:m # m:total number of harmonics to consider
                        # sum over ODD harmonics only
                tau_recon(q) = tau_recon(q) + Bn(Ncycles*p)*sin(p*2*pi*(q-1)/PPC) ...
                    + An(Ncycles*p)*cos(p*2*pi*(q-1)/PPC);
                
                FTtau_e(q)   = FTtau_e(q) + Bn(Ncycles*p)*sin(p*2*pi*(q-1)/PPC);
                FTtau_v(q)   = FTtau_v(q) + An(Ncycles*p)*cos(p*2*pi*(q-1)/PPC);

            end
            for p=1:3 # Now just the first 3 harmonics
                tau_recon3(q) = tau_recon3(q) + Bn(Ncycles*p)*sin(p*2*pi*(q)/PPC) ...
                    + An(Ncycles*p)*cos(p*2*pi*(q)/PPC);
            end
        #RHE, added June 15, 2007, trying to use FT to reconstruct "Chebyshev"
        #curves
            for p=1 #Now just the first harmonic
                tau_recon1(q) = tau_recon1(q) + Bn(Ncycles*p)*sin(p*2*pi*(q-1)/PPC) ...
                    + An(Ncycles*p)*cos(p*2*pi*(q-1)/PPC);
            end
            for p=1:2:3 #Harmonics 1 & 3, for "elastic" stress
                tau_e_3(q) = tau_e_3(q) + Bn(Ncycles*p)*sin(p*2*pi*(q-1)/PPC);
            end
            for p=1:2:3 #Harmonics 1 & 3, for "elastic" stress
                tau_v_3(q) = tau_v_3(q) + An(Ncycles*p)*cos(p*2*pi*(q-1)/PPC);
            end
        end


        #make FTtau_* have one point overlap
        FTtau_e(PPC+1,1)=FTtau_e(1);
        FTtau_v(PPC+1,1)=FTtau_v(1);
        tau_e_3(PPC+1,1)=tau_e_3(1);
        tau_v_3(PPC+1,1)=tau_v_3(1);
        #make tau_recon* 1.5 cycles with 1 point overlap
        tau_recon = [tau_recon; tau_recon(1:2*PPQC+1)];
        tau_recon3 = [tau_recon3; tau_recon3(1:2*PPQC+1)];

        tau_recon_Ncycles = [];
        for r=1:Ncycles
            tau_recon_Ncycles = [tau_recon_Ncycles; tau_recon(1:PPC)];
        end

        tau_recon_max = max(abs(tau_recon)); # 080422 RHE, for VEparameters data output


Xe=gam_recon(3*PPQC+1:5*PPQC+1)/gam_0; %gam_recon is 1.5 cycles
Xv=gamdot_recon(2*PPQC+1:4*PPQC+1)/(gam_0*w); %gamdot_recon is 1.5 cycles
% Create corresponding input function from Geo. Interp. decomposition
fe=[FTtau_e(3*PPQC+1:4*PPQC); FTtau_e(1:PPQC+1)]; %tau_e is 1 cycle
fv=FTtau_v(2*PPQC+1:4*PPQC+1); %tau_v is 1 cycle

fe3 =[tau_e_3(3*PPQC+1:4*PPQC); tau_e_3(1:PPQC+1)]; %tau_e is 1 cycle
fv3 = tau_v_3(2*PPQC+1:4*PPQC+1); %tau_v is 1 cycle

 An_e = chebyshev_decompose_MITlaos(fe,15,Xe);
 An_v = chebyshev_decompose_MITlaos(fv,15,Xv);

if Bn(Ncycles)>0  %ensure that G_1' is positive
    Gp = Bn/gam_0;  %G' from sine terms
else
    Gp = -Bn/gam_0;
end

if An(Ncycles) > 0  %ensure that G_1'' is positive
    Gpp = An/gam_0; %G'' from cosine terms
else 
    Gpp = -An/gam_0;
end

N=length(An); % number of available harmonics
G_complex = zeros(N,1);
G_compNORM = zeros(N,1);
for j=1:N
    G_complex(j)=(Gp(j)^2+Gpp(j)^2)^0.5;
end
for j=1:N
    G_compNORM(j) = G_complex(j)/G_complex(Ncycles); %max intensity occurs at Ncycles frequency
end

dn = 1/Ncycles;
% n = (dn:dn:maxharmonic);  % FTharmonicGUI_MITlaos.m calculation (but I changed it 080422 RHE)
n = (dn:dn:dn*length(Gp));  % I do NOT want to truncate at the largest odd, integer harmonic

% Chebyshev coefficients, found from FT results
e_n(1:floor(length(Gp)/Ncycles)) = zeros;
%contains e1, e2, e3, e4, ...
for o = 1:2:floor(length(Gp)/Ncycles)
    e_n(o) = Gp(Ncycles*o)*(-1)^((o-1)/2);  %only works for ODD Chebyshevs, so I leave even Chebyshevs = 0;
end


v_n(1:floor(length(Gp)/Ncycles)) = zeros;
for o = 1:2:floor(length(Gpp)/Ncycles)
    v_n(o) = Gpp(Ncycles*o)/w;   
    %I'm suppressing output of even Chebyshevs, since they should all = 0
    %due to reconstruction with only ODD FT harmonics
    %  See An_e and An_v for the true polynomial decomposition of the raw
    %  tau_elastic signal (but if even harmonics exist it's due due to
    %  noise in numerical calculation RHE
end

% 080422 RHE - Also determine the n-spectrum for the integer harmonics
n_integer = (1:1:length(e_n));

M=0;
Lo=0;
EtaM = 0;
EtaL = 0;
for p=1:2:m
    M = M + p*Gp(Ncycles*p);
    Lo = Lo + Gp(Ncycles*p)*(-1)^((p-1)/2);
    
    EtaM = EtaM + (1/w)*p*Gpp(Ncycles*p)*(-1)^((p-1)/2);
    EtaL = EtaL + (1/w)*Gpp(Ncycles*p);
end
%M
L=Lo;

S=L/M;
EtaT=EtaL/EtaM;

S2=(L-M)/L;



        tt.num_rows = len(time)
        tt.data = np.zeros((tt.num_rows, tt.num_columns))
        tt.data[:, 0] = time
        tt.data[:, 1] = gam
        tt.data[:, 2] = tau



class CLTheoryMITlaos(BaseTheoryMITlaos, Theory):
    """[summary]
    
    [description]
    """

    def __init__(self, name='', parent_dataset=None, axarr=None):
        """
        **Constructor**
        
        Keyword Arguments:
            - name {[type]} -- [description] (default: {''})
            - parent_dataset {[type]} -- [description] (default: {None})
            - ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)

    # This class usually stays empty


class GUITheoryMITlaos(BaseTheoryMITlaos, QTheory):
    """[summary]
    
    [description]
    """

    def __init__(self, name='', parent_dataset=None, axarr=None):
        """
        **Constructor**
        
        Keyword Arguments:
            - name {[type]} -- [description] (default: {''})
            - parent_dataset {[type]} -- [description] (default: {None})
            - ax {[type]} -- [description] (default: {None})
        """
        super().__init__(name, parent_dataset, axarr)

    # add widgets specific to the theory here:
