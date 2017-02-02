from collections import namedtuple
from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref, cast, Structure
from ctypes.wintypes import DWORD
import win32api
import win32con
import win32api
import win32gui
import atexit
from time import time



class KBDLLHOOKSTRUCT(Structure):
    """
    see https://msdn.microsoft.com/en-us/library/windows/desktop/ms644967
    """
    _fields_ = [
        ('vkCode', DWORD),
        ('scanCode', DWORD),
        ('flags', DWORD),
        ('time', DWORD),
        ('dwExtraInfo', DWORD),
    ]

KeyboardEvent = namedtuple('KeyboardEvent', ['event_type',
                                             'key_code',
                                             'key_code_readable',
                                             'scan_code',
                                             'alt_pressed',
                                             'time'])
MouseEvent    = namedtuple('MouseEvent', ['event_type',
                                          'pos_x',
                                          'pos_y',
                                          'time'])

class PyHooker:
    """
    Adapted from http://www.hackerthreads.org/Topic-42395
    as well as the pyhook package
    """

    # virtual keycode constant names to virtual keycodes numerical id
    vk_to_id = {'VK_LBUTTON': 0x01, 'VK_RBUTTON': 0x02, 'VK_CANCEL': 0x03,
                'VK_MBUTTON': 0x04, 'VK_BACK': 0x08, 'VK_TAB': 0x09,
                'VK_CLEAR': 0x0C, 'VK_RETURN': 0x0D, 'VK_SHIFT': 0x10,
                'VK_CONTROL': 0x11, 'VK_MENU': 0x12, 'VK_PAUSE': 0x13,
                'VK_CAPITAL': 0x14, 'VK_KANA': 0x15, 'VK_HANGEUL': 0x15,
                'VK_HANGUL': 0x15, 'VK_JUNJA': 0x17, 'VK_FINAL': 0x18,
                'VK_HANJA': 0x19, 'VK_KANJI': 0x19, 'VK_ESCAPE': 0x1B,
                'VK_CONVERT': 0x1C, 'VK_NONCONVERT': 0x1D, 'VK_ACCEPT': 0x1E,
                'VK_MODECHANGE': 0x1F, 'VK_SPACE': 0x20, 'VK_PRIOR': 0x21,
                'VK_NEXT': 0x22, 'VK_END': 0x23, 'VK_HOME': 0x24,
                'VK_LEFT': 0x25, 'VK_UP': 0x26, 'VK_RIGHT': 0x27,
                'VK_DOWN': 0x28, 'VK_SELECT': 0x29, 'VK_PRINT': 0x2A,
                'VK_EXECUTE': 0x2B, 'VK_SNAPSHOT': 0x2C, 'VK_INSERT': 0x2D,
                'VK_DELETE': 0x2E, 'VK_HELP': 0x2F, 'VK_LWIN': 0x5B,
                'VK_RWIN': 0x5C, 'VK_APPS': 0x5D, 'VK_NUMPAD0': 0x60,
                'VK_NUMPAD1': 0x61, 'VK_NUMPAD2': 0x62, 'VK_NUMPAD3': 0x63,
                'VK_NUMPAD4': 0x64, 'VK_NUMPAD5': 0x65, 'VK_NUMPAD6': 0x66,
                'VK_NUMPAD7': 0x67, 'VK_NUMPAD8': 0x68, 'VK_NUMPAD9': 0x69,
                'VK_MULTIPLY': 0x6A, 'VK_ADD': 0x6B, 'VK_SEPARATOR': 0x6C,
                'VK_SUBTRACT': 0x6D, 'VK_DECIMAL': 0x6E, 'VK_DIVIDE': 0x6F,
                'VK_F1': 0x70, 'VK_F2': 0x71, 'VK_F3': 0x72, 'VK_F4': 0x73,
                'VK_F5': 0x74, 'VK_F6': 0x75, 'VK_F7': 0x76, 'VK_F8': 0x77,
                'VK_F9': 0x78, 'VK_F10': 0x79, 'VK_F11': 0x7A, 'VK_F12': 0x7B,
                'VK_F13': 0x7C, 'VK_F14': 0x7D, 'VK_F15': 0x7E, 'VK_F16': 0x7F,
                'VK_F17': 0x80, 'VK_F18': 0x81, 'VK_F19': 0x82, 'VK_F20': 0x83,
                'VK_F21': 0x84, 'VK_F22': 0x85, 'VK_F23': 0x86, 'VK_F24': 0x87,
                'VK_NUMLOCK': 0x90, 'VK_SCROLL': 0x91, 'VK_LSHIFT': 0xA0,
                'VK_RSHIFT': 0xA1, 'VK_LCONTROL': 0xA2, 'VK_RCONTROL': 0xA3,
                'VK_LMENU': 0xA4, 'VK_RMENU': 0xA5, 'VK_PROCESSKEY': 0xE5,
                'VK_ATTN': 0xF6, 'VK_CRSEL': 0xF7, 'VK_EXSEL': 0xF8,
                'VK_EREOF': 0xF9, 'VK_PLAY': 0xFA, 'VK_ZOOM': 0xFB,
                'VK_NONAME': 0xFC, 'VK_PA1': 0xFD, 'VK_OEM_CLEAR': 0xFE,
                'VK_BROWSER_BACK': 0xA6, 'VK_BROWSER_FORWARD': 0xA7,
                'VK_BROWSER_REFRESH': 0xA8, 'VK_BROWSER_STOP': 0xA9,
                'VK_BROWSER_SEARCH': 0xAA, 'VK_BROWSER_FAVORITES': 0xAB,
                'VK_BROWSER_HOME': 0xAC, 'VK_VOLUME_MUTE': 0xAD,
                'VK_VOLUME_DOWN': 0xAE, 'VK_VOLUME_UP': 0xAF,
                'VK_MEDIA_NEXT_TRACK': 0xB0, 'VK_MEDIA_PREV_TRACK': 0xB1,
                'VK_MEDIA_STOP': 0xB2, 'VK_MEDIA_PLAY_PAUSE': 0xB3,
                'VK_LAUNCH_MAIL': 0xB4, 'VK_LAUNCH_MEDIA_SELECT': 0xB5,
                'VK_LAUNCH_APP1': 0xB6, 'VK_LAUNCH_APP2': 0xB7,
                'VK_OEM_1': 0xBA, 'VK_OEM_PLUS': 0xBB, 'VK_OEM_COMMA': 0xBC,
                'VK_OEM_MINUS': 0xBD, 'VK_OEM_PERIOD': 0xBE, 'VK_OEM_2': 0xBF,
                'VK_OEM_3': 0xC0, 'VK_OEM_4': 0xDB, 'VK_OEM_5': 0xDC,
                'VK_OEM_6': 0xDD, 'VK_OEM_7': 0xDE, 'VK_OEM_8': 0xDF,
                'VK_OEM_102': 0xE2, 'VK_PROCESSKEY': 0xE5, 'VK_PACKET': 0xE7}

    # inverse mapping of keycodes
    id_to_vk = dict([(v, k) for k, v in vk_to_id.items()])

    event_types = {win32con.WM_KEYDOWN: 'key_down',
                   win32con.WM_KEYUP: 'key_up',
                   win32con.WM_SYSKEYDOWN: 'key_down',  # used for Alt key.
                   win32con.WM_SYSKEYUP: 'key_up',  # used for Alt key.
                   win32con.WM_MOUSEMOVE: 'mouse_move',
                   win32con.WM_MOUSEWHEEL: 'mouse_wheel',
                   win32con.WM_LBUTTONDOWN: 'mouse_down_left',
                   win32con.WM_MBUTTONDOWN: 'mouse_down_middle',
                   win32con.WM_RBUTTONDOWN: 'mouse_down_right',
                   }

    handler_keyboard = ''
    hook_keyboard = ''
    previous_keycode = ''
    handler_mouse = ''
    hook_mouse = ''
    handler_destruct = ''
    listen_to_hooks = True

    def id_to_name(self, code):
        '''
        Copied from pyhook

        Gets the keycode name for the given value.

        Args:
            code (integer): Virtual keycode value

        Returns:
            string: Virtual keycode name
        '''
        if (code >= 0x30 and code <= 0x39) or (code >= 0x41 and code <= 0x5A):
            text = chr(code)
        else:
            text = self.id_to_vk.get(code)
            if text is not None:
                text = text[3:].title()
        return text

    def low_level_handler_keyboard(self, nCode, wParam, lParam):
        """
        Processes a low level Windows keyboard event.
        """
        msg = cast(lParam, POINTER(KBDLLHOOKSTRUCT))

        event = ''
        if wParam in self.event_types:
            if msg[0].vkCode == 222 and wParam == win32con.WM_KEYDOWN and self.previous_keycode == 222:
                # if key 222 (ä) is pressed twice, stop the recording
                self.destruct()

            timestamp = self.current_milli_time()
            event = KeyboardEvent(self.event_types[wParam],
                                       msg[0].vkCode,
                                       self.id_to_name(msg[0].vkCode),
                                       msg[0].scanCode,
                                       msg[0].flags & win32con.LLKHF_ALTDOWN == 32,
                                       timestamp)
            self.previous_keycode = msg[0].vkCode
            if self.handler_keyboard:
                self.handler_keyboard(event)

        # Be a good neighbor and call the next hook.
        return windll.user32.CallNextHookEx(self.hook_keyboard, nCode, wParam,
                                            lParam)

    def set_handler_keyboard(self, funcName):
        """Summary

        Args:
            funcName (TYPE): Description

        Returns:
            TYPE: Description
        """
        self.handler_keyboard = funcName

    def set_handler_mouse(self, funcName):
        self.handler_mouse = funcName

    def set_handler_destruct(self, funcName):
        self.handler_destruct = funcName

    def low_level_handler_mouse(self, nCode, wParam, lParam):
        """
        Processes a low level Windows keyboard event.
        """
        event = ''
        if wParam in self.event_types:
            pos_x, pos_y = win32api.GetCursorPos()

            timestamp = self.current_milli_time()
            event = MouseEvent(self.event_types[wParam],
                                    pos_x,
                                    pos_y,
                                    timestamp)
            if self.handler_mouse:
                self.handler_mouse(event)

        # Be a good neighbor and call the next hook.
        return windll.user32.CallNextHookEx(self.hook_mouse, nCode, wParam,
                                            lParam)

    def hook_keyboard(self, pointer):
        self.hook_keyboard = windll.user32.SetWindowsHookExW(
            win32con.WH_KEYBOARD_LL,
            pointer,
            win32api.GetModuleHandle(None), 0)
        # Register to remove the hook when the interpreter exits. Unfortunately
        # a try/finally block doesn't seem to work here.
        atexit.register(windll.user32.UnhookWindowsHookEx, self.hook_keyboard)

    def unhook_keyboard(self):
        windll.user32.UnhookWindowsHookEx(self.hook_keyboard)

    def hook_mouse(self, pointer):
        self.hook_mouse = windll.user32.SetWindowsHookExW(
            win32con.WH_MOUSE_LL,
            pointer,
            win32api.GetModuleHandle(None), 0)
        # Register to remove the hook when the interpreter exits. Unfortunately
        # a try/finally block doesn't seem to work here.
        atexit.register(windll.user32.UnhookWindowsHookEx, self.hook_mouse)

    def unhook_mouse(self):
        """Summary

        Returns:
            TYPE: Description
        """
        windll.user32.UnhookWindowsHookEx(self.hook_mouse)

    def listen(self):
        """
        Calls `handlers` for each keyboard event received. This is a blocking
        call.
        """

        # Our low level handler signature.
        CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
        # Convert the Python handler into C pointer.
        pointer_keyboard = CMPFUNC(self.low_level_handler_keyboard)
        pointer_mouse = CMPFUNC(self.low_level_handler_mouse)

        self.hook_keyboard(pointer_keyboard)
        self.hook_mouse(pointer_mouse)

        while self.listen_to_hooks:
            msg = win32gui.GetMessage(None, 0, 0)
            win32gui.TranslateMessage(byref(msg))
            win32gui.DispatchMessage(byref(msg))

    def current_milli_time(self):
        return int(round(time()*1000))

    def destruct(self):
        self.listen_to_hooks = False
        self.unhook_mouse()
        self.unhook_keyboard()
        if self.handler_destruct:
            self.handler_destruct()
