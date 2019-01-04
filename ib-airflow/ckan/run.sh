#!/bin/bash

while true
do
    if [[ -z `curl http://solr:8983/solr 2>/dev/null` ]]
    then
        break
    fi
    sleep 1
done

while ! ( PGPASSWORD=ckan psql -h db ckan ckan -c '\q' );
do
    sleep 1
done

. /usr/lib/ckan/default/bin/activate
cd /usr/lib/ckan/default/src/ckan
paster db init -c /etc/ckan.ini

paster --plugin=ckan create-test-data -c /etc/ckan.ini 
paster --plugin=ckan sysadmin -c /etc/ckan.ini add ckadmin email=myemail@surfsara.nl password=ckadminckadmin
PGPASSWORD=ckan psql -h db ckan ckan -c "update \"user\" set \"apikey\"='d0af7090-fc3e-4342-8f9c-40acc28943bd' where name='ckadmin'"

/usr/lib/ckan/default/bin/paster serve /etc/ckan.ini


