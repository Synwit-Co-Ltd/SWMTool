from typing import Dict, Union
from dataclasses import dataclass
from collections import OrderedDict


@dataclass
class SDRAMInfo:
	name: str
	size: int				# MB
	bank: int				# 4 or 2
	nrow: int 				# row address line count
	ncol: int 				# column address line count
	tCLK: Dict[str, float]	# CLK Cycle Time (ns)
	tRP : float				# Row precharge time, Ie. Precharge to Activate delay (ns)
	tRCD: float				# Row to column delay, Ie. Activate to Command delay (ns)
	tRFC: float				# Refresh/Active to Refresh/Active Command Period (ns)
	tRRD: Union[float, str]	# Activate to Activate on different bank (ns or tCK)
	tRAS: float				# Activate to Precharge delay (ns)


W9864G6KH_5 = SDRAMInfo(
	name = 'W9864G6KH-5',
	size = 8,
	bank = 4,
	nrow = 12,
	ncol = 8,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 5 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 55,
	tRRD = 10,
	tRAS = 40
)

W9864G6KH_6 = SDRAMInfo(
	name = 'W9864G6KH-6',
	size = 8,
	bank = 4,
	nrow = 12,
	ncol = 8,
	tCLK = {
		'2': 7.5,			# for CAS Latency = 2
		'3': 6 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 60,
	tRRD = 12,
	tRAS = 42
)

W9864G6KH_7 = SDRAMInfo(
	name = 'W9864G6KH-7',
	size = 8,
	bank = 4,
	nrow = 12,
	ncol = 8,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 7 				# for CAS Latency = 3
	},
	tRP  = 18,
	tRCD = 20,
	tRFC = 65,
	tRRD = 14,
	tRAS = 45
)


W9825G6DH_6 = SDRAMInfo(
	name = 'W9825G6DH-6',
	size = 32,
	bank = 4,
	nrow = 13,
	ncol = 9,
	tCLK = {
		'2': 7.5,			# for CAS Latency = 2
		'3': 6 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 60,
	tRRD = '2tCK',
	tRAS = 42
)


W986416KG_5 = SDRAMInfo(
	name = 'W986416KG-5',
	size = 8,
	bank = 4,
	nrow = 12,
	ncol = 8,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 5 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 55,
	tRRD = 10,
	tRAS = 40
)


W981616JG_5 = SDRAMInfo(
	name = 'W981616JG-5',
	size = 2,
	bank = 2,
	nrow = 11,
	ncol = 8,
	tCLK = {
		'2': 7,				# for CAS Latency = 2
		'3': 5 				# for CAS Latency = 3
	},
	tRP  = 15,
	tRCD = 15,
	tRFC = 55,
	tRRD = 10,
	tRAS = 40
)


PMS307416CTR_6CN = SDRAMInfo(
	name = 'PMS307416CTR-6CN',
	size = 16,
	bank = 4,
	nrow = 12,
	ncol = 9,
	tCLK = {
		'2': 10,			# for CAS Latency = 2
		'3': 6 				# for CAS Latency = 3
	},
	tRP  = 18,
	tRCD = 18,
	tRFC = 60,
	tRRD = 12,
	tRAS = 42
)


Devices = OrderedDict([
	('W9864G6KH-5', W9864G6KH_5),
    ('W9864G6KH-6', W9864G6KH_6),
    ('W9864G6KH-7', W9864G6KH_7),
    ('W9825G6DH-6', W9825G6DH_6),
    ('W986416KG-5', W986416KG_5),
    ('W981616JG-5', W981616JG_5),
    ('PMS307416CTR-6CN', PMS307416CTR_6CN)
])
