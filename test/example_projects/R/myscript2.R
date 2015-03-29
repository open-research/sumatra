library(foreign)
library(MASS)
library(stats)

args <- commandArgs(TRUE)

if (length(args) != 4)
    stop('Usage: Rscript script_filename package_split_string element_split_string name_value_split_string')
if(args[2] == args[3] || args[2] == args[4] || args[3] == args[4])
    stop('Usage: Rscript script_filename package_split_string element_split_string name_value_split_string \n
                 all split_string must differ!')

output <- readRDS('myscript.rds')
for(p in output) {
    cat(args[2])
    for(n in names(p))
        cat(n, args[4], p[[n]], args[3])
}

