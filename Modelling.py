"""
The Module contains neccessary functions for analysing
a 3D RC Frame model described in Fernando Gutiérrez Urzúa
 YouTube channel (https://www.youtube.com/user/lfgurzua).
In his videos, the default TCL language was used. This is
a python implementation of the same model.
"""
# Author: Nolaraj Poudel, January 2022


import openseespy.opensees as ops
import numpy as np
import os
import time
import pandas as pd
from Excel_Extraction import *
import openseespy.postprocessing.Get_Rendering as opp
# import vfo.vfo as vfo
from Basic_Info import *



def build_RC_rect_section(sec_tag, H, B, cover_H, cover_B, core_tag,
                          cover_tag, steel_tag, n_bars_top, bar_area_top,
                          n_bars_bot, bar_area_bot, n_bars_int_tot,
                          bar_area_int, nf_core_y, nf_core_z, nf_cover_y, nf_cover_z):
    """
    Build fiber rectangular RC section, 1 steel layer top, 1 bottom, 1 skin, confined core
    Define a procedure which generates a rectangular reinforced concrete section
    with one layer of steel at the top & bottom, skin reinforcement and a
    confined core.
     TCL version by: Silvia Mazzoni, 2006
                     adapted from Michael H. Scott, 2003
     Python version by: Amir Hossein Namadchi, 2022
    Keyword arguments:
    sec_tag -- tag for the section that is generated by this function
    H -- depth of section, along local-y axis
    B -- width of section, along local-z axis
    cover_H -- concrete cover over in local-y axis
    cover_B -- concrete cover over in local-z axis
    core_tag -- material tag for the core patch
    cover_tag -- material tag for the cover patches
    steel_tag -- material tag for the reinforcing steel
    n_bars_top -- number of reinforcing bars in the top layer
    bar_area_top -- cross-sectional area of each reinforcing bar in top layer
    n_bars_bot -- number of reinforcing bars in the bottom layer
    bar_area_bot -- cross-sectional area of each reinforcing bar in bottom layer
    n_bars_int_tot -- TOTAL number of reinforcing bars on the intermediate layers,
                    symmetric about z axis and 2 bars per layer, needs to be an even integer
    bar_area_int -- cross-sectional area of each reinforcing bar in intermediate layer
    nf_core_y -- number of fibers in the core patch in the y direction
    nf_core_z -- number of fibers in the core patch in the z direction
    nf_cover_y -- number of fibers in the cover patches with long sides in the y direction
    nf_cover_z - number of fibers in the cover patches with long sides in the z direction
    """
    # The distance from the section z-axis to the edge of the cover concrete
    # -- outer edge of cover concrete
    cover_y = 0.5 * H
    # The distance from the section y-axis to the edge of the cover concrete
    # -- outer edge of cover concrete
    cover_z = 0.5 * B
    # The distance from the section z-axis to the edge of the core concrete
    # --  edge of the core concrete/inner edge of cover concrete
    core_y = cover_y - cover_H
    # The distance from the section y-axis to the edge of the core concrete
    # --  edge of the core concrete/inner edge of cover concrete
    core_z = cover_z - cover_B
    # number of intermediate bars per side
    n_bars_int = int(n_bars_int_tot / 2)

    # constructs a FiberSection
    ops.section('Fiber', sec_tag, '-GJ', 1.0e9)

    # Generate a quadrilateral shaped patch (core patch)
    ops.patch('quad', core_tag,
              nf_core_z, nf_core_y,
              *[-core_y, core_z],
              *[-core_y, -core_z],
              *[core_y, -core_z],
              *[core_y, core_z])

    # Define the four cover patches
    ops.patch('quad', cover_tag,
              2, nf_cover_y,
              *[-cover_y, cover_z],
              *[-core_y, core_z],
              *[core_y, core_z],
              *[cover_y, cover_z])
    ops.patch('quad', cover_tag,
              2, nf_cover_y,
              *[-core_y, -core_z],
              *[-cover_y, -cover_z],
              *[cover_y, -cover_z],
              *[core_y, -core_z])
    ops.patch('quad', cover_tag,
              nf_cover_z, 2,
              *[-cover_y, cover_z],
              *[-cover_y, -cover_z],
              *[-core_y, -core_z],
              *[-core_y, core_z])
    ops.patch('quad', cover_tag,
              nf_cover_z, 2,
              *[core_y, core_z],
              *[core_y, -core_z],
              *[cover_y, -cover_z],
              *[cover_y, cover_z])

    # construct a straight line of fibers
    ## intermediate skin reinf. +z
    ops.layer('straight', steel_tag, n_bars_int, bar_area_int,
              *[-core_y, core_z], *[core_y, core_z])
    ## intermediate skin reinf. -z
    ops.layer('straight', steel_tag, n_bars_int, bar_area_int,
              *[-core_y, -core_z], *[core_y, -core_z])
    ## top layer reinfocement
    ops.layer('straight', steel_tag, n_bars_top, bar_area_top,
              *[core_y, core_z], *[core_y, -core_z])
    ## bottom layer reinforcement
    ops.layer('straight', steel_tag, n_bars_bot, bar_area_bot,
              *[-core_y, core_z], *[-core_y, -core_z])

