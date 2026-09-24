#! python3
import os
import re
import math
import zipfile
import xml.etree.ElementTree as ET

from PyQt5 import QtCore, QtGui, QtWidgets


VS_NS = '{http://schemas.microsoft.com/office/visio/2012/main}'
DPI = 96.0                                # 场景坐标每英寸像素数，只决定文字/线宽的基准，整体仍会适配视图

# 文档样式表（TextStyle“正常”等）里与显示相关的默认值：形状未给出时按此渲染
DEF_LINE_WEIGHT = 0.01041666666666667     # 英寸（0.75 pt）
DEF_FONT_SIZE = 0.1666666666666667        # 英寸（12 pt）
DEF_TEXT_MARGIN = 0.05555555555555555     # 文字块四周的文字边距（英寸）

PACK_PAD = 8.0                            # 场景矩形相对图形包围盒的外扩量（场景单位）


class VsdxShape:
    """Visio 页面中的一个形状：单元值、各 Section 的行、文字、子形状。

    只取 Cell 的 V 值（公式计算结果），坐标一律为英寸；几何行的 X/Y 在
    Rel* 行里是宽高的比例，其余是形状局部坐标（y 向上）。
    """

    def __init__(self, el):
        self.cells = {c.get('N'): c.get('V') for c in el.findall(VS_NS + 'Cell')}
        self.sections = []                                    # [{'name', 'cells', 'rows': [(行类型, {单元: 值}), ...]}, ...]
        for sec in el.findall(VS_NS + 'Section'):
            self.sections.append({
                'name': sec.get('N'),
                'cells': {c.get('N'): c.get('V') for c in sec.findall(VS_NS + 'Cell')},
                'rows': [(row.get('T'), {c.get('N'): c.get('V') for c in row.findall(VS_NS + 'Cell')})
                         for row in sec.findall(VS_NS + 'Row')]})
        text = el.find(VS_NS + 'Text')
        self.text = ''.join(text.itertext()).strip() if text is not None else ''
        self.children = [VsdxShape(s) for s in el.findall(VS_NS + 'Shapes/' + VS_NS + 'Shape')]

    def cell(self, name, default=None):
        return self.cells.get(name, default)

    def rowCell(self, section, cell, default=None):
        """Section 行里的单元值（如 Character 的 Size、Paragraph 的 HorzAlign）。"""
        for sec in self.sections:
            if sec['name'] == section:
                for _, cells in sec['rows']:
                    if cell in cells:
                        return cells[cell]
        return default


class VsdxPage:
    """vsdx 封装图形的第一页。Visio 坐标系：英寸、原点在页面左下、y 轴向上。"""

    def __init__(self, path):
        zipf = zipfile.ZipFile(path)

        # 第一页的内容文件记录在 pages.xml 的关系里（Target 形如 page1.xml）
        rels = ET.fromstring(zipf.read('visio/pages/_rels/pages.xml.rels'))
        targets = [rel.get('Target') for rel in rels if rel.get('Target')]
        pagename = targets[0] if targets else 'page1.xml'

        self.height = 11.0                                     # 页面高度，页面坐标换算场景坐标用
        for c in ET.fromstring(zipf.read('visio/pages/pages.xml')).iter(VS_NS + 'Cell'):
            if c.get('N') == 'PageHeight':
                self.height = float(c.get('V'))

        shapes = ET.fromstring(zipf.read('visio/pages/' + pagename)).find(VS_NS + 'Shapes')
        self.shapes = [VsdxShape(s) for s in shapes] if shapes is not None else []


def shapeXform(shape):
    """形状自身坐标 → 父坐标的变换（英寸，y 向上）：先翻转、绕 LocPin 旋转、再平移到 Pin。"""
    w = float(shape.cell('Width', 0) or 0)
    h = float(shape.cell('Height', 0) or 0)
    t = QtGui.QTransform()
    t.translate(float(shape.cell('PinX', 0) or 0), float(shape.cell('PinY', 0) or 0))
    t.rotateRadians(float(shape.cell('Angle', 0) or 0))
    t.translate(-float(shape.cell('LocPinX', w / 2) or 0), -float(shape.cell('LocPinY', h / 2) or 0))
    if shape.cell('FlipX', '0') != '0':
        t.translate(w, 0)
        t.scale(-1, 1)
    if shape.cell('FlipY', '0') != '0':
        t.translate(0, h)
        t.scale(1, -1)
    return t


