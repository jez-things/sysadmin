#!/bin/bash 

: ${MQTT_USER:='mosquitto'}
: ${MQTT_PASS:='siorb'}
: ${MQTT_HOST:='127.0.0.1'}

logit () {
	local msg="${1:?too few args}"
	echo "${msg}" | /usr/bin/logger -p local0.notice -t mqttnotify 
}

mqtt_bcast () {
	name=$(hostname -s)
	msg="${1:?too few args}"

	logit "${msg}"

	/usr/bin/mosquitto_pub -q 1 -d -h "${MQTT_HOST}" -u "${MQTT_USER}" -P "${MQTT_PASS}" \
		-t "/system/${name}/status" -m "${msg:-NO_STATUS_MESSAGE}"

}

case ${1:?too few arguments} in
	start)
		mqtt_bcast "SYSTEM_IS_STARTING"
		;;
	reload)
		mqtt_bcast "SYSTEM_IS_RELOADING"
		;;
	stop)
		mqtt_bcast "SYSTEM_IS_STOPPING"
		;;
	*)
		mqtt_bcast "INTERNAL_ERROR"
		;;
esac

