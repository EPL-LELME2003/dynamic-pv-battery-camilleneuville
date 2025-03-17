from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeReals, minimize, SolverFactory
import matplotlib.pyplot as plt
import pyomo.environ as pyo


# Data / Parameters
load = [99,93, 88, 87, 87, 88, 109, 127, 140, 142, 142, 140, 140, 140, 137, 139, 146, 148, 148, 142, 134, 123, 108, 93] # in kWh
lf_pv = [0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 9.80E-04, 2.47E-02, 9.51E-02, 1.50E-01, 2.29E-01, 2.98E-01, 3.52E-01, 4.15E-01, 4.58E-01, 3.73E-01, 2.60E-01, 2.19E-01, 1.99E-01, 8.80E-02, 7.03E-02, 3.90E-02, 9.92E-03, 1.39E-06, 0.00E+00, 0.00E+00] #entre 0 et 1
timestep = len(load)
c_pv = 2500 # in €/kWcrete
c_batt = 1000 # in €/kWh
eff_batt_in = 0.95
eff_batt_out = 0.95
chargetime = 4  # hours to charge fully the battery

# Model
model = ConcreteModel()
model.Temps = pyo.RangeSet(0, timestep-1)  # 24 pas de temps

# Define model variables
##########################################
############ CODE TO ADD HERE ############
##########################################

model.Remplisage_Batterie = pyo.Var(model.Temps, domain=pyo.Reals)
model.Puissance_Batterie_In = pyo.Var(model.Temps, domain=pyo.NonNegativeReals)
model.Puissance_Batterie_Out = pyo.Var(model.Temps, domain=pyo.NonNegativeReals)
model.PV = pyo.Var(domain=pyo.NonNegativeReals)
model.Production_PV = pyo.Var(model.Temps, domain=pyo.NonNegativeReals)
model.Capacité_Batterie = pyo.Var(domain=pyo.NonNegativeReals)  # Pas besoin de l'indexer si constant



# Define the constraints
##########################################
############ CODE TO ADD HERE ############
##########################################


def contrainte_capacite_batterie(model, t):
    return model.Remplisage_Batterie[t] <= model.Capacité_Batterie
model.Contrainte_Capacite_Batterie = pyo.Constraint(model.Temps, rule=contrainte_capacite_batterie)

def contrainte_etat_batterie(model, t):
    return model.Remplisage_Batterie[t] >= 0
model.Contrainte_Etat_Batterie = pyo.Constraint(model.Temps, rule=contrainte_etat_batterie)


def contrainte_remplissage_batterie(model, t):
        if t == 0:
        # Condition initiale : on fixe le niveau initial de la batterie
            return model.Remplisage_Batterie[t] == model.Capacité_Batterie * 0.5 
        else:
            # Équation pour les autres instants
            return model.Remplisage_Batterie[t] == (
                model.Remplisage_Batterie[t-1] 
                + model.Puissance_Batterie_In[t] * eff_batt_in 
                - model.Puissance_Batterie_Out[t] / eff_batt_out
            )
model.Contrainte_Remplissage_Batterie = pyo.Constraint(model.Temps, rule=contrainte_remplissage_batterie)

def contrainte_production_pv(model, t):
    return model.Production_PV[t] <= model.PV*lf_pv[t]
model.Contrainte_Production_PV = pyo.Constraint(model.Temps, rule=contrainte_production_pv)

def contrainte_puissance_batterie_in(model, t):
    return model.Puissance_Batterie_In[t]  <= model.Capacité_Batterie/chargetime
model.Contrainte_Puissance_Batterie_In = pyo.Constraint(model.Temps, rule=contrainte_puissance_batterie_in)

def contrainte_puissance_batterie_out(model, t):
    return model.Puissance_Batterie_Out[t] <= model.Capacité_Batterie/chargetime
model.Contrainte_Puissance_Batterie_Out = pyo.Constraint(model.Temps, rule=contrainte_puissance_batterie_out)

def contrainte_demande(model, t):
    return model.Production_PV[t] + model.Puissance_Batterie_Out[t] - model.Puissance_Batterie_In[t] == load[t]
model.Contrainte_Demande = pyo.Constraint(model.Temps, rule=contrainte_demande)
  





# Define the objective functions
##########################################
############ CODE TO ADD HERE ############
##########################################

model.objective = pyo.Objective(expr = model.PV * c_pv + model.Capacité_Batterie * c_batt, sense=pyo.minimize)

# Specify the path towards your solver (gurobi) file
solver = SolverFactory('gurobi')
solver.solve(model)

# Results - Print the optimal PV size and optimal battery capacity
##########################################
############ CODE TO ADD HERE ############
##########################################

print("Optimal PV : ", model.PV.value)
print("Optimal Battery Capacity : ", model.Capacité_Batterie.value)


# Plotting - Generate a graph showing the evolution of (i) the load, 
# (ii) the PV production and, (iii) the soc of the battery
##########################################
############ CODE TO ADD HERE ############
##########################################

import matplotlib.pyplot as plt

temps = list(range(timestep))
pv_production = [model.Production_PV[t].value for t in model.Temps]
batt_charge = [model.Remplisage_Batterie[t].value for t in model.Temps]

plt.figure(figsize=(10,5))
plt.plot(temps, load, label="Load (kWh)", linestyle="dashed", color="black")
plt.plot(temps, pv_production, label="PV Production (kWh)", color="orange")
plt.plot(temps, batt_charge, label="Battery Charge (kWh)", color="blue")
plt.legend()
plt.xlabel("Time (hours)")
plt.ylabel("Energy (kWh)")
plt.title("Energy Flow in the System")
plt.grid()
plt.show()
