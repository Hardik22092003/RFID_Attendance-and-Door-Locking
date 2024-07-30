# sdcard.py

import machine
import os

_CMD_TIMEOUT = const(100)

_R1_IDLE_STATE = const(1 << 0)
_R1_ILLEGAL_COMMAND = const(1 << 2)
_TOKEN_CMD25 = const(0xfc)
_TOKEN_STOP_TRAN = const(0xfd)
_TOKEN_DATA = const(0xfe)

class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        self.dummybuf[0] = 0xff
        self.tokenbuf = bytearray(1)
        self.tokenbuf[0] = _TOKEN_DATA

    def _write(self, buf):
        self.spi.write(buf)

    def _readinto(self, buf):
        self.spi.readinto(buf)

    def _cmd(self, cmd, arg, crc=0xff, final=0xff, release=True, skip1=False):
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = arg >> 24
        self.cmdbuf[2] = arg >> 16
        self.cmdbuf[3] = arg >> 8
        self.cmdbuf[4] = arg
        self.cmdbuf[5] = crc
        self.cs(0)
        self._write(self.cmdbuf)
        if skip1:
            self.spi.readinto(self.tokenbuf, 0xff)
        for _ in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xff)
            if not (self.tokenbuf[0] & 0x80):
                if release:
                    self.cs(1)
                    self.spi.write(b'\xff')
                return self.tokenbuf[0]
        self.cs(1)
        self.spi.write(b'\xff')
        return -1

    def _init_card(self):
        self.cs(1)
        for _ in range(10):
            self.spi.write(b'\xff')
        for _ in range(4):
            if self._cmd(0, 0, 0x95) == _R1_IDLE_STATE:
                break
        else:
            raise OSError("no SD card")
        if self._cmd(8, 0x1aa, 0x87, release=False) == _R1_IDLE_STATE:
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
            while self._cmd(55, 0, release=False) == 0 and self._cmd(41, 0x40000000, release=False) != 0:
                pass
            if self._cmd(58, 0, release=False) != 0:
                raise OSError("init error")
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
            self.spi.readinto(self.tokenbuf, 0xff)
        else:
            self._cmd(55, 0)
            while self._cmd(41, 0) != 0:
                pass
        self._cmd(16, 512)

    def readblocks(self, block_num, buf):
        assert len(buf) % 512 == 0, "Buffer length must be a multiple of 512"
        nblocks = len(buf) // 512
        if nblocks == 1
