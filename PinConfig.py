#! python3
import os
import re
import math
import zipfile
import xml.etree.ElementTree as ET

from PyQt5 import QtCore, QtGui, QtWidgets


VS_NS = '{http://schemas.microsoft.com/office/visio/2012/main}'


class VsdxShape:
    def __init__(self, el):
        self.cells = {cell.get('N'): cell.get('V') for cell in el.findall(VS_NS + 'Cell')}  # name: value

        self.sections = []
        for sect in el.findall(VS_NS + 'Section'):
            self.sections.append({
                'name': sect.get('N'),
                'cells': {cell.get('N'): cell.get('V') for cell in sect.findall(VS_NS + 'Cell')},
                'rows' : [ ]
            })

            for row in sect.findall(VS_NS + 'Row'):
                self.sections[-1]['rows'].append((row.get('T'), {cell.get('N'): cell.get('V') for cell in row.findall(VS_NS + 'Cell')}))

        text = el.find(VS_NS + 'Text')
        self.text = ''.join(text.itertext()).strip() if text is not None else ''

        self.children = [VsdxShape(shape) for shape in el.findall(VS_NS + 'Shapes/' + VS_NS + 'Shape')]

    def cell(self, name, default=None):
        return self.cells.get(name, default)

    def rowCell(self, section, cell, default=None):
        for sect in self.sections:
            if sect['name'] == section:
                for rowType, cells in sect['rows']:
                    if cell in cells:
                        return cells[cell]
        return default

    def color(self, name):
        ''' name: cell name, e.g. LineColor, FillForegnd. '''
        val = self.cell(name)
        if val and val.startswith('#'):     # #rrggbb
            return QtGui.QColor(val)

        return QtGui.QColor('black' if val in (None, '0') else val)     # 调色板号，0=黑

    def geometryPaths(self):
        ''' Shape 的各个 Geometry Section → [(QPainterPath, sect['cells']), ...]
            只处理 MoveTo/LineTo/RelMoveTo/RelLineTo/Ellipse（现有图形只用到这些）。
        '''
        w = float(self.cell('Width', 0) or 0)   # or 0 用于应对“存在但值是空串”的情况
        h = float(self.cell('Height', 0) or 0)

        paths = []
        for sect in self.sections:
            if sect['name'] != 'Geometry':
                continue

            path = QtGui.QPainterPath()
            for rowtype, cells in sect['rows']:
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
                paths.append((path, sect['cells']))

        return paths

    def transform(self):
        ''' 将一个 Visio Shape 从自身局部坐标变换到父坐标（页或父形状，单位英寸，y 向上）

            Visio 中每个形状有三组坐标：局部坐标系原点在包围盒左下角、范围 (0,0)~(w,h)，Geometry Row 的 X/Y 用的是它；
            LocPinX/LocPinY 是针脚（锚点）在局部坐标里的位置，一般是 Width*0.5, Height*0.5；PinX/PinY 是同一个针脚在父坐标中的位置。

            QTransform 对点的作用顺序与书写顺序相反，先写的后作用（最外层）；所以下面的代码完成的变换依次是：
                形状在自己的局部坐标空间里执行 FlipX/FlipY 镜像
                将局部坐标系原点移到锚点（LocPinX, LocPinY），因为后面的旋转是绕锚点执行的
                绕锚点逆时针旋转 Angle 弧度
                把旋转后形状的锚点（通常是形状中心点）平移到父坐标的 (PinX, PinY)
        '''
        w = float(self.cell('Width', 0) or 0)
        h = float(self.cell('Height', 0) or 0)

        t = QtGui.QTransform()
        t.translate(float(self.cell('PinX', 0) or 0), float(self.cell('PinY', 0) or 0))
        t.rotateRadians(float(self.cell('Angle', 0) or 0))
        t.translate(-float(self.cell('LocPinX', w / 2) or 0), -float(self.cell('LocPinY', h / 2) or 0))
        if self.cell('FlipX', '0') != '0':
            t.translate(w, 0)
            t.scale(-1, 1)
        if self.cell('FlipY', '0') != '0':
            t.translate(0, h)
            t.scale(1, -1)

        return t


