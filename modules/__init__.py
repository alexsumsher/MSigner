#!/usr/local/bin/python
# -*- coding:utf-8

# DB objects


from .system_vals import sysconsts
from .mqueue import mnode, Mqueue
from .dbm_member import attenders
from .dbm_rooms import mroom
from .dbm_meetings import meeting
from .dbm_user import user_tbl
from .dbm_roomschedule import room_schedule
_all_tables = [meeting, mroom, attenders, user_tbl, sysconsts, room_schedule]