def Section_Manager():
        Beams_Numbers =   int(ws_SB.cell(column=6, row=BD_row - 1).value)
        Columns_Numbers = int(ws_SB.cell(column=6, row=CD_row - 1).value)

        Tag_Check = []
        def Section_Builder(Materials_Data, ConcreteUnCon_Data, ConcreteCon_Data, Steel_Data, Sectional_Data):


            # Uniaxial Kent-Scott-Park concrete material with degraded linear unloading/reloading
            mat_KSP_unconf = {'ID': ConcreteUnCon_Data[0],
                              'matTag': int(ConcreteUnCon_Data[1]),
                              'fpc': ConcreteUnCon_Data[2],
                              'epsc0': ConcreteUnCon_Data[3],
                              'fpcu': ConcreteUnCon_Data[4],
                              'epsU': ConcreteUnCon_Data[5],
                              'lamda': ConcreteUnCon_Data[6],
                              'ft': ConcreteUnCon_Data[7],
                              'Ets': ConcreteUnCon_Data[8]}
            # Uniaxial Kent-Scott-Park concrete material with degraded linear unloading/reloading
            mat_KSP_conf = {'ID': ConcreteCon_Data[0],
                            'matTag': int(ConcreteCon_Data[1]),
                            'fpc': ConcreteCon_Data[2],
                            'epsc0': ConcreteCon_Data[3],
                            'fpcu': ConcreteCon_Data[4],
                            'epsU': ConcreteCon_Data[5],
                            'lamda': ConcreteCon_Data[6],
                            'ft': ConcreteCon_Data[7],
                            'Ets': ConcreteCon_Data[8]}
            # Uniaxial Giuffre-Menegotto-Pinto steel with isotropic strain hardening
            mat_GMP = {'ID': Steel_Data[0],
                       'matTag': int(Steel_Data[1]),
                       'Fy': Steel_Data[2],
                       'E0': Steel_Data[3],
                       'b': Steel_Data[4],
                       'R0': Steel_Data[5],
                       'cR1': Steel_Data[6],
                       'cR2': Steel_Data[7]}

            def try_except(value):
                Tag = value["matTag"]
                if Tag not in Tag_Check:
                    ops.uniaxialMaterial(*value.values())
                    Tag_Check.append(Tag)



            # Materials
            try_except(mat_KSP_unconf)
            try_except(mat_KSP_conf)
            try_except(mat_GMP)


            # Adding Sections
            build_RC_rect_section(Sectional_Data[0],
                                  Sectional_Data[1],
                                  Sectional_Data[2],
                                  Sectional_Data[3],
                                  Sectional_Data[4],
                                  Sectional_Data[5],
                                  Sectional_Data[6],
                                  Sectional_Data[7],
                                  Sectional_Data[8],
                                  Sectional_Data[9],
                                  Sectional_Data[10],
                                  Sectional_Data[11],
                                  Sectional_Data[12],
                                  Sectional_Data[13],
                                  *[Sectional_Data[14],
                                  Sectional_Data[15],
                                  Sectional_Data[16],
                                  Sectional_Data[17]]
                                  )




        for i in range(1, Beams_Numbers + 1):
            Type = "Type" + str(i)
            Materials_Data, ConcreteUnCon_Data, ConcreteCon_Data, Steel_Data, Sectional_Data = Sectional_Info(
                "Beam", Type)
            Section_Builder(Materials_Data, ConcreteUnCon_Data, ConcreteCon_Data, Steel_Data, Sectional_Data)

            #Info Writer
            ModalInfo_Writer(f" ____________________Beam {Type} ____________________")
            ModalInfo_Writer("Materials_Data", Data=Materials_Data)
            ModalInfo_Writer("ConcreteUnCon_Data", Data=ConcreteUnCon_Data)
            ModalInfo_Writer("ConcreteCon_Data", Data=ConcreteCon_Data)
            ModalInfo_Writer("Steel_Data", Data=Steel_Data)
            ModalInfo_Writer("Sectional_Data", Data=Sectional_Data)





        for i in range(1,Columns_Numbers + 1):
            Type = "Type" + str(i)
            Materials_Data, ConcreteUnCon_Data, ConcreteCon_Data, Steel_Data, Sectional_Data = Sectional_Info(
                "Column", Type)
            Section_Builder(Materials_Data, ConcreteUnCon_Data, ConcreteCon_Data, Steel_Data, Sectional_Data)
            #Info Writer
            ModalInfo_Writer(f" ____________________Column {Type} ____________________")
            ModalInfo_Writer("Materials_Data", Data=Materials_Data)
            ModalInfo_Writer("ConcreteUnCon_Data", Data=ConcreteUnCon_Data)
            ModalInfo_Writer("ConcreteCon_Data", Data=ConcreteCon_Data)
            ModalInfo_Writer("Steel_Data", Data=Steel_Data)
            ModalInfo_Writer("Sectional_Data", Data=Sectional_Data)