def geometryPaths(shape):
    """形状的各 Geometry 段 → [(QPainterPath, 段单元), ...]，路径为形状局部坐标（英寸）。

    只处理 MoveTo/LineTo/RelMoveTo/RelLineTo/Ellipse（现有图形只用到这些），
    遇到其它行类型就停止该段（保留已画出的部分）。
    """
    w = float(shape.cell('Width', 0) or 0)
    h = float(shape.cell('Height', 0) or 0)
    paths = []
    for sec in shape.sections:
        if sec['name'] != 'Geometry':
            continue
        path = QtGui.QPainterPath()
        for rowtype, cells in sec['rows']:
            try:
                if rowtype in ('MoveTo', 'RelMoveTo'):
                    x, y = float(cells['X']), float(cells['Y'])
                    if rowtype.startswith('Rel'):
                        x, y = x * w, y * h
                    path.moveTo(x, y)
                elif rowtype in ('LineTo', 'RelLineTo'):
                    x, y = float(cells['X']), float(cells['Y'])
                    if rowtype.startswith('Rel'):
                        x, y = x * w, y * h
                    path.lineTo(x, y)
                elif rowtype == 'Ellipse':
                    cx, cy = float(cells['X']), float(cells['Y'])
                    rx = abs(float(cells['A']) - cx)
                    ry = abs(float(cells['D']) - cy)
                    path.addEllipse(QtCore.QPointF(cx, cy), rx, ry)
                else:
                    break
            except (KeyError, ValueError):
                break
        if path.elementCount():
            paths.append((path, sec['cells']))
    return paths


def parseColor(v):
    """LineColor/FillForegnd 的值（#rrggbb 或调色板号，0=黑）→ QColor。"""
    if v and v.startswith('#'):
        return QtGui.QColor(v)
    return QtGui.QColor('black' if v in (None, '0') else v)


