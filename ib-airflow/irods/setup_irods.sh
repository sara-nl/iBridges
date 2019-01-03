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
    ) | /var/lib/irods/packaging/setup_irods.sh
fi

/app/sleep.sh
