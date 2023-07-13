#! python3
import os
import sys
import wave
import array
import collections
import configparser

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog

from math import ceil
from package import packages
from SDRAMInfo import Devices as sdrs


PAGE_CAN = 1
PAGE_SDR = 2    # SDRAM
PAGE_JPG = 3    # JPEG2Code
PAGE_WAV = 4    # Wave2Code


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

        self.setWindowTitle('%s %s' %(self.windowTitle(), 'v1.3.3'))
        
        self.initSetting()

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('global'):
            self.conf.add_section('global')
            self.conf.set('global', 'mcu', 'SWM341')

        if not self.conf.has_section('mcu.pack'):
            self.conf.add_section('mcu.pack')
            self.conf.set('mcu.pack', 'SWM181', 'SWM181CxTy')
            self.conf.set('mcu.pack', 'SWM190', 'SWM190CxTy')
            self.conf.set('mcu.pack', 'SWM201', 'SWM201CxTy')
            self.conf.set('mcu.pack', 'SWM211', 'SWM211CxTy')
            self.conf.set('mcu.pack', 'SWM260', 'SWM260CxTy')
            self.conf.set('mcu.pack', 'SWM320', 'SWM320RxTy')
            self.conf.set('mcu.pack', 'SWM341', 'SWM341RxTy')
            self.conf.set('mcu.pack', 'SWM342', 'SWM342RxTy')

        if not self.conf.has_section('mcu.freq'):
            self.conf.add_section('mcu.freq')
            self.conf.set('mcu.freq', 'SWM181', '24')
            self.conf.set('mcu.freq', 'SWM190', '60')
            self.conf.set('mcu.freq', 'SWM201', '24')
            self.conf.set('mcu.freq', 'SWM211', '60')
            self.conf.set('mcu.freq', 'SWM260', '60')
            self.conf.set('mcu.freq', 'SWM320', '120')
            self.conf.set('mcu.freq', 'SWM341', '150')
            self.conf.set('mcu.freq', 'SWM342', '150')

        self.MCUPack = {mcu: self.conf.get('mcu.pack', mcu) for mcu in ('SWM181', 'SWM190', 'SWM201', 'SWM211', 'SWM260', 'SWM320', 'SWM341', 'SWM342')}
        self.MCUFreq = {mcu: self.conf.get('mcu.freq', mcu) for mcu in ('SWM181', 'SWM190', 'SWM201', 'SWM211', 'SWM260', 'SWM320', 'SWM341', 'SWM342')}

        self.cmbMCU.setCurrentIndex(self.cmbMCU.findText(self.conf.get('global', 'mcu')))

        self.tabMain.setCurrentIndex(0)

        self.cmbSDRChip.addItems(sdrs.keys())

        if not self.conf.has_section('CAN'):
            self.conf.add_section('CAN')
            self.conf.set('CAN', 'Baudrate', '100')
            self.conf.set('CAN', 'Sample Point', '75')

        self.linCANBaud.setText(self.conf.get('CAN', 'Baudrate'))
        self.linCANSamp.setText(self.conf.get('CAN', 'Sample Point'))

        if not self.conf.has_section('JPEG'):
            self.conf.add_section('JPEG')
            self.conf.set('JPEG', 'Path', '')

        self.linJPGFile.setText(self.conf.get('JPEG', 'Path'))

        if not self.conf.has_section('Wave'):
            self.conf.add_section('Wave')
            self.conf.set('Wave', 'Path', '')

        self.linWavFile.setText(self.conf.get('Wave', 'Path'))

    @pyqtSlot(str)
    def on_cmbMCU_currentIndexChanged(self, mcu):

        self.linFreq.setText(self.MCUFreq[mcu])

        self.cmbPack.clear()
        self.cmbPack.addItems(packages[self.cmbMCU.currentText()].keys())

        if mcu == 'SWM181':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 1
            self.CAN_brpBit = 6

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM190':
            self.tabMain.setTabVisible(PAGE_CAN, False)

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM201':
            self.tabMain.setTabVisible(PAGE_CAN, False)

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM211':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 2
            self.CAN_brpBit = 10

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM260':
            self.tabMain.setTabVisible(PAGE_CAN, False)

            self.tabMain.setTabVisible(PAGE_SDR, False)

        elif mcu == 'SWM320':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 1
            self.CAN_brpBit = 6

            self.tabMain.setTabVisible(PAGE_SDR, True)

        elif mcu =='SWM341':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 2
            self.CAN_brpBit = 10

            self.tabMain.setTabVisible(PAGE_SDR, True)

        elif mcu =='SWM342':
            self.tabMain.setTabVisible(PAGE_CAN, True)
            self.CAN_preDiv = 2
            self.CAN_brpBit = 10

            self.tabMain.setTabVisible(PAGE_SDR, True)

    @pyqtSlot(int)
    def on_tabMain_currentChanged(self, page):
        if page == 0:
            self.lblPack.setText('封装：')
            self.lblPack.setVisible(True)
            self.cmbPack.setVisible(True)
            self.linFreq.setVisible(False)

        elif page == PAGE_CAN:
            self.lblPack.setText('主频（MHz）：')
            self.lblPack.setVisible(True)
            self.cmbPack.setVisible(False)
            self.linFreq.setVisible(True)

        elif page == PAGE_SDR:
            self.lblPack.setText('主频（MHz）：')
            self.lblPack.setVisible(True)
            self.cmbPack.setVisible(False)
            self.linFreq.setVisible(True)

        elif page == PAGE_JPG:
            self.lblPack.setVisible(False)
            self.cmbPack.setVisible(False)
            self.linFreq.setVisible(False)

        elif page == PAGE_WAV:
            self.lblPack.setVisible(False)
            self.cmbPack.setVisible(False)
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
        self.txtSDRShow.append(f'tRP, Row precharge time, Ie. Precharge to Activate delay (ns) :  {sdr.tRP}')
        self.txtSDRShow.append(f'tRCD, Row to column delay, Ie. Activate to Command delay (ns) :  {sdr.tRCD}')
        self.txtSDRShow.append(f'tRFC, Refresh/Active to Refresh/Active Command Period (ns)    :  {sdr.tRFC}')

        if self.cmbMCU.currentText() in ('SWM342', ):
            self.txtSDRShow.append(f'tRRD, Activate to Activate on different bank (ns or tCK)      :  {sdr.tRRD}')
            self.txtSDRShow.append(f'tRAS, Activate to Precharge delay (ns)                        :  {sdr.tRAS}')

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
            divs = (1, 2)
        elif mcu in ('SWM342', ):
            divs = (1,  )

        self.txtSDRShow.clear()

        for cas, clk in sdr.tCLK.items():
            fSDR_max = 1000 / clk

            for div in divs:
                fSDR = fMCU / div
                if fSDR > fSDR_max: continue

                tSDR = 1000 / fSDR              # ns

                nRP = ceil(sdr.tRP / tSDR)
                nRCD = ceil(sdr.tRCD / tSDR)
                nRFC = ceil(sdr.tRFC / tSDR)
                nRRD = int(sdr.tRRD[0]) if type(sdr.tRRD) is str else ceil(sdr.tRRD / tSDR)
                nRAS = ceil(sdr.tRAS / tSDR)

                if mcu == 'SWM320':
                    if nRP  < 3: nRP  = 3
                    if nRCD < 3: nRCD = 3
                    if nRFC < 2: nRFC = 2

                else:
                    if nRFC < 4: nRFC = 4

                if   mcu in ('SWM320', ):
                    self.txtSDRShow.append(f'可用配置（CAS Latency = {cas}）：')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CellSize = SDRAM_CELLSIZE_{sdr.size*8}Mb;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CellBank = SDRAM_CELLBANK_{sdr.bank};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CellWidth = SDRAM_CELLWIDTH_16;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTMRD = SDRAM_TMRD_5;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRRD = SDRAM_TRRD_3;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRAS = SDRAM_TRAS_{nRFC};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRFC};')

                elif mcu in ('SWM341', ):
                    self.txtSDRShow.append(f'可用配置（CAS Latency = {cas}，CLKDIV = {div}）：')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.Size = SDRAM_SIZE_{sdr.size}MB;')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.ClkDiv = SDRAM_CLKDIV_{div};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRFC = SDRAM_TRFC_{nRFC};')

                elif mcu in ('SWM342', ):
                    self.txtSDRShow.append(f'可用配置（CAS Latency = {cas}，CLKDIV = {div}）：')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.ClkDiv = SDRAM_CLKDIV_{div};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.NbrBank = SDRAM_BANK_{sdr.bank};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.NbrRowAddr = SDRAM_ROW_{sdr.nrow};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.NbrColAddr = SDRAM_COLUMN_{sdr.ncol};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.CASLatency = SDRAM_CASLATENCY_{cas};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRP  = SDRAM_TRP_{nRP};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRCD = SDRAM_TRCD_{nRCD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRC  = SDRAM_TRC_{nRFC};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRRD = SDRAM_TRRD_{nRRD};')
                    self.txtSDRShow.append(f'SDRAM_InitStruct.TimeTRAS = SDRAM_TRAS_{nRAS};')
            
                self.txtSDRShow.append('SDRAM_Init(&SDRAM_InitStruct);\n\n')
    
    @pyqtSlot()
    def on_btnJPGFile_clicked(self):
        path, filter = QFileDialog.getOpenFileName(caption='JPEG文件选择', filter='JPEG (*.jpg *.jpeg *.bmp *.ico)', directory=self.linJPGFile.text())
        if path:
            self.linJPGFile.setText(path)

    @pyqtSlot()
    def on_btnJPGConv_clicked(self):
        path, name = os.path.split(self.linJPGFile.text())
        name, _ = os.path.splitext(name)

        if self.cmbJPGOut.currentText() == '不解码':
            img = open(self.linJPGFile.text(), 'rb').read()

            txt = f'const unsigned char jpeg_{name}[{len(img)}] = {{\n'
            for i, x in enumerate(img):
                txt += f'0x{x:02X}, '
                if i%16 == 15: txt += '\n'
            txt += '};\n'

        else:
            ''' 模仿 PIL 的输出格式
            from PIL import Image
            imd = Image.open(self.linJPGFile.text()).getdata()
            '''
            img = QtGui.QImage(self.linJPGFile.text())

            imd = []
            for y in range(img.height()):
                for x in range(img.width()):
                    pix = img.pixel(x, y)
                    imd.append(((pix >> 16) & 0xFF, (pix >> 8) & 0xFF, pix & 0xFF))

            if self.cmbJPGOut.currentText() == 'XRGB888':
                dat = [(p[0] << 16) | (p[1] << 8) | p[2] for p in imd]

            elif self.cmbJPGOut.currentText() == 'XBGR888':
                dat = [(p[2] << 16) | (p[1] << 8) | p[0] for p in imd]

            if self.cmbJPGOut.currentText() == 'RGB565':
                dat = [((p[0] >> 3) << 11) | ((p[1] >> 2) << 5) | (p[2] >> 3) for p in imd]

            elif self.cmbJPGOut.currentText() == 'BGR565':
                dat = [((p[2] >> 3) << 11) | ((p[1] >> 2) << 5) | (p[0] >> 3) for p in imd]

            if self.cmbJPGOut.currentText() in ('RGB565', 'BGR565'):
                txt = f'const unsigned short jpeg_{name}[{len(imd)}] = {{\n'
                for i, x in enumerate(dat):
                    txt += f'0x{x:04X}, '
                    if i%16 == 15: txt += '\n'
                txt += '};\n'

            elif self.cmbJPGOut.currentText() in ('XRGB888', 'XBGR888'):
                txt = f'const unsigned int jpeg_{name}[{len(imd)}] = {{\n'
                for i, x in enumerate(dat):
                    txt += f'0x{x:08X}, '
                    if i%16 == 15: txt += '\n'
                txt += '};\n'

        self.txtJPGShow.clear()
        self.txtJPGShow.append(txt)
        self.txtJPGShow.moveCursor(QtGui.QTextCursor.Start)

    @pyqtSlot()
    def on_btnWavFile_clicked(self):
        path, filter = QFileDialog.getOpenFileName(caption='Wave文件选择', filter='JPEG (*.wav)', directory=self.linWavFile.text())
        if path:
            self.linWavFile.setText(path)

    @pyqtSlot(str)
    def on_linWavFile_textChanged(self, path):
        try:
            wav = wave.open(path, 'rb')

            nchannels, sampwidth, framerate, nframes = wav.getparams()[:4]

            wav.close()

        except Exception as ex:
            self.txtWavShow.setText(f'Open Wave file fail!')

        else:
            self.txtWavShow.setText(f'声道数：{nchannels}, 量化位数：{sampwidth*8}, 采样频率：{framerate}, 采样点数：{nframes}')

    @pyqtSlot()
    def on_btnWavConv_clicked(self):
        self.txtWavShow.clear()

        if not self.chkWavAll.isChecked():
            self.wave_convert(self.linWavFile.text())

        else:
            path, _ = os.path.split(self.linWavFile.text())
            for name in os.listdir(path):
                if name.endswith('.wav'):
                    self.wave_convert(os.path.join(path, name).replace('\\', '/'))

    def wave_convert(self, wavFile):
        self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
        self.txtWavShow.append('{}{}'.format('\n' if self.txtWavShow.toPlainText() else '', wavFile))

        try:
            wav = wave.open(wavFile, 'rb')

            nchannels, sampwidth, framerate, nframes = wav.getparams()[:4]

            wavbin = wav.readframes(nframes)

            wav.close()

        except Exception as ex:
            self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
            self.txtWavShow.append(f'  Open Wave file fail!')

        else:
            self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
            self.txtWavShow.append(f'  声道数：{nchannels}, 量化位数：{sampwidth*8}, 采样频率：{framerate}, 采样点数：{nframes}')

            path, name = os.path.split(wavFile)
            name, _ = os.path.splitext(name)

            if sampwidth == 1:
                wavArr = array.array('B', wavbin)

                if self.cmbWavObit.currentText() == '16-bit':
                    sampwidth = 2

                    wavArr = array.array('H', [x << 8 for x in wavArr])

            elif sampwidth == 2:
                wavArr = array.array('H', wavbin)

                if self.cmbWavObit.currentText() == '8-bit':
                    sampwidth = 1

                    wavArr = array.array('B', [x >> 8 for x in wavArr])

            else:
                self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
                self.txtWavShow.append(f'  Sample Width > 16-bit, Not Support!')
                return

            if nchannels == 1:
                if sampwidth == 1:
                    txt = f'const unsigned char wave_{name}[{nframes}] = {{\n'
                    
                elif sampwidth == 2:
                    txt = f'const unsigned short wave_{name}[{nframes}] = {{\n'
                
                for i, x in enumerate(wavArr):
                    txt += f'0x{x:02X}, ' if sampwidth == 1 else f'0x{x:04X}, '
                    if i%16 == 15: txt += '\n'
                txt += '};\n'
                
            elif nchannels == 2:
                if sampwidth == 1:
                    txtL = f'const unsigned char waveL_{name}[{nframes}] = {{\n'
                    txtR = f'const unsigned char waveR_{name}[{nframes}] = {{\n'

                elif sampwidth == 2:
                    txtL = f'const unsigned short waveL_{name}[{nframes}] = {{\n'
                    txtR = f'const unsigned short waveR_{name}[{nframes}] = {{\n'

                wavArrL, wavArrR = wavArr[0::2], wavArr[1::2]

                for i, x in enumerate(wavArrL):
                    txtL += f'0x{x:02X}, ' if sampwidth == 1 else f'0x{x:04X}, '
                    if i%16 == 15: txtL += '\n'
                txtL += '};\n'

                for i, x in enumerate(wavArrR):
                    txtR += f'0x{x:02X}, ' if sampwidth == 1 else f'0x{x:04X}, '
                    if i%16 == 15: txtR += '\n'
                txtR += '};\n'

                txt = f'{txtL}\n\n{txtR}'

            else:
                self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
                self.txtWavShow.append(f'  Channel Count > 2, Not Support!')
                return

            try:
                path = os.path.join(path, f'{name}.c').replace('\\', '/')

                open(path, 'w', encoding='utf-8').write(txt)

            except Exception as ex:
                self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
                self.txtWavShow.append(f'  Write "{path}" Fail!')

            else:
                self.txtWavShow.moveCursor(QtGui.QTextCursor.End)
                self.txtWavShow.append(f'  Write "{path}" Success!')

    def closeEvent(self, evt):
        self.conf.set('global', 'mcu', self.cmbMCU.currentText())
        self.conf.set('mcu.freq', self.cmbMCU.currentText(), self.linFreq.text())
        self.conf.set('CAN', 'Baudrate', self.linCANBaud.text())
        self.conf.set('CAN', 'Sample Point', self.linCANSamp.text())
        self.conf.set('JPEG', 'Path', self.linJPGFile.text())
        self.conf.set('Wave', 'Path', self.linWavFile.text())
        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    swm = SWMTool()
    swm.show()
    app.exec()