def drawVsdx(scene, page, packPins, packSel):
    """把 vsdx 的形状画进场景：几何画成矢量路径，编号等文字按 Visio 的文字块规则摆放。

    引脚文字（txt 记录的引脚名 / 选中的功能名，红色）由这里计算位置：编号框分布在芯片
    四周，按编号框中心相对全部编号框中心的方位判断所在的边，文字排在编号外侧——左右
    边水平书写、顶/底边竖排（自下而上读），起点贴着编号框、向外延伸。编号框、编号、
    文字的图形项都带上引脚号（setData(0)），供点击弹出功能列表。

    返回（适配包围盒, 芯片中心）：包围盒中引脚文字按当前显示的文字（选中功能后即
    功能文字）计算，文字变长时包围盒随之变大，drawPack 便会缩小缩放让文字完全显示；
    芯片中心为全部编号框的中心，与引脚文字无关，用作画布的居中锚点。
    """
    sceneT = QtGui.QTransform()                               # 页面坐标（英寸，y 向上）→ 场景坐标（y 向下）
    sceneT.translate(0, page.height * DPI)
    sceneT.scale(DPI, -DPI)

    def addText(shape, xform, baseAngle, text, color, num):
        c = shape.cells
        w = float(c.get('Width', 0) or 0)
        h = float(c.get('Height', 0) or 0)
        # 文字块（缺省为整个形状框）及其中的文字边距
        bw_ = float(c.get('TxtWidth', w) or 0)
        bh_ = float(c.get('TxtHeight', h) or 0)
        tpx = float(c.get('TxtPinX', w / 2) or 0)
        tpy = float(c.get('TxtPinY', h / 2) or 0)
        tlx = float(c.get('TxtLocPinX', bw_ / 2) or 0)
        tly = float(c.get('TxtLocPinY', bh_ / 2) or 0)
        bx, by = tpx - tlx, tpy - tly                         # 文字块左下角（形状坐标）
        m = DEF_TEXT_MARGIN
        bw, bh = bw_ - 2 * m, bh_ - 2 * m                     # 扣掉边距后的文字区域

        fnt = QtGui.QFont('Segoe UI')
        fnt.setPixelSize(max(4, round(float(shape.rowCell('Character', 'Size', DEF_FONT_SIZE) or 0) * DPI)))
        fm = QtGui.QFontMetrics(fnt)
        lines = text.split('\n')
        tw = max(fm.horizontalAdvance(line) for line in lines) / DPI       # 换回英寸参与摆放计算
        th = fm.height() * len(lines) / DPI

        ha = int(float(shape.rowCell('Paragraph', 'HorzAlign', '1') or 0))    # 0左 1中 2右
        va = int(float(c.get('VerticalAlign', '1') or 0))                     # 0上 1中 2下（y 向上）
        ox = (0.0, (bw - tw) / 2, bw - tw)[ha]
        oy = (bh - th, (bh - th) / 2, 0.0)[va]
        # 文字左上角（形状坐标），先绕 TxtPin 旋转（TxtAngle 及竖排文字的 -90°），再随形状变换到页面
        lx, ly = bx + m + ox, by + m + oy + th
        angT = float(c.get('TxtAngle', 0) or 0)
        # 竖排文字（TextDirection=1）的文字块相对形状再转 -90°：Visio 实际渲染的朝向即
        # Angle + TxtAngle - 90°（与 Visio 导出 PDF 中各引脚的字符排布逐项核对得到）
        if c.get('TextDirection', '0') == '1':
            angT -= math.pi / 2
        ax = tpx + (lx - tpx) * math.cos(angT) - (ly - tpy) * math.sin(angT)
        ay = tpy + (lx - tpx) * math.sin(angT) + (ly - tpy) * math.cos(angT)
        pos = xform.map(QtCore.QPointF(ax, ay))
        theta = baseAngle + angT                              # 文字最终旋转角（弧度，页面坐标逆时针）

        item = QtWidgets.QGraphicsSimpleTextItem(text)
        item.setFont(fnt)
        item.setBrush(QtGui.QBrush(color))
        item.setPos(pos.x() * DPI, (page.height - pos.y()) * DPI)
        item.setRotation(-math.degrees(theta))                # Qt 的旋转以顺时针为正
        if num is not None:
            item.setData(0, num)                              # 点击文字弹出该引脚的功能列表
        item.setZValue(1)
        scene.addItem(item)

    fit = [QtCore.QRectF()]                                    # 适配包围盒（用列表以便闭包内修改）

    def walk(shape, xform, baseAngle):
        xf = shapeXform(shape) * xform                       # Qt 的 a*b 是先 a 后 b：子变换在前、父变换在后
        angle = baseAngle + float(shape.cell('Angle', 0) or 0)

        num = int(shape.text) if shape.text.isdigit() else None
        for path, seccells in geometryPaths(shape):
            pen = brush = None
            if seccells.get('NoLine') != '1' and shape.cell('LinePattern', '1') != '0':
                pen = QtGui.QPen(parseColor(shape.cell('LineColor')),
                                 max(1.0, float(shape.cell('LineWeight', DEF_LINE_WEIGHT) or 0) * DPI))
            if seccells.get('NoFill') != '1' and shape.cell('FillPattern', '1') != '0':
                brush = QtGui.QBrush(parseColor(shape.cell('FillForegnd')))
            if pen is not None or brush is not None:
                item = scene.addPath(sceneT.map(xf.map(path)),
                                     pen or QtGui.QPen(QtCore.Qt.NoPen),
                                     brush or QtGui.QBrush(QtCore.Qt.NoBrush))
                if num is not None:
                    item.setData(0, num)                      # 引脚编号的小框也可点击
                item.setZValue(0)
                fit[0] = fit[0].united(item.boundingRect())

        if shape.text and not (shape.text.startswith('Pin_') and shape.text[4:].isdigit()):
            addText(shape, xf, angle, shape.text, QtCore.Qt.black, num)

        if num is not None:                                   # 编号框在页面里的位置，供计算引脚文字位置
            w = float(shape.cell('Width', 0) or 0)
            h = float(shape.cell('Height', 0) or 0)
            xs, ys = [], []
            for x, y in ((0, 0), (w, 0), (0, h), (w, h)):
                p = xf.map(QtCore.QPointF(x, y))
                xs.append(p.x() * DPI)
                ys.append((page.height - p.y()) * DPI)
            digits.append((num, min(xs), min(ys), max(xs), max(ys), shape))
            fit[0] = fit[0].united(QtCore.QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))

        for child in shape.children:
            walk(child, xf, angle)

    digits = []                                               # [(编号, 左, 上, 右, 下, 形状), ...]（场景坐标）
    for shape in page.shapes:
        walk(shape, QtGui.QTransform(), 0.0)

    GAP = 6.0                                                 # 编号框与文字的间距（像素）
    cx = sum(d[1] + d[3] for d in digits) / (2 * len(digits)) if digits else 0
    cy = sum(d[2] + d[4] for d in digits) / (2 * len(digits)) if digits else 0
    for num, x0, y0, x1, y1, shape in digits:
        name = packPins.get(num)
        if not name:
            continue
        text = packSel.get(num) or name
        fnt = QtGui.QFont('Segoe UI')
        fnt.setPixelSize(max(4, round(float(shape.rowCell('Character', 'Size', DEF_FONT_SIZE) or 0) * DPI)))
        fm = QtGui.QFontMetrics(fnt)
        tw, th = fm.horizontalAdvance(text), fm.height()

        item = QtWidgets.QGraphicsSimpleTextItem(text)
        item.setFont(fnt)
        item.setBrush(QtGui.QBrush(QtCore.Qt.red if num in packSel else QtCore.Qt.black))
        item.setData(0, num)                                  # 点文字弹出该引脚的功能列表
        item.setZValue(1)
        scene.addItem(item)

        if abs((x0 + x1) / 2 - cx) > abs((y0 + y1) / 2 - cy):  # 离中心横向更远：左右边
            if (x0 + x1) / 2 < cx:                            # 左边：右端贴编号、垂直居中
                item.setPos(x0 - GAP - tw, (y0 + y1) / 2 - th / 2)
                fit[0] = fit[0].united(QtCore.QRectF(x0 - GAP - tw, (y0 + y1) / 2 - th / 2, tw, th))
            else:                                             # 右边：左端贴编号、垂直居中
                item.setPos(x1 + GAP, (y0 + y1) / 2 - th / 2)
                fit[0] = fit[0].united(QtCore.QRectF(x1 + GAP, (y0 + y1) / 2 - th / 2, tw, th))
        else:                                                 # 顶/底边：竖排，自下而上读
            item.setRotation(-90)
            if (y0 + y1) / 2 < cy:                            # 顶边：末端贴编号、向上延伸
                item.setPos((x0 + x1) / 2 - th / 2, y0 - GAP)
                fit[0] = fit[0].united(QtCore.QRectF((x0 + x1) / 2 - th / 2, y0 - GAP - tw, th, tw))
            else:                                             # 底边：起端贴编号、向下延伸
                item.setPos((x0 + x1) / 2 - th / 2, y1 + GAP + tw)
                fit[0] = fit[0].united(QtCore.QRectF((x0 + x1) / 2 - th / 2, y1 + GAP, th, tw))

    return fit[0], QtCore.QPointF(cx, cy) if digits else fit[0].center()


