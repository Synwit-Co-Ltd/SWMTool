#! python3
import os
import sys
import collections
import configparser

from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog

from math import ceil
from SDRAMInfo import Devices as sdrs
from PinConfig import PinConfigPage


PAGE_PIN = 0
PAGE_CAN = 1
PAGE_SDR = 2    # SDRAM


'''
from SWMTool_UI import Ui_SWMTool
class SWMTool(QWidget, Ui_SWMTool):
    def __init__(self, parent=None):
        super(SWMTool, self).__init__(parent)
        
        self.setupUi(self)
'''
class SWMTool(QWidget):
    def __init__(self, parent=None):
        super(SWMTool, self).__init__(parent)
        
        uic.loadUi('SWMTool.ui', self)

        self.setWindowTitle('%s %s' %(self.windowTitle(), 'v1.3.9'))
        
        self.tabMain.tabBar().setVisible(False)     # 通过 ComboBox 切换页面

        self.pinPage = PinConfigPage(self)

        self.initSetting()

        self.on_tabMain_currentChanged(self.tabMain.currentIndex())

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('global'):
            self.conf.add_section('global')
            self.conf.set('global', 'mcu', 'SWM341')

        mcus = sorted([name for name in os.listdir('package') if name.startswith('SWM')])
        for mcu in mcus:
            if not self.conf.has_section(mcu):
                self.conf.add_section(mcu)
                self.conf.set(mcu, 'pack', '')
                self.conf.set(mcu, 'freq', '48')
                self.conf.set(mcu, 'sdram', '')
                self.conf.set(mcu, 'can.baudrate', '100')
                self.conf.set(mcu, 'can.sampoint', '75')
                self.conf.set(mcu, 'pin.confpath', '')

        self.cmbMCU.addItems(mcus)
        self.cmbMCU.setCurrentIndex(self.cmbMCU.findText(self.conf.get('global', 'mcu')))

    @pyqtSlot(str)
    def on_cmbMCU_currentIndexChanged(self, mcu):
        self.pinPage.portFuncs = self.pinPage.loadPortFuncs(os.path.join('package', mcu, mcu + '_port.h'))

        self.cmbPack.clear()
        self.cmbPack.addItems(sorted(name[:-4] for name in os.listdir(f'package/{mcu}') if name.endswith('.txt')))

        self.cmbSDRAM.clear()
        self.cmbSDRAM.addItems(sdrs.keys())     # todo: add SDRAM according to the MCU model.
        
        self.linFreq.setText(self.conf.get(mcu, 'freq'))
        self.cmbPack.setCurrentText(self.conf.get(mcu, 'pack'))
        self.cmbSDRAM.setCurrentText(self.conf.get(mcu, 'sdram'))
        self.linCANBaud.setText(self.conf.get(mcu, 'can.baudrate'))
        self.linCANSamp.setText(self.conf.get(mcu, 'can.sampoint'))
        self.linPinPath.setText(self.conf.get(mcu, 'pin.confpath'))

        if mcu == 'SWM181':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 1
            self.CAN_brpBit = 6

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu in ('SWM190', 'SWM201', 'SWM231', 'SWM260'):
            self.tabMain.setTabVisible(PAGE_CAN, False)

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu in ('SWM211', 'SWM221', 'SWM241', 'SWM261', 'SWM330', 'SWM350'):
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 2
            self.CAN_brpBit = 10

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM320':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 1
            self.CAN_brpBit = 6

            self.tabMain.setTabVisible(PAGE_SDR, True)

        elif mcu == 'SWM341':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 2
            self.CAN_brpBit = 10

            self.tabMain.setTabVisible(PAGE_SDR, True)

        ''' 按当前型号的 tab 可见性重建 cmbPage 条目，顺序与 tab 序号一致。 '''
        self.cmbPage.blockSignals(True)
        self.cmbPage.clear()
        for i in range(self.tabMain.count()):
            if self.tabMain.isTabVisible(i):
                self.cmbPage.addItem(self.tabMain.tabText(i), i)     # 用户数据记录 tab 序号，供反查
        self.cmbPage.blockSignals(False)

        self.cmbPage.setCurrentIndex(self.cmbPage.findData(self.tabMain.currentIndex()))

    @pyqtSlot(int)
    def on_cmbPage_currentIndexChanged(self, idx):
        page = self.cmbPage.itemData(idx)
        self.tabMain.setCurrentIndex(page)

        if page == 0:
            QtCore.QTimer.singleShot(0, self.pinPage.drawPack)      # 等页面显示、视图取得实际尺寸后再绘制

    @pyqtSlot(int)
    def on_cmbPack_currentIndexChanged(self, idx):
        self.pinPage.onPackChanged(self.cmbPack.currentText())

    @pyqtSlot(int)
    def on_tabMain_currentChanged(self, page):
        if page in (PAGE_CAN, PAGE_SDR):
            self.lblPack.setVisible(False)
            self.cmbPack.setVisible(False)

            self.lblFreq.setVisible(True)
            self.linFreq.setVisible(True)

        else:
            self.lblFreq.setVisible(False)
            self.linFreq.setVisible(False)
            
            self.lblPack.setVisible(True)
            self.cmbPack.setVisible(True)

    @pyqtSlot()
    def on_btnPinPath_clicked(self):
        path, filter = QFileDialog.getOpenFileName(caption='加载引脚配置文件', filter='引脚配置文件 (*.csv)', directory=self.linPinPath.text())
        if path:
            self.linPinPath.setText(path)

            with open(path, 'r') as csvf:
                package = csvf.readline().strip()
                if package != self.cmbPack.currentText():
                    QMessageBox.critical(self, '错误，试图加载其他封装的引脚配置', f'配置文件记录的封装（{package}）与当前选择的封装（{self.cmbPack.currentText()}）不一致')
                    return

                packSel = {}
                for line in csvf:
                    fields = [field.strip() for field in line.strip().split(',')]
                    if len(fields) == 3 and fields[0].isdigit() and int(fields[0]) in self.pinPage.packPins:
                        packSel[int(fields[0])] = fields[2]

                self.pinPage.packSel = packSel    # 加载即整体替换当前的选择
                self.pinPage.drawPack()

    @pyqtSlot()
    def on_btnPinSave_clicked(self):
        path, filter = QFileDialog.getSaveFileName(caption='保存引脚配置文件', filter='引脚配置文件 (*.csv)', directory=self.linPinPath.text())
        if path:
            self.linPinPath.setText(path)
            
            with open(path, 'w') as csvf:
                csvf.write(f'{self.cmbPack.currentText()}\n\n')

                for num, func in sorted(self.pinPage.packSel.items()):     # 功能不为 GPIO 的引脚
                    csvf.write(f'{num}, {self.pinPage.packPins[num]}, {func}\n')

    @pyqtSlot()
    def on_btnPinGen_clicked(self):
        pins = []
        for num, func in self.pinPage.packSel.items():
            label = self.pinPage.packPins[num]          # PC5
            port = label[1:].rstrip('0123456789')       #  C
            pnum = label[1 + len(port):]                #   5
            pins.append((port, int(pnum), func))

        c_code = ''
        for port, pnum, func in sorted(pins):
            c_code += f'PORT_Init(PORT{port}, PIN{pnum}, PORT{port}_PIN{pnum}_{func}, 1);\n'

        path, filter = QFileDialog.getSaveFileName(caption='保存生成的 C 代码', filter='C Code (*.c)', directory=f'{self.linPinPath.text()}.c')
        if path:
            with open(path, 'w') as cf:
                cf.write(c_code)

    @pyqtSlot()
    def on_btnCANGen_clicked(self):
        self.txtCANInfo.clear()

        try:
            SystemCoreClock = int(float(self.linFreq.text()) * 1000000)
            baudrate        = int(float(self.linCANBaud.text()) * 1000)
            sampoint        =     float(self.linCANSamp.text()) / 100
        except Exception as e:
            self.txtCANInfo.setText('Core Frequency invalid')
            return

        Config = collections.namedtuple('Config', 'bs1 bs2 sjw pos brp')
        configs = []
        for bs1 in range(2, 17):
            for bs2 in range(2, 9):
                TQ_per_bit = 1 + bs1 + bs2
                brp = (SystemCoreClock / self.CAN_preDiv) / 2 / baudrate / TQ_per_bit
                if brp != int(brp) or brp > pow(2, self.CAN_brpBit):     # 不能整除，或寄存器存不下
                    continue

                configs.append(Config(bs1, bs2, min(bs2-1, 4), (1 + bs1) / TQ_per_bit, int(brp)))

        if configs:
            configs.sort(key=lambda c: (abs(sampoint - c.pos), -c.brp))
            for (i, c) in enumerate(configs[:3]):
                self.txtCANInfo.append(f'可用配置 {i+1}（采样点 = {c.pos*100:.1f}%）：')
                self.txtCANInfo.append(f'CAN_initStruct.CAN_bs1 = CAN_BS1_{c.bs1}tq;')
                self.txtCANInfo.append(f'CAN_initStruct.CAN_bs2 = CAN_BS2_{c.bs2}tq;')
                self.txtCANInfo.append(f'CAN_initStruct.CAN_sjw = CAN_SJW_{c.sjw}tq;')
                self.txtCANInfo.append(f'CAN_initStruct.Baudrate = {baudrate};\n\n')

        else:
            self.txtCANInfo.append('要求的配置无法实现')

    @pyqtSlot(str)
    def on_cmbSDRAM_currentTextChanged(self, sdr):
        if not sdr:
            return
        
        sdr = sdrs[sdr]

        self.txtSDRInfo.clear()
        self.txtSDRInfo.append('tCK, CLK Cycle Time (ns)')
        for cas, clk in sdr.tCLK.items():
            self.txtSDRInfo.append(f'   when CAS Latency = {cas}: {clk}')
        self.txtSDRInfo.append(f'tRP,  Row precharge time, Ie. Precharge to Activate delay (ns) :  {sdr.tRP}')
        self.txtSDRInfo.append(f'tRCD, Row to column delay, Ie. Activate to Command delay (ns)  :  {sdr.tRCD}')
        self.txtSDRInfo.append(f'tRC,  Activate to Activate on same bank (ns)                   :  {sdr.tRC}')
        self.txtSDRInfo.append(f'tRRD, Activate to Activate on different bank (ns or tCK)       :  {sdr.tRRD}')
        self.txtSDRInfo.append(f'tRAS, Activate to Precharge delay (ns)                         :  {sdr.tRAS}')

    @pyqtSlot()
    def on_btnSDRGen_clicked(self):
        try:
            fMCU = float(self.linFreq.text())   # MHz
        except Exception as e:
            self.txtSDRInfo.setText('Core Frequency invalid')
            return

        mcu = self.cmbMCU.currentText()
        sdr = sdrs[self.cmbSDRAM.currentText()]

        if   mcu in ('SWM320', ):
            divs = (4,  )
        elif mcu in ('SWM341', ):
            divs = (1, 2) if fMCU <= 140 else (2, )

        self.txtSDRInfo.clear()

        for cas, clk in sdr.tCLK.items():
            fSDR_max = 1000 / clk

            for div in divs:
                fSDR = fMCU / div
                if fSDR > fSDR_max: continue

                tSDR = 1000 / fSDR              # ns

                nRP  = ceil(sdr.tRP  / tSDR)
                nRCD = ceil(sdr.tRCD / tSDR)
                nRC  = ceil(sdr.tRC  / tSDR)
                nRRD = ceil(sdr.tRRD / tSDR) if type(sdr.tRRD) != str else int(sdr.tRRD[0])
                nRAS = ceil(sdr.tRAS / tSDR)

                if mcu == 'SWM320':
                    if nRP  < 3: nRP  = 3
                    if nRCD < 3: nRCD = 3
                    if nRC  < 4: nRC  = 4
                    if nRRD < 2: nRRD = 2
                    if nRAS < 2: nRAS = 2

                else:
                    if nRC  < 4: nRC  = 4

                if   mcu in ('SWM320', ):
                    self.txtSDRInfo.append(f'可用配置（CAS Latency = {cas}）：')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.CellSize = SDRAM_CELLSIZE_{sdr.size*8}Mb;')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.CellWidth = SDRAM_CELLWIDTH_16;')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.RefreshTime = {sdr.tREF};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTMRD = SDRAM_TMRD_6;')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRC};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRRD = SDRAM_TRRD_{nRRD};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRAS = SDRAM_TRAS_{nRAS};')

                elif mcu in ('SWM341', ):
                    self.txtSDRInfo.append(f'可用配置（CAS Latency = {cas}，CLKDIV = {div}）：')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.Size = SDRAM_SIZE_{sdr.size}MB;')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.ClkDiv = SDRAM_CLKDIV_{div};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.RefreshTime = {sdr.tREF};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRInfo.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRC};')
            
                self.txtSDRInfo.append('SDRAM_Init(&SDRAM_InitStruct);\n\n')

    def closeEvent(self, evt):
        self.conf.set('global', 'mcu', self.cmbMCU.currentText())
        self.conf.set(self.cmbMCU.currentText(), 'freq', self.linFreq.text())
        self.conf.set(self.cmbMCU.currentText(), 'pack', self.cmbPack.currentText())
        self.conf.set(self.cmbMCU.currentText(), 'sdram', self.cmbSDRAM.currentText())
        self.conf.set(self.cmbMCU.currentText(), 'can.baudrate', self.linCANBaud.text())
        self.conf.set(self.cmbMCU.currentText(), 'can.sampoint', self.linCANSamp.text())
        self.conf.set(self.cmbMCU.currentText(), 'pin.confpath', self.linPinPath.text())
        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    swm = SWMTool()
    swm.show()
    app.exec()
