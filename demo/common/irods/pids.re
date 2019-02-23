acPostProcForPut {
    ON($objPath like "/$rodsZoneClient/public/*") {
        writeLine("serverLog", "DBG: PID RULE CREATE");
        register($objPath);
    }
}

acPostProcForCollCreate{
    ON($collName like "/$rodsZoneClient/public/*"){
         writeLine("serverLog", "DBG: PID RULE CREATE");
         register($collName);
    }
}

acPostProcForPut { }
acPostProcForCollCreate { }

register(*path) {
    msiPidCreate(*path, "", *handle);
    writeLine("serverLog", "PID RULE CREATE INFO: Creating AVU: IRODS/PID: *handle");
    createAVU("IRODS/PID", *handle, *path);
    writeLine("serverLog", "PID RULE CREATE INFO: Created AVU: IRODS/PID: *handle");
}

createAVU(*key, *value, *path) {
    #Creates a key-value pair and attaches it to a data object or collection
    writeLine("serverLog", "AVU RULE CREATE INFO: Creating AVU: Path: *path");
    msiAddKeyVal(*Keyval,*key, *value);
    #writeKeyValPairs("stdout", *Keyval, " is : ");
    msiGetObjType(*path,*objType);
    writeLine("serverLog", "AVU RULE CREATE INFO: Creating AVU: Object type: *objType");
    msiSetKeyValuePairsToObj(*Keyval, *path, *objType);
}