class PackView(QtWidgets.QGraphicsView):
    """封装图形视图（对应 Tkinter 版的 packView 画布），事件交给 PinConfigPage 处理。"""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setBackgroundBrush(QtCore.Qt.white)
        self.setAlignment(QtCore.Qt.AlignCenter)             # 图形比视图小时居中显示
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

        self.packPage = None                                # 当前封装的图形（vsdx 第一页）
        self.packZoom = 1.0                                 # 封装图形的缩放倍数
        self.packName = ''                                  # 从 txt 第一行读出的封装名称
        self.packPins = {}                                  # txt 记录的 {引脚号: 引脚文字}
        self.portFuncs = {}                                 # <MCU>_port.h 解析出的 {引脚名: [功能, ...]}
        self.packSel = {}                                   # {引脚号: 选中的功能文字}（选中后红色显示）

        self.packView = PackView(self)
        layout = QtWidgets.QVBoxLayout(win.viewPIN)
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

        self.packPage = None
        self.packZoom = 1.0
        self.packName = ''
        self.packPins = {}
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

            if self.packName:
                try:
                    self.packPage = VsdxPage(os.path.join('package', 'package', self.packName + '.vsdx'))
                except Exception:
                    self.packPage = None

        self.drawPack()

    def onPageChanged(self, page):
        if page == 0:
            QtCore.QTimer.singleShot(0, self.drawPack)     # 等页面显示、视图取得实际尺寸后再绘制

    def onPackWheel(self, event):
        """Ctrl+滚轮：缩放封装图形（以视口中心为不动点）。返回是否已处理。"""
        if event.modifiers() & QtCore.Qt.ControlModifier and self.packPage is not None:
            delta = event.angleDelta().y()
            if delta:
                newZoom = min(6, max(0.3, self.packZoom * (1.1 if delta > 0 else 1 / 1.1)))
                anchor = self.packView.mapToScene(self.packView.viewport().rect().center())
                self.packView.scale(newZoom / self.packZoom, newZoom / self.packZoom)
                self.packView.centerOn(anchor)
                self.packZoom = newZoom
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
        """在 packView 中显示当前封装的图形（package/package/<封装名>.vsdx）。"""
        sc = self.packView.scene()
        sc.clear()

        w, h = self.packView.viewport().width(), self.packView.viewport().height()
        if w < 10 or h < 10:
            return                                 # 视图尚未显示，等页面切换或尺寸变化时再画

        if self.packPage is not None:
            fit, center = drawVsdx(sc, self.packPage, self.packPins, self.packSel)
            # 场景矩形、缩放都以芯片中心对称、视图以芯片中心居中：引脚文字在某一边
            # 变长但窗口还放得下时，缩放比例不变、图形位置不动；长到放不下时按对称
            # 包围盒缩小缩放（芯片中心不动），让文字完全显示
            halfW = max(center.x() - fit.left(), fit.right() - center.x())
            halfH = max(center.y() - fit.top(), fit.bottom() - center.y())
            sc.setSceneRect(QtCore.QRectF(center.x() - halfW, center.y() - halfH, 2 * halfW, 2 * halfH)
                            .adjusted(-PACK_PAD, -PACK_PAD, PACK_PAD, PACK_PAD))
            view = self.packView
            view.resetTransform()
            vw, vh = view.viewport().width(), view.viewport().height()
            if vw > 0 and vh > 0 and halfW > 0 and halfH > 0:
                # 缩放要按含留白的场景尺寸算：留白若不计入，s>1 时会被放大成 PACK_PAD*s
                # 像素，整块场景反而比视口高/宽，QGraphicsView 就冒出滚动条（窗口越大越明显）
                boxW, boxH = 2 * (halfW + PACK_PAD), 2 * (halfH + PACK_PAD)
                s = min((vw - 2) / boxW, (vh - 2) / boxH) * self.packZoom   # 留 2px 余量，避免正好相等
                view.setTransform(QtGui.QTransform().scale(s, s))
                view.centerOn(center)
            return

        if not self.win.cmbPack.currentText():
            text = f'package/{self.win.cmbMCU.currentText()}/ 目录下没有封装数据文件'
        elif not self.packName:
            text = f'无法读取 {self.win.cmbPack.currentText()}.txt 第一行的封装名称'
        else:
            text = f'缺少 package/package/{self.packName}.vsdx'

        self.packView.resetTransform()                     # 别延用上个封装的缩放，否则提示文字被放大、滚动条常驻
        sc.setSceneRect(0, 0, w, h)
        item = sc.addSimpleText(text)
        item.setBrush(QtGui.QBrush(QtCore.Qt.gray))
        item.setPos((w - item.boundingRect().width()) / 2, (h - item.boundingRect().height()) / 2)

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
