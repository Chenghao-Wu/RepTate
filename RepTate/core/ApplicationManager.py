import os
import cmd
import sys
import logging
import logging.handlers
import readline
import glob
import matplotlib.pyplot as plt

from ApplicationTest import *
from ApplicationReact import *
from ApplicationMWD import *
from ApplicationTTS import *
from ApplicationLVE import *
from ApplicationNLVE import *
from ApplicationGt import *

class ApplicationManager(cmd.Cmd):
    """Main Reptate container of applications"""

    version = '0.3'
    prompt = 'reptate> '
    intro = 'Reptate Version %s command processor'%version
    
    def preloop(self):
        print("Starting Reptate...")
        super(ApplicationManager,self).preloop()

    def postloop(self):
        print ("Exiting RepTate...")

    def __init__ (self, parent=None):
        """Constructor """
        cmd.Cmd.__init__(self)        

        # SETUP LOG
        self.reptatelogger = logging.getLogger('ReptateLogger')
        self.reptatelogger.setLevel(logging.DEBUG) # INFO, WARNING
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        #log_file_name = 'reptate.log'
        #handler = logging.handlers.RotatingFileHandler(
        #    log_file_name, maxBytes=20000, backupCount=2, mode='w')
        #MainWindow.reptatelogger.addHandler(handler)

        # SETUP READLINE, COMMAND HISTORY FILE, ETC
        readline.read_history_file()

        # SETUP APPLICATIONS
        self.application_counter=0
        self.applications=[]
        self.available_applications={}
        self.available_applications[ApplicationTest.name]=ApplicationTest
        self.available_applications[ApplicationReact.name]=ApplicationReact
        self.available_applications[ApplicationMWD.name]=ApplicationMWD
        self.available_applications[ApplicationTTS.name]=ApplicationTTS
        self.available_applications[ApplicationLVE.name]=ApplicationLVE
        self.available_applications[ApplicationNLVE.name]=ApplicationNLVE
        self.available_applications[ApplicationGt.name]=ApplicationGt
        self.current_application=None

# APPLICATION STUFF
    def do_application_available(self, line):
        """List available applications"""
        for app in list(self.available_applications.values()):
            print("%s: %s"%(app.name,app.description))

    def do_application_delete(self, name):
        """Delete an open application"""
        done=False
        for index, app in enumerate(self.applications):
            if (app.name==name):
                if (self.current_application==app):
                    if (index<len(self.applications)-1):
                        self.current_application=self.applications[index+1]
                    else:
                        self.current_application=self.applications[0]
                self.applications.remove(app)
                done=True
        if (not done):
            print("Application \"%s\" not found"%name)            

    def complete_application_delete(self, text, line, begidx, endidx):
        """Complete delete application command"""
        app_names=[]
        for app in self.applications:
            app_names.append(app.name)
        if not text:
            completions = app_names[:]
        else:
            completions = [ f
                            for f in app_names
                            if f.startswith(text)
                            ]
        return completions

    def do_application_list(self, line):
        """List open applications"""
        for app in self.applications:
            if (app==self.current_application):
                print("*%s: %s"%(app.name,app.description))
            else:
                print("%s: %s"%(app.name,app.description))

    def do_application_new(self, name):
        """ Create new application"""
        if (name in self.available_applications):
            self.application_counter+=1
            newapp=self.available_applications[name]()
            newapp.name=newapp.name+str(self.application_counter)
            self.applications.append(newapp)
            self.current_application=newapp
            newapp.prompt = self.prompt[:-2]+'/'+newapp.name+'> '
            newapp.cmdloop()

        else:
            print("Application \"%s\" is not available"%name)            
    
    def complete_application_new(self, text, line, begidx, endidx):
        """Complete command"""
        app_names=list(self.available_applications.keys())
        if not text:
            completions = app_names[:]
        else:
            completions = [ f
                            for f in app_names
                            if f.startswith(text)
                            ]
        return completions

    def do_application_switch(self, name):
        """Set focus to an open application"""
        done=False
        for app in self.applications:
            if (app.name==name):
                #self.current_application=app    
                app.cmdloop()
                done=True
        if (not done):
            print("Application \"%s\" not found"%name)                        

    def complete_application_switch(self, text, line, begidx, endidx):
        completions = self.complete_application_delete(text, line, begidx, endidx)
        return completions

    def check_application_exist(self):
        """Check if there is any open application"""
        if (len(self.applications)==0):
            print("No open applications available")
            return False
        else:
            return True

