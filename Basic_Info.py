#Modules Extractor

#Basic Model Info
Model_Data = {"Node" : {}, "BC_Element" : {}}
Model_Name = "Regular_Modal"
Modes_No = 0

#Default Units
m = 1.0               # Meters
KN = 1.0              # KiloNewtons
sec = 1.0             # Seconds

#Derived Units
mm = 0.001*m          # Milimeters
cm = 0.01*m           # Centimeters
ton = KN*(sec**2)/m   # mass unit (derived)
g = 9.81*(m/sec**2)   # gravitational constant (derived)
MPa = 1e3*(KN/m**2)   # Mega Pascal
GPa = 1e6*(KN/m**2)   # Giga Pascal
ft = 381/1250 * m
inch = 127/5000 * m


#Load on Each Vertical Joint
Conc_Load = 0 * KN


#Plotting Details
NDM = 3
fixed_Nodes = []
fixed_DOF = [1, 2, 3, 4, 5, 6]
