#!/usr/bin/env python
import irods.password_obfuscation as password_obfuscation


with open("/usr/lib/airflow/.irods/.irodsA", "wb") as fp:
    fp.write(password_obfuscation.encode("test"))

# Test the connection
# from irods.session import iRODSSession
# sess = iRODSSession(irods_env_file="/usr/lib/airflow/irods_environment.json",
# irods_authentication_file="/usr/lib/airflow/irodsA")
# sess.users.get('rods')