def NodeElement_Segregator(Nodes_Name, XSpacing, YSpacing, ZSpacing):
    # Nodes Segregation
    Node_Data = {}

    # Floor Segregation
    Node_Data["Base"] = []
    Node_Data["Top"] = []
    Node_Data["Floors"] = []


    for floor in range(len(ZSpacing)):
        Node_Data["Floor " + str(floor + 1)] = []

    for i in range(len(Nodes_Name)):
        Node_Name = Nodes_Name[i]

        Floor_Value = int(str(Node_Name)[0])
        if Floor_Value == 1:
            Floor_Name = "Base"
            Node_Data[Floor_Name].append(Node_Name)

        else:
            Floor_Name = "Floor " + str(Floor_Value - 1)
            Node_Data[Floor_Name].append(Node_Name)
            Node_Data["Floors"].append(Node_Name)

        if Floor_Value == len(ZSpacing) + 1:
            Floor_Name = "Top"
            Node_Data[Floor_Name].append(Node_Name)

    # Outer and Inner Nodes
    Node_Data["Outer"] = []
    for i in range(len(Nodes_Name)):
        Node_Name = Nodes_Name[i]

        X_Index = int(str(Node_Name)[1])
        Y_Index = int(str(Node_Name)[2])

        if (X_Index == 1 or X_Index == len(XSpacing) + 1) or (Y_Index == 1 or Y_Index == len(XSpacing) + 1):
            Node_Data["Outer"].append(Node_Name)

    Node_Data["Inner"] = List_Subtractor(Nodes_Name, Node_Data["Outer"])


    # Grid Along X and Y Nodes
    X_Grids = []
    Y_Grids = []

    for X in range(1, len(XSpacing) + 2):
        Name = "X" + str(X)
        Node_Data[Name] = []
        X_Grids.append(Name)
    for i in range(len(Nodes_Name)):
        Node_Name = Nodes_Name[i]
        X_Value = int(str(Node_Name)[1])
        Grid = "X" + str(X_Value)
        Node_Data[Grid].append(Node_Name)
    for Y in range(1, len(YSpacing) + 2):
        Name = "Y" + str(Y)
        Node_Data[Name] = []
        Y_Grids.append(Name)
    for i in range(len(Nodes_Name)):
        Node_Name = Nodes_Name[i]
        Y_Value = int(str(Node_Name)[2])
        Grid = "Y" + str(Y_Value)
        Node_Data[Grid].append(Node_Name)

    Model_Data["Node"]["All"] = Nodes_Name

    for key, value in Node_Data.items():
        Model_Data["Node"][key] = value


    def Element_Connectivity():
        Beams_XGrids = []
        Beams_YGrids = []
        Column_Grids = []
        Grids = {}


        for floor in range(1, len(ZSpacing) + 1):
            Floor_Name = "Floor " + str(floor)
            for key, value in Node_Data.items():
                if key in X_Grids:
                    Z_Index = floor
                    X_Index = key[1]

                    Grid_Name = str(Z_Index) + "X" + str(X_Index)
                    Required_Nodes = List_Intersection(Node_Data[key], Node_Data[Floor_Name])

                    Beams_XGrids.append(Grid_Name)
                    Grids[Grid_Name] = Required_Nodes

                if key in Y_Grids:
                    Z_Index = floor
                    Y_Index = key[1]

                    Grid_Name = str(Z_Index) + "Y" + str(Y_Index)
                    Required_Nodes = List_Intersection(Node_Data[key], Node_Data[Floor_Name])

                    Beams_YGrids.append(Grid_Name)
                    Grids[Grid_Name] = Required_Nodes
        for x in range(1, len(XSpacing) + 2):
            for y in range(1, len(YSpacing) + 2):
                X_Index = x
                Y_Index = y
                Grid_Name = str(X_Index) + "Z" + str(Y_Index)

                Grids[Grid_Name] = []
                Column_Grids.append(Grid_Name)
        for Name in Nodes_Name:
            for x in range(1, len(XSpacing) + 2):
                for y in range(1, len(YSpacing) + 2):
                    X_Index = x
                    Y_Index = y
                    Grid_Name = str(X_Index) + "Z" + str(Y_Index)

                    X_Value = int(str(Name)[1])
                    Y_Value = int(str(Name)[2])

                    if X_Value == X_Index and Y_Value == Y_Index:
                        Grids[Grid_Name].append(Name)

        Grid_Data = [Grids, Beams_XGrids, Beams_YGrids, Column_Grids]

        Model_Data["BC_Element"] = {"All":[], "XBeams":[], "YBeams":[], "Columns":[], "Grids":{}, "Connectivity":{} }
        for key, value in Grids.items():
            Model_Data["BC_Element"]["Grids"][key] = value



        # Beam ID Naming
        X_BeamNames = []
        Y_BeamNames = []
        Z_ColNames = []
        Name_Connectivity = {}
        for grids in Beams_XGrids:
            Nodes_List = Grids[grids]
            for i in range(len(Nodes_List) - 1):
                First_Node_Name = int(Nodes_List[i])
                End_Node_Name = int(Nodes_List[i + 1])
                Name = int(str(First_Node_Name) + str(End_Node_Name))
                Connectivity = [First_Node_Name, End_Node_Name]

                Name_Connectivity[Name] = Connectivity
                Y_BeamNames.append(Name)



        for grids in Beams_YGrids:
            Nodes_List = Grids[grids]
            for i in range(len(Nodes_List) - 1):
                First_Node_Name = int(Nodes_List[i])
                End_Node_Name = int(Nodes_List[i + 1])
                Name = int(str(First_Node_Name) + str(End_Node_Name))
                Connectivity = [First_Node_Name, End_Node_Name]

                Name_Connectivity[Name] = Connectivity
                X_BeamNames.append(Name)


        for grids in Column_Grids:
            Nodes_List = Grids[grids]
            for i in range(len(Nodes_List) - 1):
                First_Node_Name = int(Nodes_List[i])
                End_Node_Name = int(Nodes_List[i + 1])
                Name = int(str(First_Node_Name) + str(End_Node_Name))
                Connectivity = [First_Node_Name, End_Node_Name]

                Name_Connectivity[Name] = Connectivity
                Z_ColNames.append(Name)



        Model_Data["BC_Element"]["All"] = Z_ColNames + Y_BeamNames + X_BeamNames
        Model_Data["BC_Element"]["XBeams"] = X_BeamNames
        Model_Data["BC_Element"]["YBeams"] = Y_BeamNames
        Model_Data["BC_Element"]["Columns"] = Z_ColNames


        Connectivity_Data = [Name_Connectivity, X_BeamNames, Y_BeamNames, Z_ColNames]


        for key, value in Name_Connectivity.items():
            Model_Data["BC_Element"]["Connectivity"][key] = value


        return Grid_Data, Connectivity_Data

    Grid_Data, Connectivity_Data = Element_Connectivity()
    return Node_Data, Grid_Data, Connectivity_Data

