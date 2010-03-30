#/bin/bash
coverage -e

for file in test_*.py; do
    echo $file;
    coverage -x $file;
    done

SUMATRA_SRC=/Users/andrew/dev/sumatra

coverage -r $SUMATRA_SRC/*.py  $SUMATRA_SRC/*/*.py $SUMATRA_SRC/*/*/*.py ./test_*.py
coverage -a $SUMATRA_SRC/*.py  $SUMATRA_SRC/*/*.py $SUMATRA_SRC/*/*/*.py
