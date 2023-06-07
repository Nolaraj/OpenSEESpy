import datetime
import os

import numpy as np
#import vfo.vfo
# import opsvis as opsv

from Modelling import *
from Basic_Info import *
import Basic_Info as BI



def reset_analysis():
    """
    Resets the analysis by setting time to 0,
    removing the recorders and wiping the analysis.
    """

    # Reset for next analysis case
    ##  Set the time in the Domain to zero
    ops.setTime(0.0)
    ## Set the loads constant in the domain
    ops.loadConst()
    ## Remove all recorder objects.
    ops.remove('recorders')
    ## destroy all components of the Analysis object
    ops.wipeAnalysis()


def Gravity_Analysis():
    Recorder_Data, Analysis_Options = GravityA_Data()
    steps = Analysis_Options[7]


    ops.initialize()
    start_time = time.time()
    ODB_Load = "Gravity"
    opp.createODB(Model_Name, ODB_Load)


    # Recorder
    if int(Analysis_Options[8]):
        for Records in Recorder_Data:
            File_Path =  Records[1]

            if Records[0] == "Node":
                nodes = Model_Data["Node"][Records[2]]
                ops.recorder(Records[0], '-file', File_Path, '-time',
                             '-node', *nodes, '-dof', *list(range(1, Records[3] + 1)), Records[4])

            if Records[0] == "Element":
                nodes = Model_Data["BC_Element"]["All"]
                ops.recorder(Records[0], '-file', File_Path, '-time',
                             '-ele', *nodes,  Records[4])


    # enforces the constraints using the transformation method
    ops.constraints(Analysis_Options[0])

    # RCM numberer uses the reverse Cuthill-McKee scheme to order the matrix equations
    ops.numberer(Analysis_Options[1])

    # Construct a BandGeneralSOE linear system of equation
    ops.system(Analysis_Options[2])

    # Uses the norm of the left hand side solution vector of the matrix equation to
    # determine if convergence has been reached
    ops.test(Analysis_Options[3], 1.0e-6, 100, 0, 2)

    # Uses the Newton-Raphson algorithm to solve the nonlinear residual equation
    ops.algorithm(Analysis_Options[4])

    # Uses LoadControl integrator object
    ops.integrator(Analysis_Options[5], 1 / steps)

    # Constructs the Static Analysis object
    ops.analysis(Analysis_Options[6])



    # Performs the analysis
    ops.analyze(steps)
    ops.record()

    #


    print("__________________________Gravity analysis Done!__________________________")
    finish_time = time.time()
    analysis_duration = finish_time - start_time

    # Info Writer
    ModalInfo_Writer(f" ____________________Gravity analysis Done! ____________________")
    ModalInfo_Writer("Recorder_Data", Data=Recorder_Data)
    ModalInfo_Writer("Analysis_Options", Data=Analysis_Options)
    ModalInfo_Writer(f"Analysis Time (seconds)", analysis_duration)

    reset_analysis()
    return 0




