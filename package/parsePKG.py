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
    表头和“可复用功能”换行后的续行都不以“管脚号 + 管脚名称 + 类型”开头，不予匹配；
    类型后面的“复位后默认功能”可以为空（如 SWM231 的 “14 PVDD S”，描述另起一行），所以后面可有可无。
'''
PIN_ROW = re.compile(r'^\s*(\d{1,3})\s+(\S+)\s+' + PIN_TYPE + r'(?:\s|$)')

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

''' 汉字和中文标点：管脚名称列里只有字母数字，用它排除表头文字、说明文字（含全角的 ，：； 等）。 '''
CHINESE = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')

''' 格式二的列名去掉数字和符号后剩下的字母，用来和型号名比对：列名 “VET7/6” → “VET”、“1CET7” → “CET”。 '''
COL_LETTERS = re.compile(r'[^A-Za-z]')

''' 管脚名称只写了端口字母和位数时补回 P 前缀：A15 → PA15、C0 → PC0，SWM320/341 系列还有 N2 → PN2、
    M2 → PM2、P19 → PP19；VSS、VDD、XO、XHIN 等多字母的管脚名不受影响。
'''
PORT_PIN = re.compile(r'^([A-Z])(\d{1,2})$')

''' 管脚名末尾被粘上的“类型”（见 sharedColPins）；只有剩下“大写字母+数字”时才去掉它。 '''
TYPE_TAIL = re.compile(r'(?:I/O|AO|I|O|S)$')
PIN_DIGITS = re.compile(r'[A-Z]+\d+')

''' 下一个小节的标题，如 “5.2 SWM221EBS7”；管脚表跨页读到它即结束。 '''
SECTION = re.compile(r'^\s*\d+\.\d+\s+(\S.*)$')

''' 目录里的小节标题后面跟着一串点，不是真正的小节标题。 '''
DOT_LEADER = re.compile(r'\.{4,}')


def textLines(doc, page):
	return doc[page].get_textpage().get_text_range().splitlines()


def findShared(doc, page, span=8):
	''' 找共用管脚表表头所在的那一页：共用表只有第一页有表头（含独立的“描述”列），
	    续页上没有；给的是续页时按前后 span 页找一下。
	'''
	for d in range(span):
		for p in (page - d, page + d):
			if 0 <= p < len(doc) and isShared(doc, p):
				return p

	return None


def findSection(doc, chip, page, span=40):
	''' 找 {chip} 型号那一小节标题所在的页（如 “5.4 SWM23PE6S7”）：管脚表就是从这一页或它的下一页开始的，
	    页码给成了表格的续页时可以靠它找回来。目录里带点线的小节标题不算。找不到就原样返回。
	'''
	for p in range(page, max(page - span, -1), -1):
		for line in textLines(doc, p):
			title = SECTION.match(line)
			if title and not DOT_LEADER.search(line) and title.group(1).startswith(chip):
				return p

	return page


def isShared(doc, page):
	''' 判断本页所在的小节是哪种版式：多个封装共用一张管脚表时，同一行里有好几个管脚号列
	    （表头列名是 VET7/6、320CET7 这样的封装名），按 x 聚类出来的“数字列”就会不止一个；
	    一个封装一张表则只有最左边一个管脚号列（复位后默认功能列里是 PC0 这类名称或者“/”，不是数字）。
	'''
	nums = [(f[2] + f[3]) / 2 for f in charFragments(doc, page) if f[1].isdigit()]
	return len([c for c in textCols(nums) if len(c) >= 2]) >= 2


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
	''' 一页的文字片段 [(y, 文字, 左 x, 右 x, 字序号), ...]：把字符按坐标合并成片段，
	    上下相距 6 磅内、左右挨着的字符算一个片段（单元格里竖排的数字 “27” 会拆成上下两个字符）；
	    字序号是该片段第一个字符在 PDF 文字流里的位置，用来按作者排版的顺序读表格。
	'''
	tp = doc[page].get_textpage()

	chars = []
	for i in range(tp.count_chars()):
		box = tp.get_charbox(i)
		left, bottom, right, top = box if isinstance(box, tuple) else (box.left, box.bottom, box.right, box.top)
		text = tp.get_text_range(i, 1)
		if text.strip():
			chars.append([left, bottom, right, text, i])

	chars.sort(key=lambda c: (-round(c[1] / 8.0), c[0]))

	frags = []
	for c in chars:
		if frags and abs(frags[-1][0] - c[1]) < 6.0 and -8.0 < c[0] - frags[-1][2] < 1.5:
			frags[-1][1] += c[3]
			frags[-1][2] = max(frags[-1][2], c[2])
			frags[-1][4] = min(frags[-1][4], c[4])
		else:
			frags.append([c[1], c[3], c[2], c[0], c[4]])

	return [(y, re.sub(r'\s+', '', text), x0, x1, i) for y, text, x1, x0, i in frags]


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


def sharedRowsByXY(pages, colX, numMax, nameMax):
	''' 按坐标分行：y 相近（9 磅内）的各列管脚号算一行，再按 y 就近把管脚名配到行上。 '''
	rows = []
	for p, body in pages:
		cellFrags = [f for f in body if PIN_CELL.fullmatch(f[1])
		             and min(abs((f[2] + f[3]) / 2 - x) for x in colX) < 17]
		for y, fs in textRows(cellFrags, 9.0):
			cell = {}
			for fy, t, x0, x1, i in fs:
				for c, x in enumerate(colX):
					if abs((x0 + x1) / 2 - x) < 17:
						cell.setdefault(c, []).append((x0, fy, t))
			if len(cell) >= 2:
				rows.append([p, sum(fy for v in cell.values() for x, fy, t in v) / sum(map(len, cell.values())),
				             cell, []])

	for p, body in pages:
		rowsP = [r for r in rows if r[0] == p]
		for fy, t, x0, x1, i in body:
			if rowsP and numMax < x0 and x1 < nameMax + 1 and t not in ('——', '/') and not CHINESE.search(t):
				near = min(rowsP, key=lambda r: abs(r[1] - fy))
				if abs(near[1] - fy) < 12:		# 换行的管脚名（如 EFLASHV+S）按行就近附到同一行
					near[3].append((x0, t))

	return rows


def sharedRowsByText(pages, colX, numMax, nameMax):
	''' 按 PDF 文字流的顺序分行：表里一行的内容是“各列管脚号 + 管脚名称”，作者就是照这个顺序排版的，
	    所以读到管脚名就说明本行结束，之后再读到管脚号（或本列的管脚号已经有了）就是下一行。
	    个别单元格的纵向位置偏差较大（比同行其它格低十几磅，如 SWM260 表里 PBT7 第 30 脚），
	    按坐标分行会把它算到下一行去，这种表只能用文字顺序读。
	'''
	rows = []
	for p, body in pages:
		row = None
		for f in sorted(body, key=lambda f: f[4]):
			fy, t, x0, x1 = f[:4]
			col = [i for i, x in enumerate(colX) if abs((x0 + x1) / 2 - x) < 17]
			if col and PIN_CELL.fullmatch(t):
				if row is None or row[3] or col[0] in row[2]:
					row = [p, fy, {}, []]
					rows.append(row)
				row[2].setdefault(col[0], []).append((x0, fy, t))
			elif row is not None and numMax < x0 and x1 < nameMax + 1 and t not in ('——', '/') and not CHINESE.search(t):
				row[3].append((x0, t))			# 管脚名；换行的名称（如 ADC0_VREFP）会分几个片段，都归到本行

	return rows


def sharedColPins(rows, colX):
	''' 把分行结果整理成 [ {管脚号: [管脚名称]} per 封装列 ]；没有管脚名的行（表头等）跳过。 '''
	colPins = [{} for _ in colX]
	for row in rows:
		if not row[3]:
			continue
		name = ''.join(t for x, t in sorted(row[3]))

		''' 有的手册里“类型”列紧挨着管脚名（如 SWM241 的列序是 管脚名称 类型 可复用功能），
		    相邻两格的文字会被并成一个片段，管脚名后面就挂上 “I/O”“S” 这样的类型；
		    这里把它去掉（只在剩下“端口字母+数字”时才去，免得误伤 XLI 这类管脚名）。
		'''
		trimmed = TYPE_TAIL.sub('', name)
		if trimmed != name and PIN_DIGITS.fullmatch(trimmed):
			name = trimmed

		for i, cell in row[2].items():
			value = ''.join(t for x, fy, t in sorted(cell))
			if value.isdigit() and int(value):
				colPins[i][int(value)] = [name]	# 与格式一同样记录成名称列表（表里一个管脚只有一个名称）

	return colPins


def readSharedPins(doc, page, chip, count):
	''' 格式二：各个封装的管脚号并排在一张表里，一个封装占一列。表头是竖排的列名（VET7/6、RET7/6 …），
	    管脚号和管脚名称排在同一行，没法按行首的文字匹配，只能按字符坐标把表格还原成行列后再读。
	    先按坐标分行，对不上管脚数时再按文字流顺序分行（两种办法互为补充，见上面两个函数）。
	'''
	if not count:
		raise ValueError('共用管脚表按管脚数找封装列，封装名末尾要带上管脚数（如 LQFP-64）')

	''' 给的是共用表的续页时（页面上没有小节标题，也没有表头），往前回到该小节的第一页再读。 '''
	while page > 0 and not any(SECTION.match(line) for line in textLines(doc, page)):
		page -= 1

	headers, firstHead, pages = [], [], []
	for p in range(page, len(doc)):
		frags = charFragments(doc, p)

		if pages and any(SECTION.match(line) for line in textLines(doc, p)[:10]):
			break								# 已读过管脚再遇到小节标题（在页首），说明管脚表结束

		band = [f[0] for f in frags if '描述' in f[1] or '管脚名称' in f[1]]
		band = (min(band) - 34, max(band) + 8) if band else (0, 0)		# 表头那一带（含竖排的列名）
		heads = [f for f in frags if band[0] <= f[0] <= band[1]]		# 表头那一带里的片段
		headers += heads
		firstHead += heads if not firstHead else []		# 列名只取第一页：后面各页的表头是重复的，拼起来会认不出

		pages.append((p, frags))			# 表体就是整页：数字/斜杠的单元格只有表格里有，不会认错

	cols = [f for f in headers if f[3] < 200 and not CHINESE.search(f[1])
	        and not PIN_CELL.fullmatch(f[1])]			# 表头里的列名（竖排文字）
	if not cols:
		raise ValueError(f'第 {page} 页起没有找到共用管脚表的列名，不是共用管脚表')

	colX = [sum(c) / len(c) for c in textCols([(f[2] + f[3]) / 2 for f in cols])]
	names = cols if not firstHead else [f for f in firstHead if f[3] < 200 and not CHINESE.search(f[1])
	                                    and not PIN_CELL.fullmatch(f[1])]
	colName = [''.join(t for y, t, x0, x1, i in sorted(names)
	                   if abs((x0 + x1) / 2 - x) < 17) for x in colX]

	numMax = colX[-1] + 10						# 管脚号列的右界：最后一列的中心再往右一个单元格
	funcX = [f[2] for p, body in pages for f in body if f[2] > numMax and f[1].endswith('/')]
	nameMax = min(funcX) if funcX else numMax + 120		# 可复用功能列的左界，名称列到它为止

	rows = sharedRowsByXY(pages, colX, numMax, nameMax)

	''' 表里个别单元格的纵向位置会偏得较远（如 SWM260 表里 PBT7 第 30 脚比同行其它格低 16 磅），
	    按坐标分行会把它算到相邻行去；行内管脚号上下差超过 5 磅就说明有这种情况，改用文字流顺序分行。
	'''
	spread = [max(fy for v in r[2].values() for x, fy, t in v) - min(fy for v in r[2].values() for x, fy, t in v)
	          for r in rows if r[2]]
	if spread and max(spread) > 5.0:
		rows = sharedRowsByText(pages, colX, numMax, nameMax)

	colPins = sharedColPins(rows, colX)
	cols = [i for i in range(len(colX)) if len(colPins[i]) == count]

	if not cols:
		cols = '、'.join('%s(%d)' % (n, len(colPins[i])) for i, n in enumerate(colName))
		raise ValueError(f'第 {page} 页起的管脚定义表里没有 {count} 个管脚的封装列（{cols}），请确认封装名')

	if len(cols) > 1:							# 管脚数相同的列（如 CET7、SCET6 都是 48 脚）用型号名挑
		cols = [i for _, i in sorted(((len(COL_LETTERS.sub('', colName[i])), i) for i in cols
		                              if COL_LETTERS.sub('', colName[i]) in chip), reverse=True)] or cols

	return colPins[cols[0]]


def parsePKG(pdf, page, pkg, dir, chip):
	# 解析 {pdf} 的 {page} 页的 {pkg} 封装，将生成信息写入 {dir} 目录下的 {chip}.txt 文件中
	count = int(re.search(r'\d+\s*$', pkg).group())		# 封装名末尾的数字即管脚数，如 LQFP-48 → 48

	with pdfium.PdfDocument(pdf) as doc:
		pins = None
		if isShared(doc, page):				# 看着像“各个封装的管脚号并排在一张表里”（SWM241/260/320/341 手册）
			try:
				pins = readSharedPins(doc, page, chip, count)
			except ValueError:
				pins = None					# 其实不是（比如这页还画着封装图），改按一个封装一张表来读

		if pins is None:					# 一个封装一张管脚表（SWM221/231/330 手册）
			pins = readPins(doc, page, count)

			if len(pins) != count:			# 也可能是共用表的续页（上面没有表头），回到表头那一页重读
				table = findShared(doc, page)
				if table is not None:
					try:
						pins = readSharedPins(doc, table, chip, count)
					except ValueError:
						pins = readPins(doc, page, count)	# 不是共用表：退回“一个封装一张表”的结果

			if len(pins) != count:			# 页码给成了管脚表的续页时，回到该型号小节的第一页从头读
				first = findSection(doc, chip, page)
				if first != page:
					pins = readPins(doc, first, count)

	nums = sorted(pins)

	''' 手册里偶尔把管脚号印错（如 SWM231 的 SSOP-24 最后一脚印成 25），
	    表现为比管脚数还大的号多出一个、1 到管脚数里少一个；这时按少的那个号改回来并提示。
	'''
	over = [n for n in nums if n > count]
	holes = [n for n in range(1, count + 1) if n not in pins]
	if len(nums) == count and len(over) == 1 and len(holes) == 1:
		print('%s 第 %d 页的 %s：手册里 %d 号印成了 %d 号（%s），已按 %d 号记录'
		      % (chip, page, pkg, holes[0], over[0], pins[over[0]][0], holes[0]))
		pins[holes[0]] = pins.pop(over[0])
		nums = sorted(pins)

	if nums != list(range(1, len(nums) + 1)):
		raise ValueError(f'{pdf} 第 {page} 页的 {pkg} 管脚号不是从 1 开始的连续号（读到 {nums}），请确认页码')

	if len(pins) != count:
		raise ValueError(f'{pdf} 第 {page} 页的 {pkg} 解析到 {len(pins)} 个管脚（应为 {count} 个），请确认页码')

	with open(os.path.join(dir, chip + '.txt'), 'w', encoding='utf-8') as txtf:
		txtf.write(pkg + '\n\n')
		for num, names in sorted(pins.items()):
			name = '/'.join(PORT_PIN.sub(r'P\1\2', name) for name in names)	# 共用焊盘的管脚记录全部名称，如 10: PB3/PB4
			txtf.write('%2d: %s\n' % (num, name))



if __name__ == '__main__':
	if False:			# SWM221 手册：每个封装一个小节、一张管脚表
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 19, 'LQFP-48', 'SWM221', 'SWM221CBT7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 22, 'SSOP-24', 'SWM221', 'SWM221EBS7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 24, 'QFN-32',  'SWM221', 'SWM221KBU7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 27, 'SSOP-24', 'SWM221', 'SWM22PE8S7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 29, 'QFN-40',  'SWM221', 'SWM22DD8U7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 32, 'SSOP-28', 'SWM221', 'SWM22PG8S7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 34, 'SSOP-28', 'SWM221', 'SWM221GBS7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 39, 'QFN-32',  'SWM221', 'SWM22DK8U7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM221数据手册_V1.22.pdf', 42, 'QFN-40',  'SWM221', 'SWM221DBU7')

	if True:
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM231数据手册_V1.26.pdf', 16, 'SSOP-24',  'SWM231', 'SWM231E6S7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM231数据手册_V1.26.pdf', 19, 'SOP-16',   'SWM231', 'SWM23PQ6M7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM231数据手册_V1.26.pdf', 21, 'QFN-20',   'SWM231', 'SWM231F6U7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM231数据手册_V1.26.pdf', 23, 'SSOP-24',  'SWM231', 'SWM23PE6S7')

	if False:
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM241数据手册V2.90.pdf', 17, 'LQFP-44',  'SWM241', 'SWM241PBT7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM241数据手册V2.90.pdf', 17, 'LQFP-32',  'SWM241', 'SWM241KBT7')

	if False:
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM260数据手册V2.05.pdf', 16, 'LQFP-48',  'SWM260', 'SWM260CBT7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM260数据手册V2.05.pdf', 16, 'LQFP-44',  'SWM260', 'SWM260PBT7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM260数据手册V2.05.pdf', 16, 'LQFP-32',  'SWM260', 'SWM260KBT7')

	if False:			# SWM320 手册：各个封装的管脚号并排放在 5.5“管脚描述”表里，故页码相同（第 18 页起）
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM320数据手册V2.41.pdf', 18, 'LQFP-48',  'SWM320', 'SWM320CET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM320数据手册V2.41.pdf', 18, 'LQFP-64',  'SWM320', 'SWM320RET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM320数据手册V2.41.pdf', 18, 'LQFP-100', 'SWM320', 'SWM320VET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM320数据手册V2.41.pdf', 18, 'LQFP-64',  'SWM320', 'SWM32SRET6')

	if False:			# SWM341 手册：各个封装的管脚号并排放在 5.8“管脚定义”表里，故页码相同（第 24 页起）
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-100', 'SWM341', 'SWM341VET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-64',  'SWM341', 'SWM341RET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-48',  'SWM341', 'SWM341CET7')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-100', 'SWM341', 'SWM34SVET6')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-64',  'SWM341', 'SWM34SRET6')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'LQFP-48',  'SWM341', 'SWM34SCET6')
		parsePKG(r'C:\Users\WMX\Desktop\数据手册\华芯微特SWM341数据手册V1.40.pdf', 24, 'QFN-80',   'SWM341', 'SWM34SMEU6')
