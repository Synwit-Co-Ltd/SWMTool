import os
import re
import sys

import pypdfium2 as pdfium


# 手册有两种版式，按管脚表的样子自动区分（见 isShared）：
#   格式一，一个封装一张管脚表，如 SWM221 手册 5.1~5.10 节；
#   格式二，各个封装的管脚号并排在同一张“管脚定义”表里，如 SWM341 手册 5.8 节。

''' 管脚类型只有 I/O、I、O、S、AO、/（NC 管脚）、——（表格未填类型）这几种，
    用它排除正文里形似管脚表的行，如 “2 禁止使用 B11 引脚做输入”。
'''
PIN_TYPE = r'(?:I/O|AO|I|O|S|/|——)'

''' 格式一的管脚表的一行：管脚号 管脚名称 类型 复位后默认功能 可复用功能/备注
    如 “1 C0 I/O PC0”、“5 A15 I/O A15 QSPI0_D0, PWM1A, HALL_IN2”、“48 NC / / 悬空”；
    表头和“可复用功能”换行后的续行都不以“管脚号 + 管脚名称 + 类型”开头，不予匹配。
'''
PIN_ROW = re.compile(r'^\s*(\d{1,3})\s+(\S+)\s+' + PIN_TYPE + r'\s+\S+')

''' 管脚号单独占一行：多个管脚名共用一个焊盘时，管脚号居中、单独占一行，
    如 5.2 SWM221EBS7 的 10（B3/B4 共用）、18（A11/A14 共用）。
'''
PIN_NUM = re.compile(r'^\s*(\d{1,3})\s*$')

''' 不带管脚号的一行：管脚名称 类型 复位后默认功能 可复用功能/备注，
    紧跟在“管脚号单独占一行”的行之后，同属该管脚号，如 5.2 SWM221EBS7 的 “B4 I/O PB4”。
'''
PIN_ROW_NO_NUM = re.compile(r'^\s*(\S+)\s+' + PIN_TYPE + r'\s+\S+')

''' 格式二里一个管脚号单元格的内容：数字，或者“/”（该封装没有这个管脚）。 '''
PIN_CELL = re.compile(r'(?:\d{1,3}|/)')

''' 汉字：管脚名称列里只有字母数字，用有没有汉字来排除表头、说明文字。 '''
CHINESE = re.compile(r'[\u4e00-\u9fff]')

''' 格式二的列名去掉数字和符号后剩下的字母，用来和型号名比对：列名 “VET7/6” → “VET”、“1CET7” → “CET”。 '''
COL_LETTERS = re.compile(r'[^A-Za-z]')

''' 管脚名称省略 P 前缀时补回：A15 → PA15、C0 → PC0；VSS、VDD、XO 等特殊管脚不受影响。 '''
PORT_PIN = re.compile(r'^([A-F])(\d{1,2})$')

''' 下一个小节的标题，如 “5.2 SWM221EBS7”；管脚表跨页读到它即结束。 '''
SECTION = re.compile(r'^\s*\d+\.\d+\s+\S')


def textLines(doc, page):
	return doc[page].get_textpage().get_text_range().splitlines()


def isShared(doc, page):
	''' 判断本页所在的小节是哪种版式：共用表的表头里有“描述”列，
	    一个封装一张表的那种表头是“可复用功能/备注”（没有“描述”）。
	'''
	text = doc[page].get_textpage().get_text_range()
	return '描述' in text and '管脚名称' in text


def readPins(doc, page, count):
	''' 格式一：一个封装一张管脚表，逐行读，读到下一个小节标题或凑够管脚数为止。 '''
	pins = {}			# {管脚号: [管脚名称, ...]}，多个管脚名共用一个焊盘时记录全部名称
	pending = 0			# “管脚号单独占一行”时记下的管脚号，供其后不带管脚号的行使用
	sect = False
	for p in range(page, len(doc)):					# 管脚表一页放不下时，顺延到后面的页继续读
		for line in textLines(doc, p):
			if pins and SECTION.match(line):
				sect = True							# 已读到管脚再遇到小节标题，说明管脚表结束
				break

			row = PIN_ROW.match(line)
			if row:
				pending = int(row.group(1))
				pins.setdefault(pending, []).append(row.group(2))
				continue

			num = PIN_NUM.match(line)
			if num:
				pending = int(num.group(1))
				continue

			row = PIN_ROW_NO_NUM.match(line)
			if row and pending:
				pins.setdefault(pending, []).append(row.group(1))

		if sect or len(pins) >= count:
			break

	return pins


