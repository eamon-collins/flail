#!/bin/bash

## Script to quickly build the base or app image
## Example: ./docker/build -f base 

# Loop through the command line arguments and 
# assign the values to local variables
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -f|--file)
    FILE="$2"
    shift # past argument
    shift # past value
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters


# Check if OS environment variable is set. If not, get it. Should return architecture.
if [[ -z "${OS}" ]]; then
    OS="$(uname -m)"
fi

if [ "$FILE" = "app" ]
then
    echo "Building app image"
elif [ "$FILE" = "base" ]
then
    echo "Building app image"
else
    echo "-f flag only accepts 'app' or 'base'"
    exit
fi

docker build -f ./docker/Dockerfile.${FILE} \
             -t flail/flail:${FILE} .