# DATASET STUFF
    def do_dataset_delete(self, name):
        """Delete a dataset from the current application"""
        if (not self.check_application_exist()): return
        done=False
        for index, ds in enumerate(self.current_application.datasets):
            if (ds.name==name):
                if (self.current_application.current_dataset==ds):
                    if (index<len(self.current_application.datasets)-1):
                        self.current_application.current_dataset=self.current_application.datasets[index+1]
                    else:
                        self.current_application.current_dataset=self.current_application.datasets[0]
                self.current_application.datasets.remove(ds)
                done=True
        if (not done):
            print("Data Set \"%s\" not found"%name)            

    def complete_dataset_delete(self, text, line, begidx, endidx):
        """Complete delete dataset command"""
        if (not self.check_application_exist()): return [""]
        dataset_names=[]
        for ds in self.current_application.datasets:
            dataset_names.append(ds.name)
        if not text:
            completions = dataset_names[:]
        else:
            completions = [ f
                            for f in dataset_names
                            if f.startswith(text)
                            ]
        return completions

    def do_dataset_list(self, line):
        """List the datasets of the current application"""
        if (not self.check_application_exist()): return
        for ds in self.current_application.datasets:
            if (ds==self.current_application.current_dataset):
                print("*%s:\t%s"%(ds.name, ds.description))
                if (self.check_files_exist()): 
                    keylist=list(ds.current_file.file_parameters.keys())
                    print("File\t",'\t'.join(keylist))
                for i, f in enumerate(ds.files):
                    vallist=[]
                    for k in keylist:
                        vallist.append(f.file_parameters[k])
                    if (f==ds.current_file):
                        print("*%s\t%s"%(f.file_name_short,'\t'.join(vallist)))
                    else:
                        print(" %s\t%s"%(f.file_name_short,'\t'.join(vallist)))
                for i, t in enumerate(ds.theories):
                    if (t==ds.current_theory):
                        print("  *%s: %s\t %s"%(t.name, t.thname, t.description))
                    else:
                        print("   %s: %s\t %s"%(t.name, t.thname, t.description))

            else:
                print("%s:\t%s"%(ds.name, ds.description))

    def do_dataset_new(self, line):
        """If there is an active application, create a new empty dataset in it.
        Arguments: [NAME [, Description]]
                NAME: of the new dataset (optional)
                DESCRIPTION: of the dataset (optional)"""
        if (not self.check_application_exist()): return
        if (line==""):
            num_ds=self.current_application.num_datasets+1
            self.current_application.new_dataset("DataSet%02d"%num_ds, "")
        else:
            items=line.split(',')
            if (len(items)>1):
                self.current_application.new_dataset(items[0],items[1])
            else:
                self.current_application.new_dataset(items[0],"")
            
    def do_dataset_plot(self, line):
        """Plot the current dataset using the current view"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        self.current_application.plot_current_dataset()

    def do_dataset_sort(self, line):
        """Sort the files in the current dataset as a function of some file parameter"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        self.current_application.current_dataset.sort(line)

    def do_dataset_sortreverse(self, line):
        """Sort the files in the current dataset as a function of some file parameter, in reverse order"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        self.current_application.current_dataset.sort(line, True)

    def complete_dataset_sortreverse(self, text, line, begidx, endidx):
        """Complete with the list of file parameters of the current file in the current dataset"""
        completions = complete_dataset_sort(text, line, begidx, endidx)
        return completions

    def complete_dataset_sort(self, text, line, begidx, endidx):
        """Complete with the list of file parameters of the current file in the current dataset"""
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        if (not self.check_files_exist()): return [""]
        fp_names=list(self.current_application.current_dataset.current_file.file_parameters.keys())
        if not text:
            completions = fp_names[:]
        else:
            completions = [ f
                            for f in fp_names
                            if f.startswith(text)
                            ]
        return completions
        
    def do_dataset_switch(self, name):
        """ Switch the current dataset"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        for ds in self.current_application.datasets:
            if (ds.name==name):
                self.current_application.current_dataset=ds    
                done=True
        if (not done):
            print("Dataset \"%s\" not found"%line)                        

    def complete_dataset_switch(self, text, line, begidx, endidx):
        """ Complete the switch dataset command"""
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        ds_names=[]
        for ds in self.current_application.datasets:
            ds_names.append(ds.name)
        if not text:
            completions = ds_names[:]
        else:
            completions = [ f
                            for f in ds_names
                            if f.startswith(text)
                            ]
        return completions

    def check_datasets_exist(self):
        """Check if there is any open dataset"""
        if (len(self.current_application.datasets)==0):
            print("No open datasets available")
            return False
        else:
            return True

