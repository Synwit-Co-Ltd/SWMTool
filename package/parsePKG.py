import os
import re
import sys

import pypdfium2 as pdfium


''' 管脚类型只有 I/O、I、O、S、AO、/（NC 管脚）、——（表格未填类型）这几种，
    用它排除正文里形似管脚表的行，如 “2 禁止使用 B11 引脚做输入”。
'''
PIN_TYPE = r'(?:I/O|AO|I|O|S|/|——)'

''' 管脚表的一行：管脚号 管脚名称 类型 复位后默认功能 可复用功能/备注
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

''' 管脚名称省略 P 前缀时补回：A15 → PA15、C0 → PC0；VSS、VDD、XO 等特殊管脚不受影响。 '''
PORT_PIN = re.compile(r'^([A-F])(\d{1,2})$')

''' 下一个小节的标题，如 “5.2 SWM221EBS7”；管脚表跨页读到它即结束。 '''
SECTION = re.compile(r'^\s*\d+\.\d+\s+\S')


def parsePKG(pdf, page, pkg, dir, chip):
	# 解析 {pdf} 的 {page} 页的 {pkg} 封装，将生成信息写入 {dir} 目录下的 {chip}.txt 文件中
	count = int(re.search(r'\d+\s*$', pkg).group())		# 封装名末尾的数字即管脚数，如 LQFP-48 → 48

	pins = {}			# {管脚号: [管脚名称, ...]}，多个管脚名共用一个焊盘时记录全部名称
	pending = 0			# “管脚号单独占一行”时记下的管脚号，供其后不带管脚号的行使用
	sect = False
	with pdfium.PdfDocument(pdf) as doc:
		for p in range(page, len(doc)):					# 管脚表一页放不下时，顺延到后面的页继续读
			for line in doc[p].get_textpage().get_text_range().splitlines():
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

	if len(pins) != count:
		raise ValueError(f'{pdf} 第 {page} 页的 {pkg} 解析到 {len(pins)} 个管脚（应为 {count} 个），请确认页码')

	with open(os.path.join(dir, chip + '.txt'), 'w', encoding='utf-8') as txtf:
		txtf.write(pkg + '\n\n')
		for num, names in sorted(pins.items()):
			name = '/'.join(PORT_PIN.sub(r'P\1\2', name) for name in names)	# 共用焊盘的管脚记录全部名称，如 10: PB3/PB4
			txtf.write('%2d: %s\n' % (num, name))


if __name__ == '__main__':
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
