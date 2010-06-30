import numpy
import sys
import time
from sumatra.projects import load_project
from sumatra.parameters import build_parameters

project = load_project()
start_time = time.time()
    
parameter_file = sys.argv[1]
parameters = build_parameters(parameter_file)
    
record = project.new_record(parameters=parameters,
                            main_file=__file__,
                            label="api_example",
                            reason="reason for running this simulation")

numpy.random.seed(parameters["seed"])
distr = getattr(numpy.random, parameters["distr"])
data = distr(size=parameters["n"])
    
numpy.savetxt("%s.dat" % record.label, data)
    
record.duration = time.time() - start_time
record.data_key = record.datastore.find_new_files(record.timestamp)
project.add_record(record)

project.save()