# FILE STUFF
    def check_files_exist(self):
        """Check if there are any files in the current dataset"""
        if (len(self.current_application.current_dataset.files)==0):
            print("No files available in the current dataset")
            return False
        else:
            return True


    def do_file_delete(self, line):
        """Delete file from the current data set"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        done=False
        for index, f in enumerate(self.current_application.current_dataset.files):
            if (f.file_name_short==line):
                if (self.current_application.current_dataset.current_file==f):
                    if (index<len(self.current_application.current_dataset.files)-1):
                        self.current_application.current_dataset.current_file=self.current_application.current_dataset.files[index+1]
                    else:
                        self.current_application.current_dataset.current_file=self.current_application.current_dataset.files[0]
                self.current_application.current_dataset.files.remove(f)
                done=True
        if (not done):
            print("File \"%s\" not found"%line)

    def complete_file_delete(self, text, line, begidx, endidx):
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        if (not self.check_files_exist()): return [""]
        f_names=[]
        for fl in self.current_application.current_dataset.files:
            f_names.append(fl.file_name_short)
        if not text:
            completions = f_names[:]
        else:
            completions = [ f
                            for f in f_names
                            if f.startswith(text)
                            ]
        return completions
    
    def do_file_list(self, line):
        """List the files in the current dataset"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        ds=self.current_application.current_dataset
        for f in ds.files:
            if (f==ds.current_file):
                print("*%s"%f.file_name_short)
            else:
                print("%s"%f.file_name_short)

    def do_file_new(self, line):
        """Add an empty file of the given type to the current Data Set
        Arguments: TYPE [, NAME]
                TYPE: extension of file
                NAME: Name (optional)
        TODO: if no app and no data set are open, create the right ones!
        """
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (line==""): 
            print("Missing file type")
            return
        ftypes=list(self.current_application.filetypes.values())
        items=line.split(',')
        if (items[0] in self.current_application.filetypes):  
            if (len(items)>1):
                self.current_application.current_dataset.new_file(self.current_application.filetypes[items[0]],self.current_application.ax,items[1])
            else:
                self.current_application.current_dataset.new_file(self.current_application.filetypes[line],self.current_application.ax)
            leg=self.current_application.ax.legend([], [], loc='upper left', frameon=True, ncol=2, title='Hello')
            if leg:
                leg.draggable()
            self.current_application.figure.canvas.draw()
        else:
            print("File type \"%s\" does not exists"%line)
    
    def complete_file_new(self, text, line, begidx, endidx):
        """Complete new file command"""
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        file_types=list(self.current_application.filetypes.keys())
        if not text:
            completions = file_types[:]
        else:
            completions = [ f
                            for f in file_types
                            if f.startswith(text)
                            ]
        return completions

    def do_file_open(self, line):
        """Open file(s) from the current folder
           Arguments: FILENAMES (pattern expansion characters -- *, ? -- allowed
           TODO: ALLOW OPENING FILES INSIDE SUBFOLDERS
        """
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        f_names = glob.glob(line)
        if (line=="" or len(f_names)==0): 
            print("No valid file names provided")
            return        
        f_ext = [os.path.splitext(x)[1].split('.')[-1] for x in f_names]
        if (f_ext.count(f_ext[0])!=len(f_ext)):
            print ("File extensions of files must be equal!")
            print (f_names)
            return
        if (f_ext[0] in self.current_application.filetypes):  
            for f in f_names:
                df = self.current_application.filetypes[f_ext[0]].read_file(f, self.current_application.ax)
                self.current_application.current_dataset.files.append(df)
                self.current_application.current_dataset.current_file=df
        else:
            print("File type \"%s\" does not exists"%f_ext[0])

    def complete_file_open(self, text, line, begidx, endidx):
        """Complete the file_open command
           TODO: ALLOW COMPLETING FILES INSIDE SUBFOLDERS
           TODO: IF NO DATASET, CREATE EMPTY ONE
           TODO: IF NO APPLICATION, SEARCH AND OPEN AVAILABLE ONE THAT MATCHES FILE EXTENSION
        """
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        f_names=[]
        for f in list(self.current_application.filetypes.keys()):
            f_names += glob.glob('*.%s'%f)
        if not text:
            completions = f_names[:]
        else:
            completions = [ f
                            for f in f_names
                            if f.startswith(text)
                            ]
        return completions

    def do_file_switch(self, line):
        """Change active file in the current dataset"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        for f in self.current_application.current_dataset.files:
            if (f.file_name_short==line):
                self.current_application.current_dataset.current_file=f    
                done=True
        if (not done):
            print("File \"%s\" not found"%line)                        

    def complete_file_switch(self, text, line, begidx, endidx):
        """Select names among the files in the current dataset"""
        completions=self.complete_file_delete(text, line, begidx, endidx)
        return completions

    def do_file_print(self, line):
        """Show the contents of the current file on the screen"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        file = self.current_application.current_dataset.current_file
        print(file)
        print("Path: %s"%file.file_full_path)
        print(file.file_parameters)
        print(file.header_lines)
        print(file.data_table.data)

    def do_file_plot(self, line):
        """Plot the current file using the current view"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        if (not self.check_files_exist()): return 
        file = self.current_application.current_dataset.current_file
        view = self.current_application.current_view
        fig=plt.figure()
        self.current_application.figure.set_visible(True)
        series=[]
        for i in range(view.n):
            s = plt.plot()
            series.append(s)
        x=np.zeros((file.data_table.num_rows,1))
        y=np.zeros((file.data_table.num_rows,view.n))
        for i in range(file.data_table.num_rows):
            vec=file.data_table.data[i,:]
            x[i], y[i], success = view.view_proc(vec, file.file_parameters)
        for i in range(view.n):
            plt.plot(x, y[:,i])
        ax = fig.add_subplot(111)
        if (view.log_x): ax.set_xscale("log")
        if (view.log_y): ax.set_yscale("log")
        ax.set_xlabel(view.x_label)
        ax.set_ylabel(view.y_label)
        fig.show()

# FILE TYPE STUFF
    def do_filetype_available(self, line):
        """List available file types in the current application"""
        if (not self.check_application_exist()): return
        ftypes=list(self.current_application.filetypes.values())
        for ftype in ftypes:
            print("%s:\t%s\t*.%s"%(ftype.name,ftype.description,ftype.extension))

# LEGEND STUFF
    def do_legend_switch(self, line):
        self.current_application.legend_visible = not self.current_application.legend_visible 
        self.current_application.set_legend_properties()
        self.current_application.figure.canvas.draw()

# THEORY STUFF
    def do_theory_available(self, line):
        """List available theories in the current application"""
        if (not self.check_application_exist()): return
        for t in list(self.current_application.theories.values()):
            print("%s:\t%s"%(t.thname,t.description))
 
    def do_theory_delete(self, name):
        """Delete a theory from the current dataset"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        done=False
        for index, th in enumerate(self.current_application.current_dataset.theories):
            if (th.name==name):
                if (self.current_application.current_dataset.current_theory==th):
                    if (index<len(self.current_application.current_dataset.theories)-1):
                        self.current_application.current_dataset.current_theory=self.current_application.current_dataset.theories[index+1]
                    else:
                        self.current_application.current_dataset.current_theory=self.current_application.current_dataset.theories[0]
                self.current_application.current_dataset.theories.remove(th)
                done=True
        if (not done):
            print("Theory \"%s\" not found"%name)            

    def complete_theory_delete(self, text, line, begidx, endidx):
        """Complete delete theory command"""
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        th_names=[]
        for th in self.current_application.current_dataset.theories:
            th_names.append(th.name)
        if not text:
            completions = th_names[:]
        else:
            completions = [ f
                            for f in th_names
                            if f.startswith(text)
                            ]
        return completions

    def do_theory_list(self, line):
        """List open theories in current dataset"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        for t in self.current_application.current_dataset.theories:
            if (t==self.current_application.current_dataset.current_theory):
                print("  *%s: %s\t %s"%(t.name, t.thname, t.description))
            else:
                print("   %s: %s\t %s"%(t.name, t.thname, t.description))

    def do_theory_new(self, line):
        """Add a new theory of the type specified to the current Data Set"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        thtypes=list(self.current_application.theories.keys())
        if (line in thtypes):
            num_th=self.current_application.current_dataset.num_theories+1
            self.current_application.current_dataset.new_theory(self.current_application.theories[line]("Theory%02d"%num_th))
        else:
            print("Theory \"%s\" does not exists"%line)
    
    def complete_theory_new(self, text, line, begidx, endidx):
        """Complete new theory command"""
        if (not self.check_application_exist()): return [""]
        if (not self.check_datasets_exist()): return [""]
        
        theory_names=list(self.current_application.theories.keys())
        if not text:
            completions = theory_names[:]
        else:
            completions = [ f
                            for f in theory_names
                            if f.startswith(text)
                            ]
        return completions

    def do_theory_switch(self, line):
        """Change the active theory"""
        if (not self.check_application_exist()): return
        if (not self.check_datasets_exist()): return
        for th in self.current_application.current_dataset.theories:
            if (th.name==line):
                self.current_application.current_dataset.current_theory=th
                done=True
        if (not done):
            print("Theory \"%s\" not found"%line)                        
        
    def complete_theory_switch(self, text, line, begidx, endidx):
        """Complete the theory switch command"""
        completions = self.complete_theory_delete(text, line, begidx, endidx)
        return completions

