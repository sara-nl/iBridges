#!/usr/bin/env python
import json


SERVER_CONFIG="/etc/irods/server_config.json"

with open(SERVER_CONFIG) as fp:
    data = json.load(fp)

data['re_rulebase_set'].insert(0, {'filename': 'pids'})

with open(SERVER_CONFIG, "w") as fp:
    json.dump(data, fp, indent=4)