def Initial_Loads(XMass, YMass, ZMass, ZSpacing, Conc_Load = 0):

    #timeSeries('Linear', tag, '-factor', factor=1.0, '-tStart', tStart=0.0)
    ops.timeSeries('Linear', 1, '-factor', 1.0)
    ops.pattern('Plain', 1, 1)



    Floor_Nodes = Model_Data["Node"]["Floors"]
    for n in Floor_Nodes:
        ops.load(n, *[0, 0, -Conc_Load, 0, 0, 0])

    for n in range(0, len(ZSpacing) + 1):
        Floor_No = "Floor " + str(n)
        if n == 0:
            Floor_No = "Base"

        NodalMass_X = XMass[n]
        NodalMass_Y = YMass[n]
        NodalMass_Z = ZMass[n]


        Floor_Nodes = Model_Data["Node"][Floor_No]
        for o in Floor_Nodes:
            ops.mass(o, *[NodalMass_X,NodalMass_Y, NodalMass_Z, 0, 0, 0])









def Modelling_Handle():
    #Modelling Data
    #Segregator Only Can be called once throughout the Analysis
    ModalInfo_Writer(Nth_writer=0)
    Nodes_Name, Node_NameCoOrd, XSpacing, YSpacing, ZSpacing, XMass, YMass, ZMass = Model_Info()
    Node_Data, Grid_Data, Connectivity_Data = NodeElement_Segregator(Nodes_Name, XSpacing, YSpacing, ZSpacing)
    Name_Connectivity, X_BeamNames, Y_BeamNames, Z_ColNames, n_integration_pts = \
        Connectivity_Data[0], Connectivity_Data[1], Connectivity_Data[2], Connectivity_Data[3], 4


    #Initialization
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 6)


    #Nodal Definitions, Restraining and Section Definitions
    [ops.node(key, *value) for key, value in Node_NameCoOrd.items()]
    [ops.fix(n, 1, 1, 1, 1, 1, 1)  for n in Node_Data["Base"]]
    Section_Manager()



    #Adding Elements and Fixing of the Elements Transformations
    trans_tags = {"P_delta": 1,
                  "linear_beam_X": 2,
                  "linear_beam_Y": 3}
    ops.geomTransf('PDelta', trans_tags['P_delta'], *[-1.0, 0.0, 0.0])
    ops.geomTransf('Linear', trans_tags['linear_beam_X'], *[0.0, 1.0, 0.0])
    ops.geomTransf('Linear', trans_tags['linear_beam_Y'], *[1.0, 0.0, 0.0])

    [ops.element('nonlinearBeamColumn', name, *Name_Connectivity[name], n_integration_pts, 21, trans_tags['P_delta'])
     for name in Z_ColNames]
    [ops.element('nonlinearBeamColumn', name, *Name_Connectivity[name], n_integration_pts, 11, trans_tags['linear_beam_X'])
     for name in X_BeamNames]
    [ops.element('nonlinearBeamColumn', name, *Name_Connectivity[name], n_integration_pts, 11, trans_tags['linear_beam_Y'])
     for name in Y_BeamNames]


    #Application of Gravity Loads to the Model - Skipping this creates error in generating ops.eigen in Modal Analysis
    Initial_Loads(XMass, YMass, ZMass, ZSpacing,  Conc_Load = Conc_Load)



