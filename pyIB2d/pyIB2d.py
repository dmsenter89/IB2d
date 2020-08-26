#!/usr/bin/python
# -*- coding: utf-8 -*-
'''-------------------------------------------------------------------------

 IB2d is an Immersed Boundary Code (IB) for solving fully coupled non-linear
 	fluid-structure interaction models. This version of the code is based off of
	Peskin's Immersed Boundary Method Paper in Acta Numerica, 2002.

 Frontend Usage:
    The user can specify the path to the simulation folder and its input2d file
    in one of two ways: either using only the terminal, in which case one types
    `$python pyIB2d.py -p PATH/TO/input2d`
    `$python pyIB2d --path PATH/TO/input2d`
    or by selecting the input2d file from a file-select dialog by typing
    `$python pyIB2d -d`
    `$python pyIB2d --fd`
    In either case the input2d file must reside in the same folder as the various
    geometry files (.vertex, .beam, etc.).

Note: to retain backwards compatibility, the files writing the simulation results
have not been edited. Therefore, the `viz_IB2d` and `hier_IB2d_data` folders
will be generated in the same folder as the frontend script.

 Author: Nicholas A. Battista
 Email:  nick.battista@unc.edu
 Date Created: May 27th, 2015
 Current Version: October 26th, 2016
 Python 3.5 port by: Christopher Strickland
 Python Frontend Script: Michael Senter
 Institution: UNC-CH

 This code is capable of creating Lagrangian Structures using:
 	1. Springs
 	2. Beams (*torsional springs)
 	3. Target Points
	4. Muscle-Model (combined Force-Length-Velocity model, "HIll+(Length-Tension)")

 One is able to update those Lagrangian Structure parameters, e.g.,
 spring constants, resting lengths, etc

 There are a number of built in Examples, mostly used for teaching purposes.

 If you would like us to add a specific muscle model,
 please let Nick (nick.battista@unc.edu) know.

----------------------------------------------------------------------------'''

import os
import argparse
import numpy as np
import sys
from tkinter.filedialog import askopenfilename
# Path Reference to where Driving code is found #
sys.path.append('IBM_Blackbox')
import IBM_Driver as Driver

def give_Me_input2d_Parameters(fpath):
    ''' Function to read in input files from "input2d"

    Returns:
        params: ndarray of parameter values
        struct_name: name of structure'''

    filename = os.path.join(fpath[0], fpath[1]) #Name of file to read in

    #This is more sophisticated than what was here before the port.
    #If desired, names could be double checked for consistancy.
    names,params = np.loadtxt(filename,dtype={'names': ('param','value'),\
            'formats': ('S25','f8')},comments=('%','string_name'),\
            delimiter='=',unpack=True)

    #now get string_name
    with open(filename,'r') as f:
        for line in f:
            #look for 'string_name'. make sure it comes before a comment char
            if ('string_name' in line) and \
                line.find('string_name') < line.find('%'):
                #split the line by whitespace
                words = line.split()
                #look for the equals sign
                for n,word in enumerate(words):
                    if word == '=':
                        struct_name = os.path.join(fpath[0], words[n+1])
                        break
                break

    return (params,struct_name)

