import machine
from esp8266_i2c_lcd import I2cLcd

class Lcd():
  def __init__(self, blacklight=True, cursor=False, cursorBlink=False):
    i2c = machine.I2C(sda=machine.Pin(21), scl=machine.Pin(22))
    addr = i2c.scan()[0]
    self.__lcd = I2cLcd(i2c, addr, 2, 16)
    self.__lcd.clear()
    self.__blacklight=blacklight
    self.__cursor = cursor
    self.__cursorBlink = cursorBlink
    self.setConfig()
    #print(dir(self.__lcd))

  def moveTo(self, row, col):
    self.__lcd.move_to(col, row)

  def write(self, text):
    self.__lcd.putstr(text)
    
  def cursorOn(self):
    self.__cursor = True
    self.__setCursor()

  def cursorOff(self):
    self.__cursor = False
    self.__setCursor()
    
  def cursorBlinkOn(self):
    self.__cursorBlink = True
    self.__setCursorBlink()

  def cursorBlinkOff(self):
    self.__cursorBlink = False
    self.__setCursorBlink()
  
  def showVersion(self, version, row=0, col=12):
    recentCursorX = self.__lcd.cursor_x
    recentCursorY = self.__lcd.cursor_y
    self.__lcd.move_to(col, row)
    self.__lcd.putstr('V{}'.format(version))
    self.__lcd.move_to(recentCursorX, recentCursorY)
    
  def setConfig(self):
    self.__lcd.backlight=self.__blacklight
    self.__setCursorBlink()
    # Reihenfolge beachten, da blink_cursor_off den cursor
    # ggf. nicht wieder versteckt.
    self.__setCursor()
      
  def __setCursor(self):
    if self.__cursor:
      self.__lcd.show_cursor()
    else:
      self.__lcd.hide_cursor()

  def __setCursorBlink(self):
    if self.__cursorBlink:
      self.__lcd.blink_cursor_on()
    else:
      self.__lcd.blink_cursor_off()
