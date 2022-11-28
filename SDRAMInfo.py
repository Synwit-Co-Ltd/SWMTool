from typing import Dict
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class SDRAMInfo:
	name: str
	size: int				# MB
	bank: int				# 4 or 2
	tCLK: Dict[str, float]	# CLK Cycle Time (ns)
	tRP : float				# Row precharge time, Ie. Precharge to Activate delay (ns)
	tRCD: float				# Row to column delay, Ie. Activate to Command delay (ns)
	tRFC: float				# Refresh/Active to Refresh/Active Command Period (ns)


W9864G6KH_5 = SDRAMInfo(
	name = 'W9864G6KH-5',
	size = 8,
	bank = 4,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 5 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 55
)

W9864G6KH_6 = SDRAMInfo(
	name = 'W9864G6KH-6',
	size = 8,
	bank = 4,
	tCLK = {
		'2': 7.5,			# for CAS Latency = 2
		'3': 6 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 60
)

W9864G6KH_7 = SDRAMInfo(
	name = 'W9864G6KH-7',
	size = 8,
	bank = 4,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 7 				# for CAS Latency = 3
	},
	tRP  = 18,
	tRCD = 20,
	tRFC = 65
)


W9825G6DH_6 = SDRAMInfo(
	name = 'W9825G6DH-6',
	size = 32,
	bank = 4,
	tCLK = {
		'2': 7.5,			# for CAS Latency = 2
		'3': 6 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 60
)


Devices = OrderedDict([
	('W9864G6KH-5', W9864G6KH_5),
    ('W9864G6KH-6', W9864G6KH_6),
    ('W9864G6KH-7', W9864G6KH_7),
    ('W9825G6DH-6', W9825G6DH_6),
])