class VsdxPage:
    def __init__(self, path):
        zipf = zipfile.ZipFile(path)

        self.height = 11.0
        for cell in ET.fromstring(zipf.read('visio/pages/pages.xml')).iter(VS_NS + 'Cell'):
            if cell.get('N') == 'PageHeight':
                self.height = float(cell.get('V'))

        shapes = ET.fromstring(zipf.read('visio/pages/page1.xml')).find(VS_NS + 'Shapes')
        self.shapes = [VsdxShape(shape) for shape in shapes] if shapes is not None else []

    def draw(self, scene, packPins, pinFunct):
        ''' 将 Visio page 中的 shapes 画进场景：几何画成矢量路径，编号等文字按 Visio 的文字块规则摆放 '''
        DPI = 96.0      # 场景坐标每英寸像素数，只决定文字/线宽的基准，整体仍会适配视图
        GAP = 6.0       # 编号框与文字的间距（像素）

        # 文档样式表里与显示相关的默认值：形状未给出时按此渲染
        LINE_WEIGHT = 0.01041666666666667   # 英寸（0.75 pt）
        FONT_SIZE   = 0.1666666666666667    # 英寸（12 pt）
        TEXT_MARGIN = 0.05555555555555555   # 文字块四周的文字边距（英寸）

        sceneT = QtGui.QTransform()         # 页面坐标（英寸，y 向上）→ 场景坐标（y 向下）
        sceneT.translate(0, self.height * DPI)
        sceneT.scale(DPI, -DPI)

        def addText(shape, xform, baseAngle, text, color, pnum):
            w = float(shape.cell('Width', 0) or 0)
            h = float(shape.cell('Height', 0) or 0)

            # 文字块（缺省为整个形状框）及其中的文字边距
            bw  = float(shape.cell('TxtWidth', w) or 0)
            bh  = float(shape.cell('TxtHeight', h) or 0)
            tpx = float(shape.cell('TxtPinX', w / 2) or 0)
            tpy = float(shape.cell('TxtPinY', h / 2) or 0)
            tlx = float(shape.cell('TxtLocPinX', bw / 2) or 0)
            tly = float(shape.cell('TxtLocPinY', bh / 2) or 0)
            bx, by = tpx - tlx, tpy - tly                           # 文字块左下角（形状坐标）
            bw, bh = bw - 2 * TEXT_MARGIN, bh - 2 * TEXT_MARGIN     # 扣掉边距后的文字区域

            font = QtGui.QFont('Segoe UI')
            font.setPixelSize(max(4, round(float(shape.rowCell('Character', 'Size', FONT_SIZE) or 0) * DPI)))
            fm = QtGui.QFontMetrics(font)   # 用于获取字体度量信息的工具类，核心作用是在绘制文本前精确计算文字占用的屏幕空间
            tw = max(fm.horizontalAdvance(line) for line in text.split('\n')) / DPI
            th = fm.height() * len(text.split('\n')) / DPI

            ha = int(float(shape.rowCell('Paragraph', 'HorzAlign', '1') or 0))  # 水平对齐：0 左, 1 中, 2 右
            va = int(float(shape.cell('VerticalAlign', '1') or 0))              # 竖直对齐：0 上, 1 中, 2 下
            ox = (0.0, (bw - tw) / 2, bw - tw)[ha]
            oy = (bh - th, (bh - th) / 2, 0.0)[va]
            lx, ly = bx + TEXT_MARGIN + ox, by + TEXT_MARGIN + oy + th          # 文字左上角坐标

            angle = float(shape.cell('TxtAngle', 0) or 0)
            if shape.cell('TextDirection', '0') == '1':     # 竖排文字的文字块相对形状再转 -90°
                angle -= math.pi / 2
            ax = tpx + (lx - tpx) * math.cos(angle) - (ly - tpy) * math.sin(angle)
            ay = tpy + (lx - tpx) * math.sin(angle) + (ly - tpy) * math.cos(angle)
            pos = xform.map(QtCore.QPointF(ax, ay))

            item = QtWidgets.QGraphicsSimpleTextItem(text)
            item.setFont(font)
            item.setBrush(QtGui.QBrush(color))
            item.setPos(pos.x() * DPI, (self.height - pos.y()) * DPI)
            item.setRotation(-math.degrees(baseAngle + angle))
            if pnum is not None:
                item.setData(0, pnum)   # 点击文字弹出该引脚的功能列表
            item.setZValue(1)           # z 值越大显示越靠前（越在上层）
            scene.addItem(item)

        ''' 从空矩形开始，每画一个元素（几何路径、引脚序号框）就用 united() 并入其包围盒，
            最终返回的是全部绘制内容在场景坐标下的总包围盒。用于计算场景矩形和"整体适配视图"的缩放。
        '''
        bRect = [QtCore.QRectF()]       # boundingRect, 用列表以便闭包内修改

        def walk(shape, xform, baseAngle):
            xform = shape.transform() * xform   # Qt 的 a*b 是先 a 后 b：子变换在前、父变换在后
            angle = baseAngle + float(shape.cell('Angle', 0) or 0)

            pnum = int(shape.text) if shape.text.isdigit() else None

            for path, sect_cells in shape.geometryPaths():
                pen = brush = None
                if sect_cells.get('NoLine') != '1' and shape.cell('LinePattern', '1') != '0':
                    pen = QtGui.QPen(shape.color('LineColor'), max(1.0, float(shape.cell('LineWeight', LINE_WEIGHT) or 0) * DPI))
                if sect_cells.get('NoFill') != '1' and shape.cell('FillPattern', '1') != '0':
                    brush = QtGui.QBrush(shape.color('FillForegnd'))
                if pen is not None or brush is not None:
                    item = scene.addPath(sceneT.map(xform.map(path)), pen or QtGui.QPen(QtCore.Qt.NoPen), brush or QtGui.QBrush(QtCore.Qt.NoBrush))
                    if pnum is not None:
                        item.setData(0, pnum)   # 引脚序号的小框也可点击
                    item.setZValue(0)
                    bRect[0] = bRect[0].united(item.boundingRect())

            if shape.text:
                addText(shape, xform, angle, shape.text, QtCore.Qt.black, pnum)

            if pnum is not None:                # 引脚序号框在页面里的位置，供计算引脚文字位置
                w = float(shape.cell('Width', 0) or 0)
                h = float(shape.cell('Height', 0) or 0)
                xs, ys = [], []
                for x, y in ((0, 0), (w, 0), (0, h), (w, h)):
                    xp = xform.map(QtCore.QPointF(x, y))
                    xs.append(xp.x() * DPI)
                    ys.append((self.height - xp.y()) * DPI)
                pads.append((pnum, min(xs), min(ys), max(xs), max(ys), shape))
                bRect[0] = bRect[0].united(QtCore.QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))

            for child in shape.children:
                walk(child, xform, angle)

        pads = []   # 即封装矩形四周表示引脚的小矩形，[(引脚序号, 左, 上, 右, 下, 形状), ...]（场景坐标）
        for shape in self.shapes:
            walk(shape, QtGui.QTransform(), 0.0)

        cx = sum(pad[1] + pad[3] for pad in pads) / (2 * len(pads)) if pads else 0      # centre x
        cy = sum(pad[2] + pad[4] for pad in pads) / (2 * len(pads)) if pads else 0
        for pnum, x0, y0, x1, y1, shape in pads:
            pname = packPins.get(pnum)
            if not pname:
                continue

            text = pinFunct.get(pnum) or pname

            font = QtGui.QFont('Segoe UI')
            font.setPixelSize(max(4, round(float(shape.rowCell('Character', 'Size', FONT_SIZE) or 0) * DPI)))
            
            item = QtWidgets.QGraphicsSimpleTextItem(text)
            item.setFont(font)
            item.setBrush(QtGui.QBrush(QtCore.Qt.red if pnum in pinFunct else QtCore.Qt.black))
            item.setData(0, pnum)   # 点文字弹出该引脚的功能列表
            item.setZValue(1)
            scene.addItem(item)

            fm = QtGui.QFontMetrics(font)
            tw, th = fm.horizontalAdvance(text), fm.height()

            if abs((x0 + x1) / 2 - cx) > abs((y0 + y1) / 2 - cy):   # 离中心横向更远：左右边
                if (x0 + x1) / 2 < cx:      # 左边：右端贴编号、垂直居中
                    item.setPos(x0 - GAP - tw, (y0 + y1) / 2 - th / 2)
                    bRect[0] = bRect[0].united(QtCore.QRectF(x0 - GAP - tw, (y0 + y1) / 2 - th / 2, tw, th))
                else:                       # 右边：左端贴编号、垂直居中
                    item.setPos(x1 + GAP, (y0 + y1) / 2 - th / 2)
                    bRect[0] = bRect[0].united(QtCore.QRectF(x1 + GAP, (y0 + y1) / 2 - th / 2, tw, th))
            else:                                                   # 顶/底边：竖排，自下而上读
                item.setRotation(-90)
                if (y0 + y1) / 2 < cy:      # 顶边：末端贴编号、向上延伸
                    item.setPos((x0 + x1) / 2 - th / 2, y0 - GAP)
                    bRect[0] = bRect[0].united(QtCore.QRectF((x0 + x1) / 2 - th / 2, y0 - GAP - tw, th, tw))
                else:                       # 底边：起端贴编号、向下延伸
                    item.setPos((x0 + x1) / 2 - th / 2, y1 + GAP + tw)
                    bRect[0] = bRect[0].united(QtCore.QRectF((x0 + x1) / 2 - th / 2, y1 + GAP, th, tw))

        return bRect[0], QtCore.QPointF(cx, cy) if pads else bRect[0].center()


