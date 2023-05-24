import gmsh
import numpy as np
import openseespy.opensees as ops
from Excel_Extraction import *
import gmsh2opensees as g2o
import math
from numpy import setdiff1d
Equal_DOF, AbsorbantMaterials, AbsorbantElements, BaseRes = Soil_BC()


def NodeTags(Physical_Group = "Solid", model = gmsh.model):
    eleTags, nodeTags, eleName, eleNodes = g2o.get_elements_and_nodes_in_physical_group(Physical_Group, model)
    return nodeTags

def RemoveNodeDuplicates(NodeTags):
    Nodes = []
    for node in NodeTags:
        Nodes += node
    Nodes = np.unique(np.array(Nodes))
    return Nodes

def Soil_Modeling():

    # Initialization
    gmsh.initialize()
    gmsh.open("Soil.msh")
    ops.model('basicBuilder', '-ndm', 3, "-ndf", 6)
    model = gmsh.model


    # Nodes Definitions
    g2o.add_nodes_to_ops(NodeTags(), model)


    # Adding solid elements of mesh
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
    viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model)
    # return model

model = Soil_Modeling()




# ops.wipe()
# gmsh.finalize()