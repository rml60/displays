""" Implements a HD44780 character LCD connected via PCF8574 on I2C.
    This was tested with: ESP32-Pico Discovery-Board
"""

from lcdhd44780 import LcdHD44780
from machine import I2C,Pin
from time import sleep_ms

# The PCF8574 has a jumper selectable address: 0x20 - 0x27
DEFAULT_I2C_ADDR = 0x27

# Defines shifts or masks for the various LCD line attached to the PCF8574

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4


class LcdHD44780I2c(LcdHD44780):
  """ Implements a HD44780 character LCD connected via PCF8574 on I2C.
  """

  def __init__( self
              , i2cAddr=DEFAULT_I2C_ADDR, numLines=2, numColumns=16
              , backlight=True, cursor=False, cursorBlink=False
              , sdaPin=21, sclPin=22):
    self.__i2c = I2C(sda=Pin(sdaPin),scl=Pin(sclPin))
    self.__i2cAddr = i2cAddr
    self.__i2c.writeto(self.__i2cAddr, bytearray([0]))
    sleep_ms(20)   # Allow LCD time to powerup
    # Send reset 3 times
    self.__writeInitNibble(self.LCD_FUNCTION_RESET)
    sleep_ms(5)    # need to delay at least 4.1 msec
    self.__writeInitNibble(self.LCD_FUNCTION_RESET)
    sleep_ms(1)
    self.__writeInitNibble(self.LCD_FUNCTION_RESET)
    sleep_ms(1)
    # Put LCD into 4 bit mode
    self.__writeInitNibble(self.LCD_FUNCTION)
    sleep_ms(1)
    LcdHD44780.__init__(self, numLines, numColumns)
    cmd = self.LCD_FUNCTION
    if numLines > 1:
      cmd |= self.LCD_FUNCTION_2LINES
    self.__writeCommand(cmd)

  def __writeInitNibble(self, nibble):
    """ Writes an initialization nibble to the LCD.
        This particular function is only used during initialization.
    """
    byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
    self.__writeByte(byte)

  def __backlightOn(self):
    """ Allows the hal layer to turn the backlight on.
    """
    self.__i2c.writeto(self.__i2cAddr, bytearray([1 << SHIFT_BACKLIGHT]))

  def __backlightOff(self):
    """ Allows the hal layer to turn the backlight off.
    """
    self.__i2c.writeto(self.__i2cAddr, bytearray([0]))

  def __writeCommand(self, cmd):
    """ Writes a command to the LCD.
        Data is latched on the falling edge of E.
    """
    byte = ((self.__backlight << SHIFT_BACKLIGHT) | (((cmd >> 4) & 0x0f) << SHIFT_DATA))
    self.__writeByte(byte)
    byte = ((self.__backlight << SHIFT_BACKLIGHT) | ((cmd & 0x0f) << SHIFT_DATA))
    self.__writeByte(byte)
    if cmd <= 3:
      # The home and clear commands require a worst case delay of 4.1 msec
      sleep_ms(5)

  def __writeData(self, data):
    """ Write data to the LCD.
    """
    byte = (MASK_RS | (self.__backlight << SHIFT_BACKLIGHT) | (((data >> 4) & 0x0f) << SHIFT_DATA))
    self.__writeByte(byte)
    byte = (MASK_RS | (self.__backlight << SHIFT_BACKLIGHT) | ((data & 0x0f) << SHIFT_DATA))
    self.__writeByte(byte)
    
  def __writeByte(self, byte):
    """ Write Byte to the LCD.
    """
    self.__i2c.writeto(self.__i2cAddr, bytearray([byte | MASK_E]))
    self.__i2c.writeto(self.__i2cAddr, bytearray([byte]))
