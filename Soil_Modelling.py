import gmsh
import numpy as np
import openseespy.opensees as ops
from Excel_Extraction import *
import gmsh2opensees as g2o
import math
from numpy import array, int32, double, concatenate, unique, setdiff1d, zeros
Equal_DOF, AbsorbantMaterials, AbsorbantElements, BaseRes = Soil_BC()
Static_Nsteps = 1


def NodeTags(Physical_Group = "Solid", model = gmsh.model, elementName = "Tetrahedron"):
    eleTags, nodeTags, eleName, eleNodes = g2o.get_elements_and_nodes_in_physical_group(Physical_Group, model, elementName)
    return nodeTags
def RemoveNodeDuplicates(NodeTags):
    Nodes = []
    for node in NodeTags:
        Nodes += node
    Nodes = np.unique(np.array(Nodes))
    return Nodes
def AnalysisOpt_Tester(numberer, constraint, algorithm):
    print("Analysis Started")

    try:

        ops.numberer(numberer)
        ops.constraints(constraint)
        ops.algorithm(algorithm)

        ops.system("FullGeneral")
        ops.integrator("LoadControl", 1/Static_Nsteps)
        ops.analysis("Static")


        viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model)
        Analysis_Visualization(viewnum)
        print(numberer, constraint, algorithm)
    except:
        pass

    print("''''''''''''''''_____________________Analysis Ended____________________________'''''''''''''''")
def Analysis_Visualization():
    if Static_Nsteps == 1:
        oa = ops.analyze(1)
        viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model)

    else:
        viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model)
        for step in range(Static_Nsteps):
            ops.analyze(1)
            viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model,
                                                          viewnum=viewnum, step=step + 1, time=ops.getTime())
        gmsh.view.option.setNumber(viewnum, "VectorType", 5)
        gmsh.view.option.setNumber(viewnum, "DisplacementFactor", 1)





def Soil_Modeling():

    # Initialization
    gmsh.initialize()
    gmsh.open("Soil.msh")
    model = gmsh.model
    ops.model('basic', '-ndm', 3, '-ndf', 6)


    # Nodes Definitions
    g2o.add_nodes_to_ops(NodeTags(elementName="Hexahedron"), model)


    # Adding Soil Material of mesh
    soilMatTag = 1
    G0 = 125
    Patm = 101325
    e0 = 0.784
    P = 3 * Patm
    G = (G0 * Patm * (2.97 - e0) ** 2) / (1 + e0) * (math.sqrt(P / Patm))
    nu = 0.3
    E = G * (2 * (1 + nu))
    rho = 2000
    ops.nDMaterial("ElasticIsotropic", soilMatTag, E, nu, rho)

    # Add Steel material model
    steelMatTag = 2
    E = 210e9  # Pa
    nu = 0.3  # -
    rho = 7300.  # kg / m³
    ops.nDMaterial('ElasticIsotropic', steelMatTag, E, nu, rho)



    #Adding 3D Solid elements
    #Soil Elements
    elementTags, nodeTags, elementName, elementNnodes = g2o.get_elements_and_nodes_in_physical_group("Soil",
                                                                                                     gmsh.model, elementName="Hexahedron")
    for eleTag, eleNodes in zip(elementTags, nodeTags):
        if eleTag == 235:
            print(eleTag, eleNodes)
        ops.element('SSPbrick', eleTag, *eleNodes, soilMatTag)



    #Steel Elements
    elementTags, nodeTags, elementName, elementNnodes = g2o.get_elements_and_nodes_in_physical_group("FootingColumn",
                                                                                                     gmsh.model, elementName="Hexahedron")
    for eleTag, eleNodes in zip(elementTags, nodeTags):
        print(eleTag, eleNodes)
        ops.element('SSPbrick', eleTag, *eleNodes, steelMatTag)

    # Equal Dof Modelling and Base Restraints Modeling
    for items in BaseRes:
        PhysicalGrp = items[0]
        Restraint = "XYZ"
        if items[1] == "Fixed": Restraint = "XYZ";
        if items[1] == "Rollar": Restraint = "Z";
        g2o.fix_nodes(NodeTags(PhysicalGrp), Restraint)
    for items in Equal_DOF:
        PhysicalGrp = items[0]  # Physical Group needs to be provided as surface type
        EqualDOFS = [x for x in range(1, items[1] + 1)]
        Node_Tags = NodeTags(PhysicalGrp)
        IdVal_Addition = 100000
        g2o.addDuplicateNode(Node_Tags, model,
                             IdVal_Addition=IdVal_Addition)  # Duplicated node value will be greater than as provided
        for nodes in Node_Tags:
            for node in nodes:
                ops.equalDOF(node, int(node) + IdVal_Addition, *EqualDOFS)

    # Absorbant Elements Modelling
    for items in AbsorbantMaterials:
        ops.uniaxialMaterial("Elastic", int(items[0]), items[2], items[4], items[6])
        ops.uniaxialMaterial("Elastic", int(items[1]), items[2], items[5], items[6])
    for items in AbsorbantElements:
        IdVal_Addition = 200000
        Dynamic_Value = IdVal_Addition
        matTagXY = int(items[0])
        matTagZ = int(items[1])
        PhysicalGrp = items[2]
        Node_Tags = NodeTags(PhysicalGrp)
        matTag = items[3]
        dirIDs = items[4]
        Materials = [matTagXY, matTagXY, matTagZ]
        Directions = [1, 2, 3]
        Nodes = RemoveNodeDuplicates(Node_Tags)
        g2o.addDuplicateNode(Nodes, model, IdVal_Addition=IdVal_Addition)
        for index, node in enumerate(Nodes):
            eleTag = Dynamic_Value + index
            NodeTag = [int(node), int(node) + IdVal_Addition]
            ops.element("zeroLength", eleTag, *NodeTag, "-mat", *Materials, "-dir", *Directions)
        Dynamic_Value += len(Nodes)

    return model