def Modal_Analysis():
    Recorder_Data, Analysis_Options = Modal_Data()
    Modes_No = Analysis_Options[0]

    ops.initialize()
    start_time = time.time()
    ODB_Load = "Modal"
    opp.createODB(Model_Name, ODB_Load, Nmodes=Modes_No)

    if int(Analysis_Options[8]):
        for Records in Recorder_Data:
            nodes = Model_Data["Node"][Records[2]]
            File_Path =  Records[1]
            ops.recorder(Records[0], '-file', File_Path, '-time',
                          '-node', *nodes, '-dof', *list(range(1, Records[3] + 1)), Records[4])


    # Constructs a transformation constraint handler,
    # which enforces the constraints using the transformation method.
    ops.constraints(Analysis_Options[1])

    # Constructs a Plain degree-of-freedom numbering object
    # to provide the mapping between the degrees-of-freedom at
    # the nodes and the equation numbers.
    ops.numberer(Analysis_Options[2])

    # Construct a BandGeneralSOE linear system of equation object
    ops.system(Analysis_Options[3])

    # Uses the norm of the left hand side solution vector of the matrix equation to
    # determine if convergence has been reached
    ops.test(Analysis_Options[4], 1.0e-12, 25, 0, 2)

    # Uses the Newton-Raphson algorithm to solve the nonlinear residual equation
    ops.algorithm(Analysis_Options[5])

    # Create a Newmark integrator.
    ops.integrator(Analysis_Options[6], 0.5, 0.25)

    # Constructs the Transient Analysis object
    ops.analysis(Analysis_Options[7])

    # Eigenvalue analysis
    lamda = np.array(ops.eigen(Modes_No))

    # Writing Eigenvalue information to file
    # lambda gives the value of eigen value in term of rad^2/sec^2
    #Omega gives the circular frequecny - sqrt of lambda
    Eigen_Filename = Analysis_Options[9]
    Eigen_FilenPath = os.path.join(os.getcwd(),Eigen_Filename)
    with open(Eigen_FilenPath, "w") as eig_file:
        # Writing data to a file
        eig_file.write("lambda omega period frequency\n")
        for l in lamda:
            #This is the true concept as l never equals to zero in any cases
            line_to_write = [l, l ** 0.5, 2 * np.pi / (l ** 0.5), (l ** 0.5) / (2 * np.pi)]
            eig_file.write('{:2.6e} {:2.6e} {:2.6e} {:2.6e}'.format(*line_to_write))
            eig_file.write('\n')

    # Record eigenvectors
    ops.record()




    print("__________________________Modal analysis Done!__________________________")
    finish_time = time.time()
    analysis_duration = finish_time - start_time

    # Info Writer
    ModalInfo_Writer(f" ____________________Modal analysis Done! ____________________")
    ModalInfo_Writer("Recorder_Data", Data=Recorder_Data)
    ModalInfo_Writer("Analysis_Options", Data=Analysis_Options)
    ModalInfo_Writer(f"Analysis Time (seconds)", analysis_duration)

    reset_analysis()
    return Eigen_Filename




