#! python3
import os
import re

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    import pypdfium2 as pdfium            # 用于显示 package/package/ 下的封装图形
except ImportError:
    pdfium = None


class PackView(QtWidgets.QGraphicsView):
    """封装图形视图（对应 Tkinter 版的 packView 画布），事件交给 PinConfigPage 处理。"""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setBackgroundBrush(QtCore.Qt.white)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)     # 对应画布 anchor='nw'
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self._lastSize = None

    def wheelEvent(self, event):
        if not self.owner.onPackWheel(event):
            super().wheelEvent(event)                                   # 普通滚轮：交给视图滚动

    def mousePressEvent(self, event):
        if not self.owner.onPackClick(event):
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.viewport().size()
        if (size.width(), size.height()) != self._lastSize:             # 尺寸没变就不重画，避免滚动条出现/消失引起循环
            self._lastSize = (size.width(), size.height())
            self.owner.drawPack()


class PinConfigPage(QtCore.QObject):
    def __init__(self, win):
        """win 为主窗口（SWMTool），顶栏的 cmbPack/cmbMCU、tabPIN 页均来自 SWMTool.ui。"""
        super().__init__(win)

        self.win = win

        self.packDoc = None                                 # 当前封装的图形（PDF 文档）
        self.packZoom = 1.0                                 # 封装图形的缩放倍数
        self.packName = ''                                  # 从 txt 第一行读出的封装名称
        self.packPins = {}                                  # txt 记录的 {引脚号: 引脚文字}
        self.packNums = []                                  # 图形中引脚编号的位置 [(编号, l, b, r, t), ...]
        self.portFuncs = {}                                 # <MCU>_port.h 解析出的 {引脚名: [功能, ...]}
        self.packSel = {}                                   # {引脚号: 选中的功能文字}（选中后红色显示）

        self.packView = PackView(self)
        layout = QtWidgets.QVBoxLayout(win.tabPIN)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.packView)

        win.cmbMCU.currentTextChanged.connect(self.onMcuChanged)
        win.cmbPack.currentTextChanged.connect(self.onPackChanged)
        win.tabMain.currentChanged.connect(self.onPageChanged)

        self.onMcuChanged(win.cmbMCU.currentText())         # 主窗口初始化时的选中不会被信号通知，这里补一次
        self.onPackChanged(win.cmbPack.currentText())

    def onMcuChanged(self, mcu):
        self.portFuncs = self.loadPortFuncs(os.path.join('package', mcu, mcu + '_port.h'))

    def onPackChanged(self, pack):
        mcu = self.win.cmbMCU.currentText()

        self.packDoc = None
        self.packZoom = 1.0
        self.packName = ''
        self.packPins = {}
        self.packNums = []
        self.packSel = {}
        if pack:
            try:
                with open(os.path.join('package', mcu, pack + '.txt'), encoding='utf-8') as f:
                    self.packName = f.readline().strip()      # 封装名称记录在 txt 第一行
                    for line in f:                            # 其余行记录 引脚编号: 引脚文字
                        pin, _, pads = line.partition(':')
                        if pin.strip().isdigit():
                            self.packPins[int(pin)] = pads.strip()
            except OSError:
                pass

            if self.packName and pdfium:
                try:
                    self.packDoc = pdfium.PdfDocument(os.path.join('package', 'package', self.packName + '.pdf'))
                    self.packNums = self.extractPinNums(self.packDoc, max(self.packPins, default=0))
                except Exception:
                    self.packDoc = None

        self.drawPack()

    def onPageChanged(self, page):
        if page == self.win.tabMain.indexOf(self.win.tabPIN):
            QtCore.QTimer.singleShot(0, self.drawPack)     # 等页面显示、视图取得实际尺寸后再绘制

    def onPackWheel(self, event):
        """Ctrl+滚轮：缩放封装图形。返回是否已处理。"""
        if event.modifiers() & QtCore.Qt.ControlModifier and self.packDoc is not None:
            delta = event.angleDelta().y()
            if delta:
                self.packZoom = min(6, max(0.3, self.packZoom * (1.1 if delta > 0 else 1/1.1)))
                self.drawPack()
            return True
        return False

    def onPackClick(self, event):
        """点击引脚编号或编号旁的文字：弹出该引脚的可选功能列表。返回是否已处理。"""
        item = self.packView.itemAt(event.pos())
        if item is not None:
            num = item.data(0)
            if num is not None:
                self.popupPinFuncs(num, event.globalPos())
                return True
        return False

    def drawPack(self):
        """在 packView 中显示当前封装的图形（package/package/<封装名>.pdf）。"""
        sc = self.packView.scene()
        sc.clear()

        w, h = self.packView.viewport().width(), self.packView.viewport().height()
        if w < 10 or h < 10:
            return                                 # 视图尚未显示，等页面切换或尺寸变化时再画

        if self.packDoc is not None:
            self.drawPackPdf(w, h)
            return

        if not self.win.cmbPack.currentText():
            text = f'package/{self.win.cmbMCU.currentText()}/ 目录下没有封装数据文件'
        elif not self.packName:
            text = f'无法读取 {self.win.cmbPack.currentText()}.txt 第一行的封装名称'
        elif pdfium is None:
            text = '显示封装图形需要 pypdfium2 库：pip install pypdfium2'
        else:
            text = f'缺少 package/package/{self.packName}.pdf'

        sc.setSceneRect(0, 0, w, h)
        item = sc.addSimpleText(text)
        item.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        item.setPos((w - item.boundingRect().width()) / 2, (h - item.boundingRect().height()) / 2)

    @staticmethod
    def pinSide(num, npins):
        """引脚所在的边（QFP 编号约定：左→下→右→上，各 P 个）：L/B/R/T。

        引脚数不能被 4 整除时该约定不成立，返回 None 由调用方按位置判断。
        """
        if npins % 4:
            return None
        P = npins // 4
        return 'L' if num <= P else 'B' if num <= 2*P else 'R' if num <= 3*P else 'T'

    @staticmethod
    def extractPinNums(doc, npins):
        """提取封装图形中引脚编号及其位置，返回 [(编号, l, b, r, t), ...]。

        左右边编号水平书写；顶/底边编号旋转 90°（自下而上读）。
        有的图形不标出某一边的编号，按四边对称关系镜像重建补齐。
        """
        tp = doc[0].get_textpage()
        chars = []
        for i in range(tp.count_chars()):
            ch = tp.get_text_range(i, 1)
            l, b, r, t = tp.get_charbox(i)
            if ch.isdigit() and r > l and t > b and max(r-l, t-b) < 3.0:    # 滤掉型号标签等大字
                chars.append([ch, l, b, r, t])

        toks = []                                          # 水平相邻（同基线）或垂直相邻（同列）的数字聚成一个编号
        def adjacent(p, c):                                # 与迭代顺序无关，前后相邻都算
            if abs(c[2] - p[2]) < 0.5:
                return -1 <= c[1] - p[3] <= 3 or -1 <= p[1] - c[3] <= 3
            if abs(c[1] + c[3] - p[1] - p[3]) < 1.4:
                return -1 <= c[2] - p[4] <= 3 or -1 <= p[2] - c[4] <= 3
            return False

        for c in sorted(chars, key=lambda c: (c[1], c[2])):
            for tok in toks:
                if adjacent(tok[-1], c):
                    tok.append(c)
                    break
            else:
                toks.append([c])

        found = {}
        for tok in toks:
            sameRow = max(c[2] for c in tok) - min(c[2] for c in tok) < 0.5
            digits = sorted(tok, key=lambda c: c[1] if sameRow else c[2])  # 竖排数字十位在下、自下而上读
            num = int(''.join(c[0] for c in digits))
            if 1 <= num <= npins and num not in found:
                found[num] = [min(c[1] for c in tok), min(c[2] for c in tok),
                              max(c[3] for c in tok), max(c[4] for c in tok)]

        def interp(num):                                   # 兜底：在前后已知引脚之间线性插值
            lo, hi = num - 1, num + 1
            while lo >= 1 and lo not in found:
                lo -= 1
            while hi <= npins and hi not in found:
                hi += 1
            if lo < 1 or hi > npins:
                return None
            f = (num - lo) / (hi - lo)
            return [found[lo][k] + (found[hi][k] - found[lo][k]) * f for k in range(4)]

        missing = [n for n in range(1, npins + 1) if n not in found]
        if missing and npins % 4 == 0:
            # 同一边上的编号共线、四边等间距，故缺号的引脚可用“隔着芯片中心对称的
            # 那个引脚”镜像得出（直接按相邻引脚连线插值会让整排编号偏斜、过长）
            P = npins // 4
            cx = [ (found[n][0] + found[n][2]) / 2 for n in found
                   if PinConfigPage.pinSide(n, npins) in ('T', 'B') ]
            cy = [ (found[n][1] + found[n][3]) / 2 for n in found
                   if PinConfigPage.pinSide(n, npins) in ('L', 'R') ]
            if cx and cy:
                cx, cy = sum(cx)/len(cx), sum(cy)/len(cy)
                for num in list(missing):
                    side = PinConfigPage.pinSide(num, npins)
                    mir = 3*P + 1 - num if side in ('L', 'R') else 5*P + 1 - num
                    if mir not in found:
                        continue
                    l, b, r, t = found[mir]
                    found[num] = [2*cx - r, b, 2*cx - l, t] if side in ('L', 'R') \
                            else [l, 2*cy - t, r, 2*cy - b]

        for num in missing:                                # 镜像补不出的再用插值兜底
            if num not in found:
                box = interp(num)
                if box:
                    found[num] = box

        return [(num, *found[num]) for num in sorted(found)]

    @staticmethod
    def loadPortFuncs(path):
        """解析 port.h 中各引脚的可选功能，返回 {引脚名: [功能, ...]}。

        形如 #define PORTC_PIN5_I2C1_SCL 的宏 → 引脚 PC5 的功能 I2C1_SCL。
        """
        funcs = {}
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                for m in re.finditer(r'\bPORT([A-Z]+)_PIN(\d+)_([A-Z0-9_]+)', f.read()):
                    pin = 'P%s%s' % (m.group(1), m.group(2))
                    if m.group(3) not in funcs.setdefault(pin, []):
                        funcs[pin].append(m.group(3))
        except OSError:
            pass
        return funcs

    def packPinSide(self, num, box, npins, cx, cy):
        """引脚所在的边（L/T/R/B）：优先按编号约定判断（角上的引脚按坐标判会判错边），
        引脚数不符合该约定时退回看它离芯片中心的横竖距离。"""
        side = self.pinSide(num, npins)
        if side is not None:
            return side
        l, b, r, t = box
        if abs((l + r) / 2 - cx) > abs((b + t) / 2 - cy):
            return 'L' if (l + r) / 2 < cx else 'R'
        return 'B' if (b + t) / 2 < cy else 'T'

    def drawPackPdf(self, w, h):
        """把封装图形 PDF 渲染成位图显示，裁掉页面白边后适配视图，Ctrl+滚轮缩放。

        引脚文字一律排在图形外侧，为此在图形四周留出白边专门放文字（文字都在图内，
        滚动、缩放时不会被裁掉），白边宽度也计入适配缩放的计算。
        """
        from PIL import Image, ImageChops

        sc = self.packView.scene()

        page = self.packDoc[0]
        ph = page.get_size()[1]                    # 页面高度（点）
        probe = page.render(scale=1).to_pil().convert('RGB')
        bbox = ImageChops.difference(probe, Image.new('RGB', probe.size, 'white')).getbbox()
        if not bbox:
            bbox = (0, 0, *probe.size)             # 整页都没有内容时按整页算
        cw, ch = bbox[2]-bbox[0], bbox[3]-bbox[1]  # 实际图形的尺寸（单位：点）

        FONT_PT, GAP_PT = 2.5, 6.0                 # 引脚文字字号系数、文字与图形的间距（点）
        npins = max(self.packPins) if self.packPins else 0
        cx = sum(n[1] + n[3] for n in self.packNums) / (2 * len(self.packNums)) if self.packNums else 0
        cy = sum(n[2] + n[4] for n in self.packNums) / (2 * len(self.packNums)) if self.packNums else 0
        # 每个引脚及其文字排在图形的哪条边（各边文字的多少、长短都不一样）；
        # 留白、缩放只按 txt 中的引脚名计算，选中功能后文字变长也不挪动图形
        pinSides = [(num, box, self.packPinSide(num, box, npins, cx, cy), self.packPins.get(num))
                    for num, *box in self.packNums if self.packPins.get(num)]

        EXTRA_TB = 40                             # 视图上、下再各自多留的空白（像素）

        def fitScale(padL, padR, padT, padB):      # 图形连同四周留白一起放进视图所需的比例
            return min((w - 20 - padL - padR)/cw,
                       (h - 20 - 2*EXTRA_TB - padT - padB)/ch) * self.packZoom

        # 各边要留多宽：从该边最“靠里”的那个编号量到图形边界，再加上文字本身的尺寸。
        # 字号取决于缩放比例、留白又反过来影响缩放，故先估一次再迭代校正
        scale, padL, padR, padT, padB = fitScale(0, 0, 0, 0), 0, 0, 0, 0
        for _ in range(3):
            fnt = QtGui.QFont('Segoe UI')
            fnt.setPointSize(max(5, round(FONT_PT * scale)))     # 点字号，与 Tkinter 版一致
            fm = QtGui.QFontMetrics(fnt)
            gap = GAP_PT * scale
            need = {'L': 0, 'R': 0, 'T': 0, 'B': 0}
            for num, (l, b, r, t), side, text in pinSides:
                if side == 'L':
                    room = fm.horizontalAdvance(text) + gap - (l - bbox[0]) * scale     # 文字排到图形左界还要多少
                elif side == 'R':
                    room = fm.horizontalAdvance(text) + gap - (bbox[2] - r) * scale
                elif side == 'T':
                    room = fm.horizontalAdvance(text) + gap - ((ph - bbox[1]) - t) * scale
                else:
                    room = fm.horizontalAdvance(text) + gap - (b - (ph - bbox[3])) * scale
                need[side] = max(need[side], room)
            padL, padR = max(0, need['L']), max(0, need['R'])
            padT, padB = max(0, need['T']), max(0, need['B'])
            scale = fitScale(padL, padR, padT, padB)

        img = page.render(scale=scale).to_pil().convert('RGB').crop([c*scale for c in bbox])
        # 末次迭代后字号可能再变一点，留 2 像素余量，避免文字压到图边
        padL, padR, padT, padB = round(padL)+2, round(padR)+2, round(padT)+2, round(padB)+2
        if padL or padR or padT or padB:           # 四周补白，给外侧的引脚文字留位置
            padded = Image.new('RGB', (img.width + padL + padR, img.height + padT + padB), 'white')
            padded.paste(img, (padL, padT))
            img = padded

        qimg = QtGui.QImage(img.tobytes('raw', 'RGB'), img.width, img.height,
                            img.width * 3, QtGui.QImage.Format_RGB888).copy()
        pixItem = sc.addPixmap(QtGui.QPixmap.fromImage(qimg))

        ox = (w - img.width)/2 if img.width < w else 10
        oy = (h - img.height)/2 if img.height < h else 10
        pixItem.setPos(ox, oy)
        sc.setSceneRect(0, 0, max(w, ox+img.width), max(h, oy+img.height))

        # 在引脚编号旁标注 txt 中记录的引脚文字：左右边水平排在编号外侧，
        # 顶/底边整体逆时针旋转 90° 竖排在编号外侧（自下而上读，相邻引脚的文字才不会互相重叠）
        if pinSides:
            def toimg(x, y):
                """文本层坐标（y 自页面底边向上）换算为图内像素坐标。"""
                return ox + padL + (x - bbox[0]) * scale, oy + padT + (ph - y - bbox[1]) * scale

            fnt = QtGui.QFont('Segoe UI')
            fnt.setPointSize(max(5, round(FONT_PT * scale)))     # 点字号，与 Tkinter 版一致
            fm = QtGui.QFontMetrics(fnt)
            gap = GAP_PT * scale
            for num, (l, b, r, t), side, name in pinSides:
                x0, y0 = toimg(l, t)               # 编号框左上
                x1, y1 = toimg(r, b)               # 编号框右下

                hit = QtWidgets.QGraphicsRectItem(x0 - 2, y0 - 2, (x1 - x0) + 4, (y1 - y0) + 4)
                hit.setPen(QtGui.QPen(QtCore.Qt.NoPen))
                hit.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
                hit.setData(0, num)                # 引脚编号的点击热区（不可见）
                hit.setZValue(1)
                sc.addItem(hit)

                text = self.packSel.get(num, name)     # 选中功能后显示功能文字（红色）
                item = QtWidgets.QGraphicsSimpleTextItem(text)
                item.setFont(fnt)
                item.setBrush(QtGui.QBrush(QtCore.Qt.red if num in self.packSel else QtCore.Qt.black))
                item.setData(0, num)                   # 点文字同样弹出功能列表
                item.setZValue(1)
                sc.addItem(item)

                tw, th = fm.horizontalAdvance(text), fm.height()
                if side == 'L':                        # 右端贴编号、垂直居中
                    item.setPos(x0 - gap - tw, (y0 + y1) / 2 - th / 2)
                elif side == 'R':                      # 左端贴编号、垂直居中
                    item.setPos(x1 + gap, (y0 + y1) / 2 - th / 2)
                elif side == 'B':
                    # 旋转 -90°（视图坐标下逆时针）后自下而上读：末端贴编号、向下延伸
                    item.setRotation(-90)
                    item.setPos((x0 + x1) / 2 - th / 2, y1 + gap + tw)
                else:
                    # 起端贴编号、向上延伸
                    item.setRotation(-90)
                    item.setPos((x0 + x1) / 2 - th / 2, y0 - gap)

    def popupPinFuncs(self, num, globalPos):
        """在点击处弹出引脚的功能列表（来自 <MCU>_port.h），选中后引脚文字换成该功能。"""
        name = self.packPins.get(num, '')
        funcs = self.portFuncs.get(name)
        if not funcs:
            return

        menu = QtWidgets.QMenu(self.win)
        act = menu.addAction(name)
        act.setEnabled(False)                          # 首项为引脚名，作为标题不可选
        for f in funcs:
            menu.addAction(f, lambda f=f: self.setPinFunc(num, f))
        sel = self.packSel.get(num, 'GPIO')            # 当前功能；未选过时即默认的 GPIO
        if sel in funcs:
            font = menu.actions()[funcs.index(sel) + 1].font()
            font.setBold(True)
            menu.actions()[funcs.index(sel) + 1].setFont(font)
        menu.exec_(globalPos)

    def setPinFunc(self, num, func):
        if func == 'GPIO':                             # GPIO 即默认状态：显示引脚名（黑色）
            self.packSel.pop(num, None)
        else:
            self.packSel[num] = func
        self.drawPack()