def main2d(fpath):

    '''This is the "main" function, which ets called to run the
    Immersed Boundary Simulation. It reads in all the parameters from
    "input2d", and sends them off to the "IBM_Driver" function to actually
    perform the simulation.'''

    # READ-IN INPUT PARAMTERS #
    params,struct_name = give_Me_input2d_Parameters(fpath)

    # FLUID PARAMETER VALUES STORED #
    mu = params[0]      # Dynamic Viscosity
    rho = params[1]     # Density

    # TEMPORAL INFORMATION VALUES STORED #
    T_final = params[2] # Final simulation time
    dt = params[3]      # Time-step

    # GRID INFO STORED #
    grid_Info = {}
    grid_Info['Nx'] = int(params[4])      # num of Eulerian Pts in x-Direction
    grid_Info['Ny'] = int(params[5])      # num of Eulerian Pts in y-Direction
    grid_Info['Lx'] = params[6]           # Length of Eulerian domain in x-Direction
    grid_Info['Ly'] = params[7]           # Length of Eulerian domain in y-Direction
    grid_Info['dx'] = params[6]/params[4] # Spatial step-size in x
    grid_Info['dy'] = params[7]/params[5] # Spatial step-size in y
    grid_Info['supp'] = params[8] # num of pts used in delta-function support
                                       #    (supp/2 in each direction)
    grid_Info['pDump'] = params[28]            # Print Dump (How often to plot)
    grid_Info['pMatplotlib'] = int(params[29]) # Plot in matplotlib? (1=YES,0=NO)
    grid_Info['lagPlot'] = int(params[30])     # Plot LAGRANGIAN PTs ONLY in matplotlib
    grid_Info['velPlot'] = int(params[31])     # Plot LAGRANGIAN PTs +
                                               #  VELOCITY FIELD in matplotlib
    grid_Info['vortPlot'] = int(params[32])    # Plot LAGRANGIAN PTs +
                                               #  VORTICITY colormap in matplotlib
    grid_Info['uMagPlot'] = int(params[33])    # Plot LAGRANGIAN PTs +
                                               #  MAGNITUDE OF VELOCITY
                                               #     colormap in matplotlib
    grid_Info['pressPlot'] = int(params[34])   # Plot LAGRANGIAN PTs +
    #                                          # PRESSURE colormap in matplotlib


    # MODEL STRUCTURE DATA STORED #
    model_Info = {}
    model_Info['springs'] = int(params[9])           # Springs: (0=no, 1=yes)
    model_Info['update_springs'] = int(params[10])   # Update_Springs: (0=no, 1=yes)
    model_Info['target_pts'] = int(params[11])       # Target_Pts: (0=no, 1=yes)
    model_Info['update_target_pts'] = int(params[12])# Update_Target_Pts: (0=no, 1=yes)
    model_Info['beams'] = int(params[13])            # Beams: (0=no, 1=yes)
    model_Info['update_beams'] = int(params[14])     # Update_Beams: (0=no, 1=yes)
    # Muscle Activation (Length/Tension-Hill Model): 0 (for no) or 1 (for yes)
    model_Info['muscles'] = int(params[15])
    # Muscle Activation 3-ELEMENT HILL MODEL w/ Length-Tension/Force-Velocity:
    #   0 (for no) or 1 (for yes)
    model_Info['hill_3_muscles'] = int(params[16])
    # Arbirtary External Force Onto Fluid Grid: 0 (for no) or 1 (for yes)
    model_Info['arb_ext_force'] = int(params[17])
    model_Info['tracers'] = int(params[18])          # Tracer Particles: (0=no, 1=yes)
    model_Info['mass']= int(params[19])              # Mass Points: (0=no, 1=yes)
    model_Info['gravity']= int(params[20])           # Gravity: (0=no, 1=yes)
    model_Info['xG']= params[21]                     # x-Component of Gravity vector
    model_Info['yG']= params[22]                     # y-Component of Gravity Vector
    model_Info['porous']= int(params[23])            # Porous Media: (0=no, 1=yes)
    model_Info['concentration']= int(params[24])     # Background Concentration Gradient:
                                                     # 0 (for no) or 1 (for yes)
    model_Info['electrophysiology'] = int(params[25])# Electrophysiology (FitzHugh-Nagumo)
    model_Info['damped_springs'] = int(params[26])   # Damped Springs (0=no, 1=yes)
    model_Info['update_D_Springs'] = int(params[27]) # Update Damped Springs


    #-#-#-# DO THE IMMERSED BOUNDARY SOLVE!!!!!!!! #-#-#-#
    #[X, Y, U, V, xLags, yLags] = Driver.main(struct_name, mu, rho, grid_Info, dt, T_final, model_Info)

    #For debugging only!
    Driver.main(struct_name, mu, rho, grid_Info, dt, T_final, model_Info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Frontend for pyIB2d.\n'
                                    'Use file-select dialog or terminal arg '
                                    'to point to simulation directory.')
    parser.add_argument('-d','--fdiag', action='store_true', help='Use file-dialog')
    parser.add_argument('-p', '--path', help='Path to input2d for sim')
    args = parser.parse_args()
    if args.path:
        inname = args.path
    elif args.fdiag:
        inname = askopenfilename()
    else:
        print('Invalid use of flags. Use the -h option for help.')
        sys.exit()
    fpath = os.path.split(inname)
    main2d(fpath)
