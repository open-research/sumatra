args <- commandArgs(TRUE)
if (length(args) != 4)
    stop("Usage: Rscript script_filename package_split_string element_split_string name_value_split_string")
if(args[2] == args[3] || args[2] == args[4] || args[3] == args[4])
    stop("Usage: Rscript script_filename package_split_string element_split_string name_value_split_string \n
                 all split_string must differ!")
packages_used <- function(script_filename) {
    parsed_script <- parse(script_filename, keep.source=TRUE)
    parse_data <- getParseData(parsed_script)
    script_calls <- parse_data[["text"]]
    script_pkgs <- script_calls[which(script_calls == "library" | script_calls == "require" ) + 3]
    script_pkgs <- Filter(function(x) !(x %in% unique(c(names(formals(require)),
                                         names(formals(library))))), script_pkgs)
    script_pkgs_named <- script_calls[which(script_calls == "package" ) + 2]
    unlist(unique(c(script_pkgs, script_pkgs_named)))
}
packages_info <- function(script_filename) {
    pkg_names <- packages_used(script_filename)
    pkgs <- lapply(pkg_names, packageDescription, encoding = NA)
    pkg_paths <- lapply(pkgs, function(x)
                        tryCatch(attr(x, "file"),
                                 error= function(e) "unknown", finally="unknown"))

    pkg_paths <- lapply(pkg_paths, function(x) gsub("/Meta/package.rds", "", x))
    pkg_paths[lapply(pkg_paths, length) == 0] <- "NA"
    pkg_vers <- lapply(pkgs, function(x)
                       tryCatch(x[["Version"]],
                                error= function(e) "unknown",
                                finally="unknown"))
    pkg_src <- lapply(pkgs, function(x)
                      tryCatch(x[["Repository"]],
                               error= function(e) "unknown",
                               finally="unknown"))
    outlist <- mapply(list, pkg_names, pkg_paths, pkg_vers, pkg_src, SIMPLIFY=FALSE, USE.NAMES=FALSE)
    lapply(outlist, function(x) setNames(x, c("name", "path", "version", "source")))
}
output <- packages_info(args[1])
for(p in output) {
    cat(args[2])
    for(n in names(p)){
        cat(n, args[4], p[[n]], args[3])
    }
}