def TH_Analysis():
    ops.initialize()

    Recorder_Data, Analysis_Options, Earthquake_Info = TH_Data()
    Eigen_Filename = Modal_Analysis()  # Eigen Value Extraction

    # Info Writer
    ModalInfo_Writer(f" ____________________TH analysis____________________")
    ModalInfo_Writer("Recorder_Data", Data=Recorder_Data)
    ModalInfo_Writer("Analysis_Options", Data=Analysis_Options)



    def EQ_Analysis(Earthquake, Scaling):


        Scaling_id = Earthquake[15].index(Scaling) + 1
        g_motion_id = Earthquake[0]
        GM_Tag = int(str(g_motion_id) + str(Scaling_id))

        Earthquake_Name = Earthquake[1]
        directory = Earthquake[2]
        filename = Earthquake[3]
        skiprows = Earthquake[4]
        acc_unit = Earthquake[5]
        direction = Earthquake[6]
        time_step_increment = Earthquake[7]
        lamda = Scaling
        alpha = Earthquake[9]
        xi = Earthquake[10]
        dt = Earthquake[11]
        n_steps = Earthquake[12]
        max_iter = Earthquake[13]
        tol = Earthquake[14]







        ODB_Load = Earthquake_Name + "_" + str(Scaling)
        opp.createODB(Model_Name, ODB_Load, Nmodes=Modes_No)
        acc_dir = os.path.join(os.getcwd(), directory, filename)

        if direction == 'X':
            # #Modal Analysis needs to be done before or time period should be provided Explicitly
            omega = np.loadtxt(os.path.join(Eigen_Filename), skiprows=1)[0, 1]
            d_o_f = 1
        else:
            omega = np.loadtxt(os.path.join(Eigen_Filename), skiprows=1)[2, 1]
            d_o_f = 2

        # Reading omega for obraining Rayleigh damping model
        a_R, b_R = (0, 2 * xi / omega)

        # Serial Number must start from the end of index of naming of loading either static loading, pushover or any other
        Serial_No = GM_Tag



        ## Analysis Parameters
        accelerogram = np.loadtxt(acc_dir, skiprows=skiprows)  # Loads accelerogram file
        def accelerogram_adjuster(accelerogram):
            try:
                row, column = np.shape(accelerogram)
            except:
                column = 1
            factor = 1
            if acc_unit[0] == "m":
                factor = m / sec ** 2
            if acc_unit[0] == "c":
                factor = cm / sec ** 2
            if acc_unit[0] == "i":
                factor = inch / sec ** 2
            if acc_unit[0] == "f":
                factor = ft / sec ** 2

            Acceleration = []
            if column > 1:
                for data in accelerogram:
                    for accln in data:
                        Acceleration.append(accln * factor)
                accelerogram = np.array(Acceleration)

            else:
                for accln in accelerogram:
                    Acceleration.append(accln * factor)
                accelerogram = np.array(Acceleration)

            return accelerogram
        accelerogram = accelerogram_adjuster(accelerogram)



        def TH_Time_Estimate(time_steps=100):
            Serial_No1 = int(str(GM_Tag) + str(1))

            # Uses the norm of the left hand side solution vector of the matrix equation to
            # determine if convergence has been reached
            ops.test(Analysis_Options[3], tol, max_iter, 0, 0)

            # RCM numberer uses the reverse Cuthill-McKee scheme to order the matrix equations
            ops.numberer(Analysis_Options[1])

            # Construct a BandGeneralSOE linear system of equation object
            ops.system(Analysis_Options[2])  # ('BandGen')

            # The relationship between load factor and time is input by the user as a
            # series of discrete points

            ops.timeSeries('Path', Serial_No1, '-dt', dt, '-values', *accelerogram, '-factor', lamda)

            # allows the user to apply a uniform excitation to a model acting in a certain direction
            ops.pattern('UniformExcitation', Serial_No1, d_o_f, '-accel', Serial_No1)

            # Constructs a transformation constraint handler,
            # which enforces the constraints using the transformation method.
            ops.constraints(Analysis_Options[0])

            # Create a Newmark integrator.
            ops.integrator(Analysis_Options[5], 0.5, 0.25)

            # assign damping to all previously-defined elements and nodes
            ops.rayleigh(a_R, b_R, 0.0, 0.0)

            # Introduces line search to the Newton algorithm to solve the nonlinear residual equation
            ops.algorithm(Analysis_Options[4], True, False, False, False, 0.8, 100, 0.1, 10.0)

            # Constructs the Transient Analysis object
            ops.analysis(Analysis_Options[6])

            # Measure analysis duration
            t = 0
            ok = 0

            n_steps = time_steps

            start_time = time.time()

            final_time = ops.getTime() + n_steps * dt
            dt_analysis = time_step_increment * dt

            while (ok == 0 and t <= alpha * final_time):
                ok = ops.analyze(1, dt_analysis)
                t = ops.getTime()

            finish_time = time.time()

            est_time = finish_time - start_time
            if ok == 0:
                print('Preliminary Time-History Analysis in {} Done'.format(direction))
            else:
                print('Preliminary Time-History Analysis in {} Failed'.format(direction))

            reset_analysis()

            return est_time / time_steps



        print('-----------------Running Time-History analysis-----------------')
        print(f"------------Earthquake - {Earthquake_Name}, Lambda - {lamda}, Direction - {direction}------------")
        print(f"------------------Analysis Started on - {dt_string}------------------")
        TimeEst_PerStep = TH_Time_Estimate()
        print("Estimated Completion Time:", str(datetime.timedelta(seconds=TimeEst_PerStep * n_steps)))




        #Recorder
        def FilePath_Assigner(Path):
            def CheckMake_Dirs(Path):
                if os.path.exists(Path) is False:
                    os.makedirs(Path)



            Output_Folder = Path.split("/")[0]
            File_Name = direction + "_" + Path.split("/")[-1]
            First_Folder = Earthquake_Name
            Second_Folder = str(lamda)
            File_Path =Output_Folder + '/' +  First_Folder + "/" + Second_Folder + "/" + File_Name

            Final_Folder = os.path.join(os.getcwd(),Output_Folder, First_Folder, Second_Folder)
            CheckMake_Dirs(Final_Folder)
            return File_Path
        if int(Analysis_Options[7]):
            for Records in Recorder_Data:
                nodes = Model_Data["Node"][Records[2]]

                File_Path = FilePath_Assigner(Records[1])
                ops.recorder(Records[0], '-file', File_Path, '-time',
                             '-node', *nodes, '-dof', *list(range(1, Records[3] + 1)), Records[4])




        # Uses the norm of the left hand side solution vector of the matrix equation to
        # determine if convergence has been reached
        ops.test(Analysis_Options[3], tol, max_iter, 0, 0)

        # RCM numberer uses the reverse Cuthill-McKee scheme to order the matrix equations
        ops.numberer(Analysis_Options[1])

        # Construct a BandGeneralSOE linear system of equation object
        ops.system(Analysis_Options[2])  # ('BandGen')

        # The relationship between load factor and time is input by the user as a
        # series of discrete points

        ops.timeSeries('Path', Serial_No, '-dt', dt, '-values', *accelerogram, '-factor', lamda)

        # allows the user to apply a uniform excitation to a model acting in a certain direction
        ops.pattern('UniformExcitation', Serial_No, d_o_f, '-accel', Serial_No)

        # Constructs a transformation constraint handler,
        # which enforces the constraints using the transformation method.
        ops.constraints(Analysis_Options[0])

        # Create a Newmark integrator.
        ops.integrator(Analysis_Options[5], 0.5, 0.25)

        # assign damping to all previously-defined elements and nodes
        ops.rayleigh(a_R, b_R, 0.0, 0.0)

        # Introduces line search to the Newton algorithm to solve the nonlinear residual equation
        ops.algorithm(Analysis_Options[4], True, False, False, False, 0.8, 100, 0.1, 10.0)

        # Constructs the Transient Analysis object
        ops.analysis(Analysis_Options[6])




        # Measure analysis duration
        t = 0
        ok = 0


        start_time = time.time()

        final_time = ops.getTime() + n_steps * dt
        dt_analysis = time_step_increment * dt

        while (ok == 0 and t <= alpha * final_time):
            ok = ops.analyze(1, dt_analysis)
            t = ops.getTime()

        finish_time = time.time()

        if ok == 0:
            print('Time-History Analysis in {} Done in {:1.2f} seconds\n\n'.format(direction, finish_time - start_time))
        else:
            print('Time-History Analysis in {} Failed in {:1.2f} seconds\n\n'.format(direction, finish_time - start_time))

        ops.record()

        reset_analysis()


    #________Earthquake Analysis Calling_________________
    for index, Earthquake in enumerate(Earthquake_Info):
        start_time = time.time()

        Scalings = Earthquake[15]
        for Scaling in Scalings:
            EQ_Analysis(Earthquake, Scaling)

        finish_time = time.time()
        analysis_duration = finish_time - start_time

        # Info Writer
        if index == 0:
            ModalInfo_Writer(f" ____________________TH analysis Done! ____________________")
        ModalInfo_Writer(f"Earthquake {index + 1} - {Earthquake[1]}")
        ModalInfo_Writer("Scalings", Data=Scalings)
        ModalInfo_Writer("Earthquake_Info", Data=Earthquake[:-1])
        ModalInfo_Writer(f"Analysis Time (seconds)", analysis_duration)