def Loading_Analysis():
    def Point_Load():
        #add a load
        ts_tag = 1
        ops.timeSeries('Constant', ts_tag)
        patternTag = 1
        ops.pattern('Plain', patternTag, ts_tag)

        loaded_node = 25
        Fx = 10             #N
        Fy = 0.                 #N
        Fz = 0                  #N
        ops.load(loaded_node, Fx, Fy, Fz, 0, 0, 0)



        ops.system("BandGen")
        ops.numberer("RCM")
        ops.constraints('Plain')
        ops.integrator("LoadControl", 1 / Static_Nsteps)
        ops.algorithm("Linear")
        ops.analysis("Static")






    Point_Load()
    Analysis_Visualization()


model = Soil_Modeling()
Loading_Analysis()
gmsh.fltk.run()
gmsh.finalize()
























# def TH_Analysis():
#     ops.initialize()
#
#     Recorder_Data, Analysis_Options, Earthquake_Info = TH_Data()
#     Eigen_Filename = Modal_Analysis()  # Eigen Value Extraction
#
#     # Info Writer
#     ModalInfo_Writer(f" ____________________TH analysis____________________")
#     ModalInfo_Writer("Recorder_Data", Data=Recorder_Data)
#     ModalInfo_Writer("Analysis_Options", Data=Analysis_Options)
#
#
#
#     def EQ_Analysis(Earthquake, Scaling):
#
#
#         Scaling_id = Earthquake[15].index(Scaling) + 1
#         g_motion_id = Earthquake[0]
#         GM_Tag = int(str(g_motion_id) + str(Scaling_id))
#
#         Earthquake_Name = Earthquake[1]
#         directory = Earthquake[2]
#         filename = Earthquake[3]
#         skiprows = Earthquake[4]
#         acc_unit = Earthquake[5]
#         direction = Earthquake[6]
#         time_step_increment = Earthquake[7]
#         lamda = Scaling
#         alpha = Earthquake[9]
#         xi = Earthquake[10]
#         dt = Earthquake[11]
#         n_steps = Earthquake[12]
#         max_iter = Earthquake[13]
#         tol = Earthquake[14]
#
#
#
#
#
#
#
#         ODB_Load = Earthquake_Name + "_" + str(Scaling)
#         opp.createODB(Model_Name, ODB_Load, Nmodes=Modes_No)
#         acc_dir = os.path.join(os.getcwd(), directory, filename)
#
#         if direction == 'X':
#             # #Modal Analysis needs to be done before or time period should be provided Explicitly
#             omega = np.loadtxt(os.path.join(Eigen_Filename), skiprows=1)[0, 1]
#             d_o_f = 1
#         else:
#             omega = np.loadtxt(os.path.join(Eigen_Filename), skiprows=1)[2, 1]
#             d_o_f = 2
#
#         # Reading omega for obraining Rayleigh damping model
#         a_R, b_R = (0, 2 * xi / omega)
#
#         # Serial Number must start from the end of index of naming of loading either static loading, pushover or any other
#         Serial_No = GM_Tag
#
#
#
#         ## Analysis Parameters
#         accelerogram = np.loadtxt(acc_dir, skiprows=skiprows)  # Loads accelerogram file
#         def accelerogram_adjuster(accelerogram):
#             try:
#                 row, column = np.shape(accelerogram)
#             except:
#                 column = 1
#             factor = 1
#             if acc_unit[0] == "m":
#                 factor = m / sec ** 2
#             if acc_unit[0] == "c":
#                 factor = cm / sec ** 2
#             if acc_unit[0] == "i":
#                 factor = inch / sec ** 2
#             if acc_unit[0] == "f":
#                 factor = ft / sec ** 2
#
#             Acceleration = []
#             if column > 1:
#                 for data in accelerogram:
#                     for accln in data:
#                         Acceleration.append(accln * factor)
#                 accelerogram = np.array(Acceleration)
#
#             else:
#                 for accln in accelerogram:
#                     Acceleration.append(accln * factor)
#                 accelerogram = np.array(Acceleration)
#
#             return accelerogram
#         accelerogram = accelerogram_adjuster(accelerogram)
#
#
#
#         def TH_Time_Estimate(time_steps=100):
#             Serial_No1 = int(str(GM_Tag) + str(1))
#
#             # Uses the norm of the left hand side solution vector of the matrix equation to
#             # determine if convergence has been reached
#             ops.test(Analysis_Options[3], tol, max_iter, 0, 0)
#
#             # RCM numberer uses the reverse Cuthill-McKee scheme to order the matrix equations
#             ops.numberer(Analysis_Options[1])
#
#             # Construct a BandGeneralSOE linear system of equation object
#             ops.system(Analysis_Options[2])  # ('BandGen')
#
#             # The relationship between load factor and time is input by the user as a
#             # series of discrete points
#
#             ops.timeSeries('Path', Serial_No1, '-dt', dt, '-values', *accelerogram, '-factor', lamda)
#
#             # allows the user to apply a uniform excitation to a model acting in a certain direction
#             ops.pattern('UniformExcitation', Serial_No1, d_o_f, '-accel', Serial_No1)
#
#             # Constructs a transformation constraint handler,
#             # which enforces the constraints using the transformation method.
#             ops.constraints(Analysis_Options[0])
#
#             # Create a Newmark integrator.
#             ops.integrator(Analysis_Options[5], 0.5, 0.25)
#
#             # assign damping to all previously-defined elements and nodes
#             ops.rayleigh(a_R, b_R, 0.0, 0.0)
#
#             # Introduces line search to the Newton algorithm to solve the nonlinear residual equation
#             ops.algorithm(Analysis_Options[4], True, False, False, False, 0.8, 100, 0.1, 10.0)
#
#             # Constructs the Transient Analysis object
#             ops.analysis(Analysis_Options[6])
#
#             # Measure analysis duration
#             t = 0
#             ok = 0
#
#             n_steps = time_steps
#
#             start_time = time.time()
#
#             final_time = ops.getTime() + n_steps * dt
#             dt_analysis = time_step_increment * dt
#
#             while (ok == 0 and t <= alpha * final_time):
#                 ok = ops.analyze(1, dt_analysis)
#                 t = ops.getTime()
#
#             finish_time = time.time()
#
#             est_time = finish_time - start_time
#             if ok == 0:
#                 print('Preliminary Time-History Analysis in {} Done'.format(direction))
#             else:
#                 print('Preliminary Time-History Analysis in {} Failed'.format(direction))
#
#             reset_analysis()
#
#             return est_time / time_steps
#
#
#
#         print('-----------------Running Time-History analysis-----------------')
#         print(f"------------Earthquake - {Earthquake_Name}, Lambda - {lamda}, Direction - {direction}------------")
#         print(f"------------------Analysis Started on - {dt_string}------------------")
#         TimeEst_PerStep = TH_Time_Estimate()
#         print("Estimated Completion Time:", str(datetime.timedelta(seconds=TimeEst_PerStep * n_steps)))
#
#
#
#
#         #Recorder
#         def FilePath_Assigner(Path):
#             def CheckMake_Dirs(Path):
#                 if os.path.exists(Path) is False:
#                     os.makedirs(Path)
#
#
#
#             Output_Folder = Path.split("/")[0]
#             File_Name = direction + "_" + Path.split("/")[-1]
#             First_Folder = Earthquake_Name
#             Second_Folder = str(lamda)
#             File_Path =Output_Folder + '/' +  First_Folder + "/" + Second_Folder + "/" + File_Name
#
#             Final_Folder = os.path.join(os.getcwd(),Output_Folder, First_Folder, Second_Folder)
#             CheckMake_Dirs(Final_Folder)
#             return File_Path
#         if int(Analysis_Options[7]):
#             for Records in Recorder_Data:
#                 nodes = Model_Data["Node"][Records[2]]
#
#                 File_Path = FilePath_Assigner(Records[1])
#                 ops.recorder(Records[0], '-file', File_Path, '-time',
#                              '-node', *nodes, '-dof', *list(range(1, Records[3] + 1)), Records[4])
#
#
#
#
#         # Uses the norm of the left hand side solution vector of the matrix equation to
#         # determine if convergence has been reached
#         ops.test(Analysis_Options[3], tol, max_iter, 0, 0)
#
#         # RCM numberer uses the reverse Cuthill-McKee scheme to order the matrix equations
#         ops.numberer(Analysis_Options[1])
#
#         # Construct a BandGeneralSOE linear system of equation object
#         ops.system(Analysis_Options[2])  # ('BandGen')
#
#         # The relationship between load factor and time is input by the user as a
#         # series of discrete points
#
#         ops.timeSeries('Path', Serial_No, '-dt', dt, '-values', *accelerogram, '-factor', lamda)
#
#         # allows the user to apply a uniform excitation to a model acting in a certain direction
#         ops.pattern('UniformExcitation', Serial_No, d_o_f, '-accel', Serial_No)
#
#         # Constructs a transformation constraint handler,
#         # which enforces the constraints using the transformation method.
#         ops.constraints(Analysis_Options[0])
#
#         # Create a Newmark integrator.
#         ops.integrator(Analysis_Options[5], 0.5, 0.25)
#
#         # assign damping to all previously-defined elements and nodes
#         ops.rayleigh(a_R, b_R, 0.0, 0.0)
#
#         # Introduces line search to the Newton algorithm to solve the nonlinear residual equation
#         ops.algorithm(Analysis_Options[4], True, False, False, False, 0.8, 100, 0.1, 10.0)
#
#         # Constructs the Transient Analysis object
#         ops.analysis(Analysis_Options[6])
#
#
#
#
#         # Measure analysis duration
#         t = 0
#         ok = 0
#
#
#         start_time = time.time()
#
#         final_time = ops.getTime() + n_steps * dt
#         dt_analysis = time_step_increment * dt
#
#         while (ok == 0 and t <= alpha * final_time):
#             ok = ops.analyze(1, dt_analysis)
#             t = ops.getTime()
#
#         finish_time = time.time()
#
#         if ok == 0:
#             print('Time-History Analysis in {} Done in {:1.2f} seconds\n\n'.format(direction, finish_time - start_time))
#         else:
#             print('Time-History Analysis in {} Failed in {:1.2f} seconds\n\n'.format(direction, finish_time - start_time))
#
#         ops.record()
#
#         reset_analysis()
#
#
#     #________Earthquake Analysis Calling_________________
#     for index, Earthquake in enumerate(Earthquake_Info):
#         start_time = time.time()
#
#         Scalings = Earthquake[15]
#         for Scaling in Scalings:
#             EQ_Analysis(Earthquake, Scaling)
#
#         finish_time = time.time()
#         analysis_duration = finish_time - start_time
#
#         # Info Writer
#         if index == 0:
#             ModalInfo_Writer(f" ____________________TH analysis Done! ____________________")
#         ModalInfo_Writer(f"Earthquake {index + 1} - {Earthquake[1]}")
#         ModalInfo_Writer("Scalings", Data=Scalings)
#         ModalInfo_Writer("Earthquake_Info", Data=Earthquake[:-1])
#         ModalInfo_Writer(f"Analysis Time (seconds)", analysis_duration)
#


# ops.wipe()
# gmsh.finalize()