class VsdxView(QtWidgets.QGraphicsView):
    ''' 用于显示 VsdxPage 的画布视图 '''
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner

        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setBackgroundBrush(QtCore.Qt.white)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        self._lastSize = None

    def wheelEvent(self, event):
        if not self.owner.onPackWheel(event):
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if not self.owner.onPackClick(event):
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.viewport().size()
        if (size.width(), size.height()) != self._lastSize:     # 尺寸没变就不重画，避免滚动条出现/消失引起循环
            keepView = self._lastSize is not None               # 首次显示前没有可保持的视口位置，仍居中
            self._lastSize = (size.width(), size.height())
            self.owner.drawPack(keepView)


class PinConfigPage(QtCore.QObject):
    def __init__(self, win):            # win 为主窗口（SWMTool）
        super().__init__(win)
        self.win = win

        self.vsdxPage = None            # visio vsdx 文件页
        self.packName = ''              # 封装名称，如 LQFP-64
        self.packPins = {}              # SWM34SRET6.txt 记录的 {引脚序号: 引脚名称}，如 45: PM0
        self.pinFuncs = {}              # SWM341_port.h 解析出的 {引脚名称: [引脚功能, ...]}，如 PM0: ['GPIO', 'UART0_RX', 'PWM_BRK1', 'CAN1_TX']
        self.pinFunct = {}              # {引脚序号: 选中的非 GPIO 引脚功能}，非 GPIO 功能以红色显示

        self.vsdxView = VsdxView(self)  # 用来显示 self.vsdxPage 的画布视图
        layout = QtWidgets.QVBoxLayout(win.viewPIN)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.vsdxView)

        self.viewZoom = 1.0             # self.vsdxView 的缩放倍数

        self._drawing = False

    def onPackChanged(self, pack):
        self.vsdxPage = None
        self.viewZoom = 1.0
        self.packName = ''
        self.packPins = {}
        self.pinFunct = {}

        if pack:
            try:
                with open(os.path.join('package', self.win.cmbMCU.currentText(), pack + '.txt')) as txtf:
                    self.packName = txtf.readline().strip()     # 第一行记录 封装名称
                    for line in txtf:                           # 其余行记录 引脚序号: 引脚名称
                        pnum, _, pname = line.partition(':')
                        if pnum.strip().isdigit():
                            self.packPins[int(pnum)] = pname.strip()
            except OSError:
                pass

        if self.packName:
            try:
                self.vsdxPage = VsdxPage(os.path.join('package', 'package', f'{self.packName}.vsdx'))
            except Exception:
                self.vsdxPage = None

        self.drawPack()

    def onPackWheel(self, event):
        ''' Ctrl+滚轮：缩放封装图形（以视口中心为不动点） '''
        if event.modifiers() & QtCore.Qt.ControlModifier and self.vsdxPage is not None:
            delta = event.angleDelta().y()      # 滚轮转动的角度
            if delta:
                newZoom = min(6, max(0.3, self.viewZoom * (1.1 if delta > 0 else 1 / 1.1)))
                anchor = self.vsdxView.mapToScene(self.vsdxView.viewport().rect().center())
                self.vsdxView.scale(newZoom / self.viewZoom, newZoom / self.viewZoom)
                self.vsdxView.centerOn(anchor)
                self.viewZoom = newZoom
            return True
        return False

    def onPackClick(self, event):
        ''' 点击引脚或引脚旁的文字：弹出该引脚的可选功能列表 '''
        item = self.vsdxView.itemAt(event.pos())
        if item is not None:
            pnum = item.data(0)
            if pnum is not None:
                pname = self.packPins.get(pnum, '')
                funcs = self.pinFuncs.get(pname)
                if funcs:
                    menu = QtWidgets.QMenu(self.win)
                    menu.addAction(pname).setEnabled(False)     # 首项为引脚名，作为标题不可选
                    for func in funcs:
                        menu.addAction(func, lambda func=func: self.setPinFunc(pnum, func))
                    funct = self.pinFunct.get(pnum, 'GPIO')     # 当前功能；未选其他功能时默认为 GPIO
                    if funct in funcs:
                        font = menu.actions()[funcs.index(funct) + 1].font()
                        font.setBold(True)
                        menu.actions()[funcs.index(funct) + 1].setFont(font)
                    menu.exec_(event.globalPos())
                return True
        return False

    def setPinFunc(self, pnum, func):       # 弹出列表中点击引脚功能条目触发的执行代码
        if func == 'GPIO':
            self.pinFunct.pop(pnum, None)   # GPIO 是默认功能，不在 {引脚序号: 选中的非 GPIO 引脚功能} 表格中记录
        else:
            self.pinFunct[pnum] = func

        self.drawPack(keepView=True)

    def drawPack(self, keepView=False):
        ''' 在 self.vsdxView 中绘制 self.vsdxPage。
            keepView = True：放大后拖滚动条查看顶部/底部引脚、点击引脚选择功能而重画时，视图不再跳回芯片中心。
        '''
        PACK_PAD = 8.0          # 场景矩形相对图形包围盒的外扩量（场景单位）

        if self._drawing:
            return              # 重画过程中滚动条出现/消失引发的 resizeEvent 重入，忽略

        self._drawing = True

        try:
            scene = self.vsdxView.scene()

            anchor = self.vsdxView.mapToScene(self.vsdxView.viewport().rect().center()) if keepView else None

            scene.clear()

            w, h = self.vsdxView.viewport().width(), self.vsdxView.viewport().height()
            if w < 10 or h < 10:
                return          # 视图尚未显示，等页面切换或尺寸变化时再画

            if self.vsdxPage is not None:
                # 引脚文字在某一边变长但窗口还放得下时，缩放比例不变、图形位置不动；
                # 长到放不下时按对称包围盒缩小缩放（芯片中心不动），让文字完全显示
                bRect, center = self.vsdxPage.draw(scene, self.packPins, self.pinFunct)
                halfW = max(center.x() - bRect.left(), bRect.right() - center.x())
                halfH = max(center.y() - bRect.top(), bRect.bottom() - center.y())
                scene.setSceneRect(QtCore.QRectF(center.x() - halfW, center.y() - halfH, 2 * halfW, 2 * halfH)
                                                .adjusted(-PACK_PAD, -PACK_PAD, PACK_PAD, PACK_PAD))
                self.vsdxView.resetTransform()
                _, _, fullW, fullH = self.vsdxView.contentsRect().getRect()         # 不含边框、不含滚动条的完整可用区域
                if fullW > 0 and fullH > 0 and halfW > 0 and halfH > 0:
                    boxW, boxH = 2 * (halfW + PACK_PAD), 2 * (halfH + PACK_PAD)     # 缩放要按含留白的场景尺寸算
                    ''' 滚动条出现会缩小视口、视口缩小又改变缩放、缩放改变又反过来决定滚动条是否出现：
                        按滚动条在场时的视口算缩放，会让滚动条出现/消失来回震荡、重画停不下来；
                        故以完整区域为基准，把滚动条要占的空间预留出来，迭代到滚动条出现/消失的判定稳定为止。
                    '''
                    sbar = max(self.vsdxView.verticalScrollBar().sizeHint().width(), 12)
                    availW, availH = fullW, fullH
                    for _ in range(3):
                        scale = min((availW - 2) / boxW, (availH - 2) / boxH) * self.viewZoom   # 留 2px 余量，避免正好相等
                        availW = fullW - (sbar if boxH * scale > availH else 0)     # 竖直方向溢出：竖滚动条占宽
                        availH = fullH - (sbar if boxW * scale > availW else 0)     # 水平方向溢出：横滚动条占高
                    self.vsdxView.setTransform(QtGui.QTransform().scale(scale, scale))
                    self.vsdxView.centerOn(anchor if anchor is not None else center)
                return

            if not self.win.cmbPack.currentText():
                error = f'package/{self.win.cmbMCU.currentText()}/ 目录下没有封装数据文件'
            elif not self.packName:
                error = f'无法读取 {self.win.cmbPack.currentText()}.txt 第一行的封装名称'
            else:
                error = f'缺少 package/package/{self.packName}.vsdx'

            self.vsdxView.resetTransform()
            scene.setSceneRect(0, 0, w, h)
            item = scene.addSimpleText(error)
            item.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            item.setPos((w - item.boundingRect().width()) / 2, (h - item.boundingRect().height()) / 2)

        finally:
            self._drawing = False

    @staticmethod
    def parsePinFuncs(path):
        ''' 从 SWM341_port.h 中解析出各引脚的可选功能，返回 {引脚名称: [功能, ...]}。
            形如 PORTC_PIN5_I2C1_SCL 的宏解析出 PC5: I2C1_SCL。
        '''
        funcs = {}
        try:
            with open(path, encoding='utf-8', errors='ignore') as cf:
                for m in re.finditer(r'\bPORT([A-Z]+)_PIN(\d+)_([A-Z0-9_]+)', cf.read()):
                    pname = 'P%s%s' % (m.group(1), m.group(2))
                    if m.group(3) not in funcs.setdefault(pname, []):
                        funcs[pname].append(m.group(3))
        except OSError:
            pass

        return funcs
