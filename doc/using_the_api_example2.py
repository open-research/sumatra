import numpy
import sys
from sumatra.parameters import build_parameters
from sumatra.decorators import capture
    
parameter_file = sys.argv[1]
parameters = build_parameters(parameter_file)

@capture
def main(parameters):
    numpy.random.seed(parameters["seed"])
    distr = getattr(numpy.random, parameters["distr"])
    data = distr(size=parameters["n"])
    numpy.savetxt("%s.dat" % parameters["sumatra_label"], data)
  
main(parameters)