def Render():
    opp.plot_model("node", "element")
    opp.plot_modeshape(2,10)
    # opp.createODB ("Building","Dynamic_GM1", deltaT=0.5)
    #
    # # vfo.createODB(model="3DFrame", Nmodes=3)
    vfo.createODB(model="3DFrame", loadcase="Gravity", Nmodes=3, deltaT=2)
    #
    # ## opp.plot_model("node", "element")
    # vfo.plot_model("node", "element")
    # ops.wipe()
    # # vfo.plot_modeshape(model='3DFrame', modenumber=1, scale=10, setview='3D', contour='none', contourlimits=None,
    # #                    line_width=1)
    # vfo.plot_deformedshape(model="3DFrame", loadcase="Gravity", tstep=24.0, scale=50 )




Modelling_Handle()
Gravity_Analysis()
# Modal_Analysis()






# [fixed_Nodes.append(n) for n in Model_Data["Node"]["Base"]]
# # print(fixed_Nodes)
#
# #Worked
# from _model import *
# print(ops.getNP())
# fig_wi = 10
# fig_he = 20
# fig = plt.figure(figsize=(fig_wi / 2.54, fig_he / 2.54))
# fig = plt.figure()
#
# plot_model(node_labels=0, element_labels=0, fig_wi_he=(20., 14.))
# plot_defo()
#
#






# opsvis.plot_model()

# TH_Analysis()
# Render()


# Load_Name = "ChiChi_1"
#
# vfo.animate_deformedshape(model=Model_Name, loadcase=Load_Name, scale=100, moviename="dffd")
#
# ops.wipe()

# import eSEESminiPy
# eSEESminiPy.RunEQDynamicAnalysis