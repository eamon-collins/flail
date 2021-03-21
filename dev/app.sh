#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -t|--TYPE)
    TYPE="$2"
    shift # past argument
    shift # past value
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# Read out any unexpected parameters passed in
if [[ -n $1 ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    tail -1 "$1"
fi

# Activate virtual environment
source venv/bin/activate

# Launch the service defined in the original --TYPE 
## argument [onc-app, onc-postgres]
case $TYPE in
    onc-app )    
        python ./oncquest_doc_manager/manage.py runserver 0.0.0.0:8000; break;;
    onc-postgres ) 
        cd dev
        docker-compose up
esac


