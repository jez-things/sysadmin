#!/bin/bash


: ${DBNAME:="mqtt.db"}

dbq () {
	if ! sqlite3 -line ${DBNAME} "${1:?too few args}"; then
		echo "sqlite3 failure!"
		echo "sqlite3 ${DBNAME} ${1:?too few args}"
		exit 3
	fi
}

show_counters () {
	tmp_cnt=$(sqlite3 ${DBNAME} 'select COUNT(*) from temperature;')
	l_cnt=$(sqlite3 ${DBNAME} 'select COUNT(*) from light;' )
	h_cnt=$(sqlite3 ${DBNAME} 'select COUNT(*) from humidity;')
	printf '.-----| DB records |------------------\n'
	printf '|\n'
	printf '| Temperature\tLight\tHumidity    \n'
	printf '|  %10d\t%5d\t%8d \n' "${tmp_cnt}" "${l_cnt}" "${h_cnt}"
	printf '`-------------------------------------\n'
}

show_schemas () {
	for t in $(dbq '.tables');
	do
		dbq ".schema $t"
	done

}

lastdate=$(dbq 'select date from temperature order by date DESC limit 1;')
temp_last_up=$(awk 'BEGIN { print strftime("%H:%M:%S", '"${lastdate}"'); }')

lastdate=$(dbq 'select date from light order by date DESC limit 1;')
light_last_up=$(awk 'BEGIN { print strftime("%H:%M:%S", '"${lastdate}"'); }')

lastdate=$(dbq 'select date from humidity order by date DESC limit 1;')
humidity_last_up=$(awk 'BEGIN { print strftime("%H:%M:%S", '"${lastdate}"'); }')

#echo "Most recent record: $(/usr/bin/date --date=@$maxdate)"
#/usr/bin/date #--date="@$maxdate"
show_schemas;
printf "Last updates:.\n"
printf "%s\n" "----------------------------------------------|"
printf "|  %10s  |  %10s  |  %10s  |\n" "humidity" "temp" "light"
printf "|  %10s  |  %10s  |  %10s  |\n" "$humidity_last_up" "$temp_last_up" "$light_last_up"
printf "%s\n" "----------------------------------------------|"

echo ;
show_counters;


