#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -d|--database)
    DATABASE="$2"
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

# Kill the tmux sessions containing the django application
tmux kill-session -t onc-app

# Optionally erase or turn off the database depending on the -d flag
if [ "$DATABASE" = "erase" ]; then
    tmux kill-session -t onc-postgres
    docker kill onc-db-dev
    docker rm onc-db-dev
elif [ "$DATABASE" = "off" ]; then
    tmux kill-session -t onc-postgres
    docker kill onc-db-dev
    docker rm onc-db-dev
fi