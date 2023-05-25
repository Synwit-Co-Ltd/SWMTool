import os


def parse(path):
	pins = {}

	for line in open(path):
		pin, pad = line.split(':')

		pins[pin] = pad.strip().split()

	return pins


packages = {
	'SWM181': {},
	'SWM190': {},
	'SWM201': {},
	'SWM211': {},
	'SWM260': {},
	'SWM320': {},
	'SWM341': {},
	'SWM342': {}
}

for file in os.listdir('package'):
	if file.endswith('txt'):
		name, ext = file.split('.')
		chip = name[:6]
		if chip == 'SWM32S':
			chip = 'SWM320'
		elif chip == 'SWM34S':
			chip = 'SWM341'

		packages[chip][name] = parse(f'package/{file}')
