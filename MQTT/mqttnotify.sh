#!/bin/bash

MQTT_USER='tester'
MQTT_PASS='dupa.8'
MQTT_HOST='172.17.17.9'

mqtt_bcast () {
	name=$(hostname -s)

	/usr/bin/mosquitto_pub -q 1 -d -h "${MQTT_HOST}" -u "${MQTT_USER}" -P "${MQTT_PASS}" \
		-t "/system/${name}/status" -m "${1:?too few args}"

}

case ${1:?too few arguments} in
	start)
		mqtt_bcast "SYSTEM_IS_STARTING"
		;;
	reload)
		mqtt_bcast "SYSTEM_IS_RELOADING"
		;;
	*)
		mqtt_bcast "INTERNAL_ERROR"
		;;
esac

