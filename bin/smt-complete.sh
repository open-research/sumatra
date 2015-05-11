# edited manually after using 'magic' autocomplete provided
# via click: http://click.pocoo.org/4/bashcomplete/
#(smt)~/smt (enhancement/bash-complete)$ _SMT_COMPLETE=source smt
## which produces
#_smt_completion() {
#    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
#                   COMP_CWORD=$COMP_CWORD \
#                   _SMT_COMPLETE=complete $1 ) )
#    return 0
#}
#
#complete -F _smt_completion -o default smt;

_smt_completion() {

    local crp1 crp2

    crp1=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _SMT_COMPLETE=complete $1 ) )

    # note this requires labels stored in .smt/labels of CWD
    local cur prev1 want_labels labels
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev1="${COMP_WORDS[COMP_CWORD-1]}"
    labels=$(cat .smt/labels)
    case "${prev1}" in
	comment|delete|diff|migrate|repeat|run|tag)
	    crp2=( $(compgen -W "${labels}" -- ${cur}) )
	    COMPREPLY=("${crp1[@]}" "${crp2[@]}")
	    return 0
	    ;;
	*)
	    if [[ ${labels} == *${prev1}* ]]
	    then
		    crp2=( $(compgen -W "${labels}" -- ${cur}) )
		    COMPREPLY=("${crp1[@]}" "${crp2[@]}")
		    return 0
	    fi
	    COMPREPLY=("${crp1[@]}")
	    return 0
	    ;;
    esac
}

complete -F _smt_completion -o default smt;
