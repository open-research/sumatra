#/bin/bash
COVERAGE=coverage
$COVERAGE -e

for file in test_*.py; do
    echo $file;
    $COVERAGE -x $file;
    done

SUMATRA_SRC=$HOME/dev/sumatra

$COVERAGE -r $SUMATRA_SRC/*.py  $SUMATRA_SRC/*/*.py $SUMATRA_SRC/*/*/*.py ./test_*.py
$COVERAGE -a $SUMATRA_SRC/*.py  $SUMATRA_SRC/*/*.py $SUMATRA_SRC/*/*/*.py