# VIEW STUFF
    def do_view_available(self, line):
        """List available views in the current application"""
        if (not self.check_application_exist()): return
        for view in self.current_application.views:
            if (view==self.current_application.current_view):
                print("*%s:\t%s"%(view.name,view.description))
            else:
                print("%s:\t%s"%(view.name,view.description))

    def do_view_switch(self, name):
        """Change to another view from open application"""
        done=False
        if (not self.check_application_exist()): return
        for view in self.current_application.views:
            if (view.name==name):
                self.current_application.current_view=view
                done=True
        if (not done):
            print("View \"%s\" not found"%name)                        

    def complete_view_switch(self, text, line, begidx, endidx):
        """Complete switch view command"""
        if (not self.check_application_exist()): return [""]
        view_names=[]
        for view in self.current_application.views:
            view_names.append(view.name)
        if not text:
            completions = view_names[:]
        else:
            completions = [ f
                            for f in view_names
                            if f.startswith(text)
                            ]
        return completions
    
# OTHER STUFF
    def do_shell(self, line):
        """Run a shell command"""
        print("running shell command:", line)
        output = os.popen(line).read()
        print(output)
        self.last_output = output

    def do_cd(self, line):
        """Change folder"""
        if os.path.isdir(line):
            os.chdir(line)
        else:
            print("Folder %s does not exist"%line)

    def complete_cd(self, text, line, begidx, endidx):
        """Complete cd command
           TODO: COMPLETE SUBFOLDERS TOO"""
        test_directory=''
        dirs=[]
        for child in os.listdir():
            test_path = os.path.join(test_directory, child)
            if os.path.isdir(test_path): 
                dirs.append(test_path)
        if not text:
            completions = dirs[:]
        else:
            completions = [ f
                            for f in dirs
                            if f.startswith(text)
                            ]
        return completions

    def do_ls(self, line):
        """List contents of current folder
           TODO: CONSIDER SUBFOLDERS TOO
        """
        dirs=os.listdir()
        for d in dirs:
            print("%s"%d)

    def do_dir(self, line):
        """List contents of current folder"""
        self.do_ls(line)

    def do_info(self, line):
        """Show info about the current RepTate session"""
        print("##AVAILABLE APPLICATIONS:")
        self.do_application_available(line)

        print("\n##OPEN APPLICATIONS (*=current):")
        self.do_application_list(line)

        print("\n##CURRENT APPLICATION:")
        print("-->FILE TYPES AVAILABLE:")
        self.do_filetype_available(line)

        print("-->VIEWS AVAILABLE (*=current):")
        self.do_view_available(line)

        print("-->THEORIES AVAILABLE:")
        self.do_theory_available(line)

        print("\n##DATA SETS IN CURRENT APPLICATION:")
        self.do_dataset_list(line)

    def emptyline(self):
        pass

    def do_quit(self, args):
        """Exit RepTate"""
        print("\n")
        readline.write_history_file()
        return True
    do_EOF = do_quit