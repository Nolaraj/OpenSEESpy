import openseespy.opensees as ops
import gmsh2opensees as g2o
import gmsh

gmsh.initialize()
gmsh.open("Soil.msh")


ops.model("basicBuilder","-ndm",3,"-ndf",6)

#Add solid material model
solidMaterialTag =  1
E = 210e9  # Pa
nu = 0.3   # -
rho = 7300. # kg / m³
ops.nDMaterial('ElasticIsotropic', solidMaterialTag, E, nu, rho)

elementTags, nodeTags, elementName, elementNnodes =g2o.get_elements_and_nodes_in_physical_group("Solid", gmsh.model)


g2o.add_nodes_to_ops(nodeTags, gmsh.model)


#Add solid elements
for eleTag, eleNodes in zip(elementTags, nodeTags):
	ops.element('FourNodeTetrahedron', eleTag, *eleNodes, solidMaterialTag)


elementTags, nodeTags, elementName, elementNnodes = g2o.get_elements_and_nodes_in_physical_group("Fixed", gmsh.model)

g2o.fix_nodes(nodeTags, "XYZ")


#add a load
ts_tag = 1
ops.timeSeries('Constant', ts_tag)

patternTag = 1
ops.pattern('Plain', patternTag, ts_tag)

loaded_node = 25
Fx = 10000.
Fy = 0.
Fz = 0  #N
ops.load(loaded_node, Fx, Fy, Fz) #, 0, 0, 0)

ops.printModel()

ops.system("UmfPack")
ops.numberer("Plain")
ops.constraints('Plain')
ops.integrator("LoadControl", 1.0)
ops.algorithm("Linear")
ops.analysis("Static")
ops.analyze(1)

# ops.system("BandGen")
# ops.numberer("RCM")
# ops.constraints('Plain')
# ops.integrator("LoadControl", 1.0 )
# ops.algorithm("Linear")
# ops.analysis("Static")
# ops.analyze(1)


for node in ops.getNodeTags():
	disp = ops.nodeDisp(node)
	print(f"node # {node} {disp=}")

viewnum = g2o.visualize_displacements_in_gmsh(gmsh.model)

gmsh.fltk.run()

gmsh.finalize()