	echo -n "+-- Environment settings (ulimit,kernel parameters)"

	# ulimit settings (limits.conf)
	VAR0[0]=nofile;VAR1[0]="-n";VALUE1[0]="1024";VALUE2[0]=65536
	VAR0[1]=noproc;VAR1[1]="-u";VALUE1[1]=2047;VALUE2[1]=16384

	L=0
	i=0
	while [ $i -lt ${#VAR0[@]} ]
	do
		CURSOFT=$(su - oracle -c "ulimit ${VAR1[$i]} -S" )
		CURHARD=$(su - oracle -c "ulimit ${VAR1[$i]} -H" )
		if [ $CURSOFT -lt ${VALUE1[$i]} -o $CURSOFT -gt ${VALUE2[$i]} ]
		then
			if [ $L -eq 0 ]
			then
				echo 
				echo -n "Limits parameters"
				RES_COL=35
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Current"
				RES_COL=60
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Expected"
			fi
			GOOD=${VALUE1[$i]};ERROR=$CURSOFT
			echo 
			echo -n "${VAR0[$i]} soft"
			echo_error
			echo_good
			X=1;L=1
		fi
		if [ $CURHARD -gt ${VALUE2[$i]} ]
		then
			if [ $L -eq 0 ]
			then
				echo 
				echo -n "Limits parameters"
				RES_COL=35
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Current"
				RES_COL=60
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Expected"
			fi
			GOOD=${VALUE1[$i]};ERROR=$CURHARD
			echo 
			echo -n "${VAR0[$i]} hard"
			echo_error
			echo_good
			X=1;L=1
		fi
		let i++
	done

	# kernel parameters (sysctl.conf)
	VAR[0]=kernel.shmall;VALUE[0]=21474836480
	VAR[1]=kernel.shmmax;VALUE[1]=21474836480
	VAR[2]=kernel.shmmni;VALUE[2]=4096
	VAR[3]=kernel.sem;VALUE[3]="250	32000	100	128"
	VAR[4]=net.core.wmem_default;VALUE[4]=262144
	VAR[5]=net.core.wmem_max;VALUE[5]=1048576
	VAR[6]=net.core.rmem_default;VALUE[6]=262144
	VAR[7]=net.core.rmem_max;VALUE[7]=4194304
	VAR[8]=net.ipv4.ip_local_port_range;VALUE[8]="9000	65500"
	VAR[9]=net.ipv4.tcp_keepalive_time;VALUE[9]=3000
	VAR[10]=net.ipv4.tcp_retries2;VALUE[10]=5
	VAR[11]=net.ipv4.tcp_syn_retries;VALUE[11]=1
	VAR[12]=fs.file-max;VALUE[12]=6815744
	VAR[13]=fs.aio-max-nr;VALUE[13]=1048576

	K=0
	i=0
	while [ $i -lt ${#VAR[@]} ]
	do
		sysctl -a | grep -q "${VAR[$i]} = ${VALUE[$i]}"
		if [ $? -ne 0 ]
		then
			if [ $K -eq 0 ]
			then
				echo 
				echo -n "Kernel Parameters"
				RES_COL=35
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Current"
				RES_COL=60
				MOVE_TO_COL="echo -en \\033[${RES_COL}G"
				$MOVE_TO_COL
				echo -n "Expected"
			fi
			V=$(sysctl -a | awk ' /'${VAR[$i]}'/ { printf("%s %s %s %s\n",$3,$4,$5,$6) } ')
			ERROR=$V; GOOD=${VALUE[$i]}

			echo 
			echo -n "${VAR[$i]} is:" 
			echo_error 
			echo_good 
			X=1;K=1
		fi
		let i++
	done
	[ $L -eq 0 -a $K -eq 0 ] && (success; echo) || echo
