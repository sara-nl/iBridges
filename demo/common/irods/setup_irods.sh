#!/bin/bash
set -x
set -e

while ! curl irodsdb:5432 2>&1 | grep '52'
do
  sleep 1
done

while ! ( PGPASSWORD=irods psql -h irodsdb ICAT irods -c '\q' );
do
    sleep 1
done

if [ -f /etc/irods/service_account.config ]
then
    echo 'setup without service account'
    cat /app/setup_answers.txt | /var/lib/irods/packaging/setup_irods.sh
else
    ( echo irods
      echo irods
      cat /app/setup_answers.txt
    ) | /var/lib/irods/packaging/setup_irods.sh &
fi

# wait for service
set +e
curl localhost:1247
res=$?
while [[ $res -ne  0 ]]
do
    curl localhost:1247
    res=$?
    sleep 1
done
set -e

if [ "${IRODS_WITH_PIDS}" = "1" ]; then
    echo "register pid"
    /app/register_pid_pep.py
fi


set +e
if [ "${IRODS_WITH_PIDS}" = "1" ]; then
    echo "wait for pids"
    curl 'handle:5001/hrls/handles/21.T12995?URL=irods'
    res=$?
    while [[ $res -ne  0 ]]
    do
        curl 'handle:5001/hrls/handles/21.T12995?URL=irods'
        res=$?
        sleep 1
    done
fi
set -e

/app/sample-data/prepare_collections.py

/app/sleep.sh
