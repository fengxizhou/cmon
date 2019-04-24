#!/usr/bin/bash

ps aux | grep -v -E "root|rpc|pcp|snmp|dbus|-bash|polkitd|ntp|libstor|mom_priv"
