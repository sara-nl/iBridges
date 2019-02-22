#!/usr/bin/env python3
import irods.password_obfuscation as password_obfuscation


with open("/usr/lib/airflow/.irods/.irodsA", "w") as fp:
    pw = password_obfuscation.encode("test")
    fp.write(pw)

# Test the connection
# from irods.session import iRODSSession
# sess = iRODSSession(irods_env_file="/usr/lib/airflow/irods_environment.json",
# irods_authentication_file="/usr/lib/airflow/irodsA")
# sess.users.get('rods')