def charFragments(doc, page):
	''' 一页的文字片段 [(y, 文字, 左 x, 右 x), ...]：把字符按坐标合并成片段，
	    上下相距 6 磅内、左右挨着的字符算一个片段（单元格里竖排的数字 “27” 会拆成上下两个字符）。
	'''
	tp = doc[page].get_textpage()

	chars = []
	for i in range(tp.count_chars()):
		box = tp.get_charbox(i)
		left, bottom, right, top = box if isinstance(box, tuple) else (box.left, box.bottom, box.right, box.top)
		text = tp.get_text_range(i, 1)
		if text.strip():
			chars.append([left, bottom, right, text])

	chars.sort(key=lambda c: (-round(c[1] / 8.0), c[0]))

	frags = []
	for c in chars:
		if frags and abs(frags[-1][0] - c[1]) < 6.0 and -8.0 < c[0] - frags[-1][2] < 1.5:
			frags[-1][1] += c[3]
			frags[-1][2] = max(frags[-1][2], c[2])
		else:
			frags.append([c[1], c[3], c[2], c[0]])

	return [(y, re.sub(r'\s+', '', text), x0, x1) for y, text, x1, x0 in frags]


def textRows(frags, gap=9.0):
	''' 把一页的片段按 y 聚成行：与上一行相差 {gap} 磅以内算同一行。
	    表里一行的管脚号可能竖排成上下两段，行距最窄时（只有一行管脚名的行）约 13 磅，故取 9 磅。
	'''
	rows = []
	for f in sorted(frags, reverse=True):
		if rows and rows[-1][0] - f[0] < gap:
			rows[-1][1].append(f)
		else:
			rows.append([f[0], [f]])

	return rows


def textCols(values, gap=10.0):
	''' 把一串 x 坐标按间距聚成几组，用于找出表格里各列的 x 位置。 '''
	cols = []
	for v in sorted(values):
		if cols and v - cols[-1][-1] < gap:
			cols[-1].append(v)
		else:
			cols.append([v])

	return cols


def readSharedPins(doc, page, chip, count):
	''' 格式二：各个封装的管脚号并排在一张表里，一个封装占一列。表头是竖排的列名（VET7/6、RET7/6 …），
	    管脚号和管脚名称排在同一行，没法按行首的文字匹配，只能按字符坐标把表格还原成行列后再读。
	'''
	if not count:
		raise ValueError('共用管脚表按管脚数找封装列，封装名末尾要带上管脚数（如 LQFP-64）')

	headers, firstHead, pages = [], [], []
	for p in range(page, len(doc)):
		frags = charFragments(doc, p)

		if pages and any(SECTION.match(line) for line in textLines(doc, p)[:10]):
			break								# 已读过管脚再遇到小节标题（在页首），说明管脚表结束

		band = [f[0] for f in frags if '描述' in f[1] or '管脚名称' in f[1]]
		band = (min(band) - 34, max(band) + 8) if band else (0, 0)		# 表头那一带（含竖排的列名）
		heads = [f for f in frags if band[0] <= f[0] <= band[1]]
		headers += heads
		firstHead = firstHead or heads		# 列名只看第一页，后面各页的表头是重复的
		pages.append((p, [f for f in frags if not band[0] <= f[0] <= band[1]]))

	colX = [sum(c) / len(c) for c in textCols([(f[2] + f[3]) / 2 for f in headers
	                                           if f[3] < 200 and not CHINESE.search(f[1])])]
	colName = [''.join(t for y, t, x0, x1 in sorted(firstHead) if abs((x0 + x1) / 2 - x) < 17)
	           for x in colX]					# 竖排的列名按 y 从小到大（从下往上）读

	rows = []									# [页, 管脚号单元格的中心 y, {列: 管脚号}, [管脚名片段]]
	for p, body in pages:
		for y, fs in textRows(body):
			cell = {}
			for fy, t, x0, x1 in fs:
				mid = (x0 + x1) / 2
				for i, x in enumerate(colX):
					if abs(mid - x) < 17 and PIN_CELL.fullmatch(t):
						cell.setdefault(i, []).append((x0, fy, t))

			if len(cell) >= 2:					# 可复用功能、描述等列的行没有管脚号，不予理会
				rows.append([p, sum(fy for v in cell.values() for x, fy, t in v) / sum(map(len, cell.values())),
				             {i: ''.join(t for x, fy, t in sorted(v)) for i, v in cell.items()}, []])

	numMax = colX[-1] + 10						# 管脚号列的右界：最后一列的中心再往右一个单元格
	funcX = [f[2] for p, body in pages for f in body if f[2] > numMax and f[1].endswith('/')]
	funcMin = min(funcX) if funcX else numMax + 120		# 可复用功能列的左界，名称列到它为止
	for p, body in pages:
		for fy, t, x0, x1 in body:				# 管脚名称：管脚号列右边、可复用功能列左边的片段
			if x0 > numMax and x1 < funcMin + 1 and t not in ('——', '/') and not CHINESE.search(t):
				near = min([r for r in rows if r[0] == p], key=lambda r: abs(r[1] - fy))
				if abs(near[1] - fy) < 12:		# 换行的管脚名（如 EFLASHV+S）按行就近附到同一行
					near[3].append((x0, t))

	colPins = [{} for _ in colX]
	for row in rows:
		if not row[3]:
			continue							# 没有管脚名的行（小节标题、跨页残留的表头等）跳过
		name = ''.join(t for x, t in sorted(row[3]))
		for i, v in row[2].items():
			if v.isdigit() and int(v):
				colPins[i][int(v)] = [name]		# 与格式一同样记录成名称列表（表里一个管脚只有一个名称）

	cols = [i for i in range(len(colX)) if len(colPins[i]) == count]
	if len(cols) > 1:							# 管脚数相同的列（如 CET7、SCET6 都是 48 脚）用型号名挑
		cols = [i for _, i in sorted(((len(COL_LETTERS.sub('', colName[i])), i) for i in cols
		                              if COL_LETTERS.sub('', colName[i]) in chip), reverse=True)] or cols

	if not cols:
		cols = '、'.join('%s(%d)' % (n, len(colPins[i])) for i, n in enumerate(colName))
		raise ValueError(f'第 {page} 页起的管脚定义表里没有 {count} 个管脚的封装列（{cols}），请确认封装名')

	return colPins[cols[0]]


