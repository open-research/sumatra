import numpy
import sys
import time
from sumatra.projects import load_simulation_project
from sumatra.parameters import build_parameters

project = load_simulation_project()
start_time = time.time()
    
parameter_file = sys.argv[1]
parameters = build_parameters(parameter_file)
    
sim_record = project.new_record(parameters=parameters,
                                main_file=__file__,
                                label="api_example",
                                reason="reason for running this simulation")
sim_record.register()

numpy.random.seed(parameters["seed"])
distr = getattr(numpy.random, parameters["distr"])
data = distr(size=parameters["n"])
    
numpy.savetxt("%s.dat" % sim_record.label, data)
    
sim_record.duration = time.time() - start_time
sim_record.data_key = sim_record.datastore.find_new_files(sim_record.timestamp)
project.add_record(sim_record)

project.save()
