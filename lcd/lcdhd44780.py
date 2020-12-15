""" Provides an API for talking to HD44780 compatible character LCDs.
"""
import time

class LcdHD44780:
  """ Implements the API for talking with HD44780 compatible character LCDs.
      This class only knows what commands to send to the LCD, and not
      how to get them to the LCD.
      It is expected that a derived class will implement the dummy functions.
  """
  # HD44780 LCD controller command set (avrlib lcd.h header file)

  LCD_CLR        = 0b00000001     # 0x01 DB0: clear display
  LCD_HOME       = 0b00000010     # 0x02 DB1: return to home position

  LCD_ENTRY_MODE = 0b00000100     # 0x04 DB2: set entry mode
  LCD_ENTRY_INC  = 0b00000010     # 0x02 --DB1: increment
  LCD_ENTRY_SHIFT= 0b00000001     # 0x01 --DB0: shift

  LCD_ON_CTRL    = 0b00001000     # 0x08 DB3: turn lcd/cursor on
  LCD_ON_DISPLAY = 0b00000100     # 0x04 --DB2: turn display on
  LCD_ON_CURSOR  = 0b00000010     # 0x02 --DB1: turn cursor on
  LCD_ON_BLINK   = 0b00000010     # 0x01 --DB0: blinking cursor

  LCD_MOVE       = 0b00010000     # 0x10 DB4: move cursor/display
  LCD_MOVE_DISP  = 0b00001000     # 0x08 --DB3: move display (0-> move cursor)
  LCD_MOVE_RIGHT = 0b00000100     # 0x04 --DB2: move right (0-> left)

  LCD_FUNCTION       = 0b00100000 # 0x20 DB5: function set
  LCD_FUNCTION_8BIT  = 0b00010000 # 0x10 --DB4: set 8BIT mode (0->4BIT mode)
  LCD_FUNCTION_2LINES= 0b00001000 # 0x08 --DB3: two lines (0->one line)
  LCD_FUNCTION_10DOTS= 0b00000100 # 0x04 --DB2: 5x10 font (0->5x7 font)
  LCD_FUNCTION_RESET = 0b00110000 # 0x30 See "Initializing by Instruction" section

  LCD_CGRAM      = 0b01000000     # 0x40 DB6: set CG RAM address
  LCD_DDRAM      = 0b10000000     # 0x80 DB7: set DD RAM address

  LCD_RS_CMD   = 0
  LCD_RS_DATA  = 1

  LCD_RW_WRITE = 0
  LCD_RW_READ  = 1

  def __init__(self, num_lines, num_columns):
    self.num_lines = num_lines
    if self.num_lines > 4:
      self.num_lines = 4
    self.num_columns = num_columns
    if self.num_columns > 40:
      self.num_columns = 40
    self.__col = 0
    self.__row = 0
    self.__colRecent = 0
    self.__rowRecent = 0
    self.__backlight = True
    self.displayOff()
    self.backlightOn()
    self.clear()
    self.__writeCommand(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
    self.cursorOff()
    self.displayOn()

  @property
  def row(self):
    return self.__row

  @property
  def col(self):
    return self.__col

  def clear(self):
    """ Clears the LCD display and moves the cursor to the top left
        corner.
    """
    self.__writeCommand(self.LCD_CLR)
    self.__writeCommand(self.LCD_HOME)
    self.__row = 0
    self.__col = 0

  def cursorOn(self):
    """ Causes the cursor to be made visible.
    """
    self.__writeCommand(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                        self.LCD_ON_CURSOR)

  def cursorOff(self):
    """ Causes the cursor to be hidden.
    """
    self.__writeCommand(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

  def cursorBlinkOn(self):
    """ Turns on the cursor, and makes it blink."""
    self.__writeCommand(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                        self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

  def cursorBlinkOff(self):
    """ Turns on the cursor, and makes it no blink (i.e. be solid).
    """
    self.__writeCommand(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                        self.LCD_ON_CURSOR)

  def displayOn(self):
    """ Turns on (i.e. unblanks) the LCD.
    """
    self.__writeCommand(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

  def displayOff(self):
    """ Turns off (i.e. blanks) the LCD.
    """
    self.__writeCommand(self.LCD_ON_CTRL)

  def backlightOn(self):
    """ Turns the backlight on.
        This isn't really an LCD command, but some modules have backlight
        controls, so this allows the hal to pass through the command.
    """
    self.__backlight = True
    self.__backlightOn()

  def backlightOff(self):
    """ Turns the backlight off.
        This isn't really an LCD command, but some modules have backlight
        controls, so this allows the hal to pass through the command.
    """
    self.__backlight = False
    self.__backlightOff()

  def move(self, row, col, setRecent=False):
    """ Moves the cursor position to the indicated position. The cursor
        position is zero based (i.e. cursor_x == 0 indicates first column).
        Default behavior is without saving the recent cursor position.
    """
    if setRecent:
      self.__rowRecent = self.__row
      self.__colRecent = self.__col
    self.__row = row
    self.__col = col
    addr = col & 0x3f
    if row & 1:
      addr += 0x40    # Lines 1 & 3 add 0x40
    if row & 2:
      addr += 0x14    # Lines 2 & 3 add 0x14
    self.__writeCommand(self.LCD_DDRAM | addr)

  def printChar(self, char):
    """ Writes the indicated character to the LCD at the current cursor
        position, and advances the cursor by one position.
    """
    if char != '\n':
      self.__writeData(ord(char))
      self.__col += 1
    if self.__col >= self.num_columns or char == '\n':
      self.__col = 0
      self.__row += 1
      if self.__row >= self.num_lines:
        self.__row = 0
      self.move(self.__row, self.__col)

  def printStr(self, string, row=None, col=None):
    """ writes the specified string either
          at the current position and set the cursor behind the string
        or
          at the specified coordinates and set the cursor at the recent
          position.
    """
    self.__rowRecent = self.__row
    self.__colRecent = self.__col
    if row is not None and col is not None:
      self.move(row, col)
    for char in string:
      self.printChar(char)
    if row is not None and col is not None:
      self.move(self.__rowRecent, self.__colRecent)
    

  def customChar(self, location, charmap):
    """ Write a character to one of the 8 CGRAM locations, available
        as chr(0) through chr(7).
    """
    location &= 0x7
    self.__writeCommand(self.LCD_CGRAM | (location << 3))
    self.__sleepUs(40)
    for i in range(8):
      self.__writeData(charmap[i])
      self.__sleepUs(40)
    self.move(self.__row, self.__col)

  def __backlightOn(self):
    """ Dummy: Allows the hal layer to turn the backlight on.
        If desired, a derived class will implement this function.
    """
    pass

  def __backlightOff(self):
    """  Dummy: Allows the hal layer to turn the backlight off.
         If desired, a derived class will implement this function.
    """
    pass

  def __writeCommand(self, cmd):
    """ Dummy: Write a command to the LCD.
        It is expected that a derived class will implement this function.
    """
    raise NotImplementedError

  def __writeData(self, data):
    """ Dummy: Write data to the LCD.
        It is expected that a derived class will implement this function.
    """
    raise NotImplementedError

  def __sleepUs(self, usecs):
    """ Sleep for some time (given in microseconds).
    """
    time.sleep_us(usecs)
    