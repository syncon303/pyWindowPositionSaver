from win32gui import EnumWindows, GetWindowRect, GetWindowText, MoveWindow
from win32api import EnumDisplayMonitors
# from win32api import GetSystemMetrics
# from win32api import GetMonitorInfo
from time import sleep
import pywintypes


debug = False


def get_window_positions():
    # App data is organized into dict with window handle (HWND) as key and list of coordinates as value of each entry
    _db = dict()

    def _callback(hwnd, _extra):
        # get window rectangle, convert bottom/right to height/width and store the coordinates
        _x, _y, _x2, _y2 = GetWindowRect(hwnd)
        _h = _y2 - _y
        _w = _x2 - _x
        if _h == _w == 0:
            return
        _title = GetWindowText(hwnd)
        _db[hwnd] = _x, _y, _w, _h, _title

    EnumWindows(_callback, None)
    return _db


def restore_window_positions(c_db, store_db):
    _db = dict()
    for k, v in c_db.items():
        if k in store_db:
            _l, _t, _r, _b, _ = store_db[k]
            try:
                MoveWindow(k, _l, _t, _r, _b, True)
            except pywintypes.error:
                # intercept and ignore 'access denied' errors
                pass


def get_displays():
    """ Get display information and return width and height of desktop.

    :return: (tuple) width, height
    """
    all_displays = EnumDisplayMonitors(None)
    # format: [(<PyHANDLE:393965>, <PyHANDLE:0>, (0, 0, 2560, 1600)),
    #          (<PyHANDLE:51059905>, <PyHANDLE:0>, (2560, 0, 5120, 1440))]
    w, h = 0, 0
    for display in all_displays:
        r = display[2]  # get virtual screen box for each display
        w = r[2] if r[2] > w else w  # search for max right (width) coordinate
        h = r[3] if r[3] > h else h  # search for max bottom (height) coordinate
    return w, h


def app_keeper():
    max_scr = get_displays()
    prev_scr = get_displays()
    prev_wins = dict()
    stored_wins = dict()
    while True:
        cur_wins = get_window_positions()
        current_scr = get_displays()
        if current_scr[0] > max_scr[0] or current_scr[1] > max_scr[1]:
            # another screen was added to the desktop
            max_scr = current_scr
            if debug:
                print('Desktop size increased to ', current_scr)
        elif current_scr != max_scr and prev_scr == max_scr and current_scr != prev_scr:
            if debug:
                print('Desktop size reduced, storing window positions before change.')
            stored_wins = prev_wins
        elif current_scr == max_scr and current_scr != prev_scr:
            if debug:
                print('Desktop size reverted to max, restoring window positions.')
            restore_window_positions(cur_wins, stored_wins)

        # store previous screen and app state
        prev_scr = current_scr
        prev_wins = cur_wins

        sleep(1)  # sleep between tries


if __name__ == '__main__':
    app_keeper()
