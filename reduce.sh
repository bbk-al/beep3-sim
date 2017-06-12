#!/bin/bash
reduce "$@"
if [ $? -eq 1 -o $? -eq 0 ]
then
	exit 0
fi
