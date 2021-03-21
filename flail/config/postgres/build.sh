#!/bin/bash

#########################################################
########### You can pre-populate tables here ############
#########################################################

set -e

export PGPASSWORD=${POSTGRES_PASSWORD}; psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d flail  <<-EOSQL

# INSERT INTO "customImport_import" (id, name) 
# VALUES 
# (1, 'assignment'),
# (2, 'generic_credit_card'),
# (3, 'item'),
# (4, 'organization'),
# (5, 'project_notes'), 
# (6, 'project'),
# (7, 'person'),
# (8, 'task')
# ON CONFLICT DO NOTHING;

EOSQL

