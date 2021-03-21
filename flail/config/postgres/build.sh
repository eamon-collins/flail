#!/bin/bash

#########################################################
########### You can pre-populate tables here ############
#########################################################

set -e

export PGPASSWORD=${POSTGRES_PASSWORD}; psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB}  <<-EOSQL


EOSQL

