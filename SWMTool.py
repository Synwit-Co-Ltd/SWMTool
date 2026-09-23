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

        self.setWindowTitle('%s %s' %(self.windowTitle(), 'v1.3.8'))
        
        self.initSetting()

        self.pinConfig = PinConfigPage(self)

        self.on_tabMain_currentChanged(self.tabMain.currentIndex())

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('global'):
            self.conf.add_section('global')
            self.conf.set('global', 'mcu', 'SWM341')

        if not self.conf.has_section('mcu.freq'):
            self.conf.add_section('mcu.freq')
            self.conf.set('mcu.freq', 'SWM181', '24')
            self.conf.set('mcu.freq', 'SWM190', '60')
            self.conf.set('mcu.freq', 'SWM201', '24')
            self.conf.set('mcu.freq', 'SWM211', '60')
            self.conf.set('mcu.freq', 'SWM221', '72')
            self.conf.set('mcu.freq', 'SWM231', '24')
            self.conf.set('mcu.freq', 'SWM241', '24')
            self.conf.set('mcu.freq', 'SWM260', '60')
            self.conf.set('mcu.freq', 'SWM261', '72')
            self.conf.set('mcu.freq', 'SWM320', '120')
            self.conf.set('mcu.freq', 'SWM330', '120')
            self.conf.set('mcu.freq', 'SWM341', '140')
            self.conf.set('mcu.freq', 'SWM350', '150')

        self.MCUFreq = {mcu.upper(): self.conf.get('mcu.freq', mcu) for mcu in self.conf['mcu.freq'].keys()}

        self.cmbMCU.addItems(self.MCUFreq.keys())

        self.cmbMCU.setCurrentIndex(self.cmbMCU.findText(self.conf.get('global', 'mcu')))

        self.cmbSDRChip.addItems(sdrs.keys())

        if not self.conf.has_section('CAN'):
            self.conf.add_section('CAN')
            self.conf.set('CAN', 'Baudrate', '100')
            self.conf.set('CAN', 'Sample Point', '75')

        self.linCANBaud.setText(self.conf.get('CAN', 'Baudrate'))
        self.linCANSamp.setText(self.conf.get('CAN', 'Sample Point'))

    @pyqtSlot(str)
    def on_cmbMCU_currentIndexChanged(self, mcu):

        self.linFreq.setText(self.MCUFreq[mcu])

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

    @pyqtSlot(int)
    def on_tabMain_currentChanged(self, page):
        if page in (PAGE_CAN, PAGE_SDR):
            self.lblFreq.setVisible(True)
            self.linFreq.setVisible(True)

            self.lblPack.setVisible(False)
            self.cmbPack.setVisible(False)

        else:
            self.lblPack.setVisible(True)
            self.cmbPack.setVisible(True)

            self.lblFreq.setVisible(False)
            self.linFreq.setVisible(False)

    @pyqtSlot()
    def on_btnCANGen_clicked(self):
        self.txtCANShow.clear()

        try:
            SystemCoreClock = int(float(self.linFreq.text()) * 1000000)
            baudrate        = int(float(self.linCANBaud.text()) * 1000)
            sampoint        =     float(self.linCANSamp.text()) / 100
        except Exception as e:
            self.txtCANShow.setText('Core Frequency invalid')
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
                self.txtCANShow.append(f'可用配置 {i+1}（采样点 = {c.pos*100:.1f}%）：')
                self.txtCANShow.append(f'CAN_initStruct.CAN_bs1 = CAN_BS1_{c.bs1}tq;')
                self.txtCANShow.append(f'CAN_initStruct.CAN_bs2 = CAN_BS2_{c.bs2}tq;')
                self.txtCANShow.append(f'CAN_initStruct.CAN_sjw = CAN_SJW_{c.sjw}tq;')
                self.txtCANShow.append(f'CAN_initStruct.Baudrate = {baudrate};\n\n')

        else:
            self.txtCANShow.append('要求的配置无法实现')

    @pyqtSlot(str)
    def on_cmbSDRChip_currentTextChanged(self, sdr):
        sdr = sdrs[sdr]

        self.txtSDRShow.clear()
        self.txtSDRShow.append('tCK, CLK Cycle Time (ns)')
        for cas, clk in sdr.tCLK.items():
            self.txtSDRShow.append(f'   when CAS Latency = {cas}: {clk}')
        self.txtSDRShow.append(f'tRP,  Row precharge time, Ie. Precharge to Activate delay (ns) :  {sdr.tRP}')
        self.txtSDRShow.append(f'tRCD, Row to column delay, Ie. Activate to Command delay (ns)  :  {sdr.tRCD}')
        self.txtSDRShow.append(f'tRC,  Activate to Activate on same bank (ns)                   :  {sdr.tRC}')
        self.txtSDRShow.append(f'tRRD, Activate to Activate on different bank (ns or tCK)       :  {sdr.tRRD}')
        self.txtSDRShow.append(f'tRAS, Activate to Precharge delay (ns)                         :  {sdr.tRAS}')

    @pyqtSlot()
    def on_btnSDRGen_clicked(self):
        try:
            fMCU = float(self.linFreq.text())   # MHz
        except Exception as e:
            self.txtSDRShow.setText('Core Frequency invalid')
            return

        mcu = self.cmbMCU.currentText()
        sdr = sdrs[self.cmbSDRChip.currentText()]

        if   mcu in ('SWM320', ):
            divs = (4,  )
        elif mcu in ('SWM341', ):
            divs = (1, 2) if fMCU <= 140 else (2, )

        self.txtSDRShow.clear()

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
                    self.txtSDRShow.append(f'可用配置（CAS Latency = {cas}）：')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CellSize = SDRAM_CELLSIZE_{sdr.size*8}Mb;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CellWidth = SDRAM_CELLWIDTH_16;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.RefreshTime = {sdr.tREF};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTMRD = SDRAM_TMRD_6;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRC};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRRD = SDRAM_TRRD_{nRRD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRAS = SDRAM_TRAS_{nRAS};')

                elif mcu in ('SWM341', ):
                    self.txtSDRShow.append(f'可用配置（CAS Latency = {cas}，CLKDIV = {div}）：')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.Size = SDRAM_SIZE_{sdr.size}MB;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.ClkDiv = SDRAM_CLKDIV_{div};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.RefreshTime = {sdr.tREF};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRC};')
            
                self.txtSDRShow.append('SDRAM_Init(&SDRAM_InitStruct);\n\n')

    def closeEvent(self, evt):
        self.conf.set('global', 'mcu', self.cmbMCU.currentText())
        self.conf.set('mcu.freq', self.cmbMCU.currentText(), self.linFreq.text())
        self.conf.set('CAN', 'Baudrate', self.linCANBaud.text())
        self.conf.set('CAN', 'Sample Point', self.linCANSamp.text())
        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    swm = SWMTool()
    swm.show()
    app.exec()
