#MicroPython SSD1306 OLED driver, I2C and SPI interfaces created by Adafruit
# https://github.com/RuiSantosdotme/ESP-MicroPython/blob/master/code/Others/OLED/ssd1306.py

import time
import framebuf

# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)


class Ssd1306:
  def __init__(self, width, height, externalvcc):
    self.__width = width
    self.__height = height
    self.__externalVcc = externalvcc
    self.pages = self.__height // 8
    # Note the subclass must initialize self.__framebuf to a framebuffer.
    # This is necessary because the underlying data buffer is different
    # between I2C and SPI implementations (I2C needs an extra byte).
    self.poweron()
    self.init_display()

  def init_display(self):
    for cmd in ( SET_DISP | 0x00 # off
               # address setting
               , SET_MEM_ADDR
               , 0x00 # horizontal
               # resolution and layout
               , SET_DISP_START_LINE | 0x00
               , SET_SEG_REMAP | 0x01 # column addr 127 mapped to SEG0
               , SET_MUX_RATIO
               , self.__height - 1
               , SET_COM_OUT_DIR | 0x08 # scan from COM[N] to COM0
               , SET_DISP_OFFSET, 0x00
               , SET_COM_PIN_CFG, 0x02 if self.__height == 32 else 0x12
               # timing and driving scheme
               , SET_DISP_CLK_DIV, 0x80
               , SET_PRECHARGE, 0x22 if self.__externalVcc else 0xf1
               , SET_VCOM_DESEL, 0x30 # 0.83*Vcc
               # display
               , SET_CONTRAST, 0xff # maximum
               , SET_ENTIRE_ON # output follows RAM contents
               , SET_NORM_INV # not inverted
               # charge pump
               , SET_CHARGE_PUMP, 0x10 if self.__externalVcc else 0x14
               , SET_DISP | 0x01 # on
               ):
      self.write_cmd(cmd)
    self.fill(0)
    self.show()

  def poweroff(self):
    self.write_cmd(SET_DISP | 0x00)

  def contrast(self, contrast):
    self.write_cmd(SET_CONTRAST)
    self.write_cmd(contrast)

  def invert(self, invert):
    self.write_cmd(SET_NORM_INV | (invert & 1))

  def show(self):
    x0 = 0
    x1 = self.__width - 1
    if self.__width == 64:
      # displays with width of 64 pixels are shifted by 32
      x0 += 32
      x1 += 32
    self.write_cmd(SET_COL_ADDR)
    self.write_cmd(x0)
    self.write_cmd(x1)
    self.write_cmd(SET_PAGE_ADDR)
    self.write_cmd(0)
    self.write_cmd(self.pages - 1)
    self.write_framebuf()

  def clear(self):
    self.__buffer[0:16] = 0
   
  def fill(self, color):
    self.__framebuf.fill(color)

  def pixel(self, x, y, color):
    self.__framebuf.pixel(x, y, color)

  def scroll(self, dx, dy):
    self.__framebuf.scroll(dx, dy)

  def text(self, string, x, y, color=1):
    self.__framebuf.text(string, x, y, color)

  def line(self, y, color):
    for x in range(0, self.__width, 1):
      self.__framebuf.pixel(x, y, color)

class Ssd1306I2c(Ssd1306):
  def __init__(self, width, height, i2c, addr=0x3c, externalvcc=False):
    self.__i2c = i2c
    self.__addr = addr
    self.__temp = bytearray(2)
    # Add an extra byte to the data buffer to hold an I2C data/command byte
    # to use hardware-compatible I2C transactions.  A memoryview of the
    # buffer is used to mask this byte from the framebuffer operations
    # (without a major memory hit as memoryview doesn't copy to a separate
    # buffer).
    self.__buffer = bytearray(((height // 8) * width) + 1)
    self.__buffer[0] = 0x40  # Set first byte of data buffer to Co=0, D/C=1
    self.__framebuf = framebuf.FrameBuffer(memoryview(self.__buffer)[1:]
                                          , width
                                          , height
                                          , framebuf.MVLSB
                                          )
    super().__init__(width, height, externalvcc)

  def write_cmd(self, cmd):
    self.__temp[0] = 0x80 # Co=1, D/C#=0
    self.__temp[1] = cmd
    self.__i2c.writeto(self.__addr, self.__temp)

  def write_framebuf(self):
    # Blast out the frame buffer using a single I2C transaction to support
    # hardware I2C interfaces.
    self.__i2c.writeto(self.__addr, self.__buffer)

  def poweron(self):
    pass


class Ssd1306Spi(Ssd1306):
  def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
    self.__rate = 10 * 1024 * 1024
    dc.init(dc.OUT, value=0)
    res.init(res.OUT, value=0)
    cs.init(cs.OUT, value=1)
    self.__spi = spi
    self.__dc = dc
    self.__res = res
    self.__cs = cs
    self.__buffer = bytearray((height // 8) * width)
    self.__framebuf = framebuf.FrameBuffer1(self.__buffer, width, height)
    super().__init__(width, height, external_vcc)

  def write_cmd(self, cmd):
    self.__spi.init(baudrate=self.__rate, polarity=0, phase=0)
    self.__cs.high()
    self.__dc.low()
    self.__cs.low()
    self.__spi.write(bytearray([cmd]))
    self.__cs.high()

  def write_framebuf(self):
    self.__spi.init(baudrate=self.__rate, polarity=0, phase=0)
    self.__cs.high()
    self.__dc.high()
    self.__cs.low()
    self.__spi.write(self.__buffer)
    self.__cs.high()

  def poweron(self):
    self.__res.high()
    time.sleep_ms(1)
    self.__res.low()
    time.sleep_ms(10)
    self.__res.high()
    