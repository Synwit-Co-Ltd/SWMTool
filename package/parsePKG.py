import os
import re

import pypdfium2 as pdfium


''' 管脚表的一行：管脚号 管脚名称 类型 复位后默认功能 可复用功能/备注
    如 “1 C0 I/O PC0”、“5 A15 I/O A15 QSPI0_D0, PWM1A, HALL_IN2”、“48 NC / / 悬空”；
    表头和“可复用功能”换行后的续行都不以“管脚号 + 三个字段”开头，不予匹配。
'''
PIN_ROW = re.compile(r'^\s*(\d{1,3})\s+(\S+)\s+(\S+)\s+(\S+)')

''' 管脚名称省略 P 前缀时补回：A15 → PA15、C0 → PC0；VSS、VDD、XO 等特殊管脚不受影响。 '''
PORT_PIN = re.compile(r'^([A-F])(\d{1,2})$')

''' 下一个小节的标题，如 “5.2 SWM221EBS7”；管脚表跨页读到它即结束。 '''
SECTION = re.compile(r'^\s*\d+\.\d+\s+\S')


def parsePKG(pdf, page, pkg, dir, chip):
	# 解析 {pdf} 的 {page} 页的 {pkg} 封装，将生成信息写入 {dir} 目录下的 {chip}.txt 文件中
	count = int(re.search(r'\d+\s*$', pkg).group())		# 封装名末尾的数字即管脚数，如 LQFP-48 → 48

	pins = {}
	sect = False
	with pdfium.PdfDocument(pdf) as doc:
		for p in range(page, len(doc)):					# 管脚表一页放不下时，顺延到后面的页继续读
			for line in doc[p].get_textpage().get_text_range().splitlines():
				if pins and SECTION.match(line):
					sect = True							# 已读到管脚再遇到小节标题，说明管脚表结束
					break

				row = PIN_ROW.match(line)
				if row:
					pins[int(row.group(1))] = PORT_PIN.sub(r'P\1\2', row.group(2))

			if sect or len(pins) >= count:
				break

	if len(pins) != count:
		raise ValueError(f'{pdf} 第 {page} 页的 {pkg} 解析到 {len(pins)} 个管脚（应为 {count} 个），请确认页码')

	with open(os.path.join(dir, chip + '.txt'), 'w', encoding='utf-8') as txtf:
		txtf.write(pkg + '\n\n')
		for num, name in sorted(pins.items()):
			txtf.write('%2d: %s\n' % (num, name))


if __name__ == '__main__':
	parsePKG(r'C:\Users\wmx\Desktop\华芯微特SWM221数据手册_V1.22.pdf', 19, 'LQFP-48', 'SWM221', 'SWM221CBT7')
