#!/bin/bash

# Run a tmux session and launch each application (2)
for application in flail-django flail-postgres
do

command="./dev/app.sh --TYPE ${application}"
tmux new-session -d -s $application $command

done