def parsePKG(pdf, page, pkg, dir, chip):
	# 解析 {pdf} 的 {page} 页的 {pkg} 封装，将生成信息写入 {dir} 目录下的 {chip}.txt 文件中
	count = int(re.search(r'\d+\s*$', pkg).group())		# 封装名末尾的数字即管脚数，如 LQFP-48 → 48

	with pdfium.PdfDocument(pdf) as doc:
		if isShared(doc, page):				# 各个封装的管脚号并排在同一张表里（SWM341 手册）
			pins = readSharedPins(doc, page, chip, count)
		else:								# 一个封装一张管脚表（SWM221 手册）
			pins = readPins(doc, page, count)

	if len(pins) != count:
		raise ValueError(f'{pdf} 第 {page} 页的 {pkg} 解析到 {len(pins)} 个管脚（应为 {count} 个），请确认页码')

	with open(os.path.join(dir, chip + '.txt'), 'w', encoding='utf-8') as txtf:
		txtf.write(pkg + '\n\n')
		for num, names in sorted(pins.items()):
			name = '/'.join(PORT_PIN.sub(r'P\1\2', name) for name in names)	# 共用焊盘的管脚记录全部名称，如 10: PB3/PB4
			txtf.write('%2d: %s\n' % (num, name))


if __name__ == '__main__':
	# SWM341 手册把各个封装的管脚号并排放在 5.8“管脚定义”表里，所以型号不同、页码相同（第 24 页起）
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-100', 'SWM341', 'SWM341VET7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-64',  'SWM341', 'SWM341RET7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-48',  'SWM341', 'SWM341CET7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-100', 'SWM341', 'SWM34SVET6')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-64',  'SWM341', 'SWM34SRET6')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-48',  'SWM341', 'SWM34SCET6')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'QFN-80',  'SWM341', 'SWM34SMEU6')

	sys.exit()
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 19, 'LQFP-48', 'SWM221', 'SWM221CBT7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 22, 'SSOP-24', 'SWM221', 'SWM221EBS7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 24, 'QFN-32', 'SWM221', 'SWM221KBU7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 27, 'SSOP-24', 'SWM221', 'SWM22PE8S7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 29, 'QFN-40', 'SWM221', 'SWM22DD8U7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 32, 'SSOP-28', 'SWM221', 'SWM22PG8S7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 34, 'SSOP-28', 'SWM221', 'SWM221GBS7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 39, 'QFN-32', 'SWM221', 'SWM22DK8U7')
	parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 42, 'QFN-40', 'SWM221', 'SWM221DBU7')
