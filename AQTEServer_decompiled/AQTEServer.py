# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.10.0 (default, Mar  2 2025, 19:23:58) [Clang 16.0.0 (clang-1600.0.26.3)]
# Embedded file name: AQTEServer.py
from flask import *
from AQTEAPI import AQTEAPI
from win32com.client import Dispatch
import pythoncom
try:
    from pywinauto import application
except ImportError:
    print 'pywinauto not installed, please install it using pip'
    application = None

try:
    from pywinauto import *
except ImportError:
    print 'pywinauto not installed, please install it using pip'
    Desktop = None

import pyautogui, base64, win32gui
try:
    from pywinauto.findwindows import find_window
except ImportError:
    print 'pywinauto not installed, please install it using pip'
    find_window = None

import time, os
from pyrobot import Robot
from PIL import ImageGrab
import time, sys
try:
    from pywinauto.keyboard import SendKeys
except ImportError:
    print 'pywinauto not installed, please install it using pip'
    SendKeys = None

from configparser import ConfigParser
import psutil, traceback, X3270API as x3270
app = Flask(__name__)
aqTEAPI = None
aqTEAPI = None
AQ_COM_ID = None
AQ_TE_EXES = []
AQ_TE_TYPE = None
AQ_HLL_DLL_PATH = None
AQ_HLL_ENTRY = None
AQ_WIN_TITLE = None
AQ_TE_APP = None
AQ_TE_WIN_TITLE = None
AQ_TE_WIN = None
try:
    pyautogui.FAILSAFE = False
except:
    pass

robot = Robot()
try:
    reload(sys)
    sys.setdefaultencoding('utf8')
except Exception as e:
    pass

def check_request_valid(request):
    if not request.get_json():
        abort(400)
    print ('REQUEST {}').format(request.get_json())
    return


def focusToSessionWindow_(restore=False, **kwargs):
    global AQ_TE_APP
    app_dialog = None
    if AQ_TE_APP is not None:
        app_dialog = AQ_TE_APP.top_window()
    if restore == True and app_dialog is not None:
        app_dialog.maximize()
        win32gui.SetForegroundWindow(find_window(handle=app_dialog.handle))
    return


def captureSS_old():
    try:
        AQ_TE_APP.top_window().set_focus().CaptureAsImage().save('Screenshot.png')
    except Exception as e:
        pass

    return


def captureSS():
    global AQ_TE_WIN
    global AQ_TE_WIN_TITLE
    try:
        img = None
        if AQ_TE_WIN_TITLE == '':
            img = ImageGrab.grab()
        else:
            if AQ_TE_WIN is not None and AQ_TE_WIN['matched_title'] == AQ_TE_WIN_TITLE and is_window_exists(AQ_TE_WIN['found_window']):
                win = AQ_TE_WIN['found_window']
            else:
                win = Desktop(backend='uia').window(title_re=AQ_TE_WIN_TITLE)
                AQ_TE_WIN = {'found_window': win, 
                   'matched_title': AQ_TE_WIN_TITLE}
            win.set_focus()
            rect = win.rectangle()
            box = (rect.left, rect.top, rect.right, rect.bottom)
            img = ImageGrab.grab(box)
        img.save('Screenshot.png')
    except Exception as e:
        print e

    return


def is_window_exists(win):
    try:
        return win.is_visible()
    except:
        traceback.print_exc(file=sys.stdout)

    return False


def ok(data={}, req=None, restore=False):
    return jsonify({'status': '200', 'error': '', 'data': data})


def error(status, error, req=None, restore=False):
    if req is not None:
        if is_hll(req):
            hll_activate_screen(req, True, restore=restore)
        elif is_x3270(req):
            pass
        else:
            com_activate_screen(req, True)
    return jsonify({'status': status, 'error': (('{}').format(error)), 'data': {}})


def clearSS():
    try:
        os.remove('Screenshot.png')
    except Exception as e:
        pass

    return


def get_com_window_title(pid):
    global AQ_TE_APP
    title = ''
    print 'Getting window title for pid {pid}'
    for child in psutil.Process(pid).children(recursive=True):
        app = application.Application().connect(process=child.pid)
        title = app.top_window().window_text()
        if title != '':
            AQ_TE_APP = app
            return title

    return ''


def hll_connect_ps():
    global aqTEAPI
    if aqTEAPI is None:
        return False
    else:
        if aqTEAPI.isConnected():
            return False
        sessionName = hll_get_session_name()
        aqTEAPI.psConnect(sessionName)
        return True


def hll_disconnect_ps():
    try:
        if aqTEAPI is None:
            return
        if not aqTEAPI.isConnected():
            return
        sessionName = hll_get_session_name()
        aqTEAPI.psDisconnect(sessionName)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

    return


def start_te_session(sess_file):
    import subprocess, time
    if not os.path.isfile(sess_file):
        raise Exception('File ' + sess_file + ' not found')
    try:
        if AQ_TE_EXES and 'pcsws.exe' in map((lambda x: x.lower()), AQ_TE_EXES):
            proc = subprocess.Popen('PCSWS.EXE ' + sess_file, shell=True)
            time.sleep(15.0)
            return get_com_window_title(proc.pid)
    except Exception as e:
        raise Exception(e)

    return


def start_com_session(sess_file):
    import subprocess, time
    return ''


def is_hll(request):
    if AQ_TE_TYPE.lower() == 'hll':
        return True
    else:
        return False

    return


def hll_get_session_name():
    global AQ_WIN_TITLE
    try:
        print ('hll get session name {}').format(AQ_WIN_TITLE)
        return 'A'
    except Exception as e:
        return (
         error(500, e), 500)

    return


def hll_startsession(request):
    global AQ_WIN_TITLE
    try:
        check_request_valid(request)
        path = request.get_json().get('path')
        AQ_WIN_TITLE = start_te_session(path)
        return (
         ok(req=request, restore=True), 200)
    except Exception as e:
        print e
        return (error(500, e, req=request), 500)

    return


def hll_init_conn(request):
    global aqTEAPI
    is_new_connection = False
    try:
        try:
            clearSS()
            check_request_valid(request)
            content = request.get_json()
            print ('request {}').format(content)
            if aqTEAPI is not None:
                print 'INIT cleaning up aqte api instance'
                aqTEAPI.psDisconnect(AQ_WIN_TITLE)
                aqTEAPI.unload()
                aqTEAPI = None
            try:
                hll = AQ_HLL_DLL_PATH
                print ('HLL PATH IS {} and {}').format(hll, AQ_HLL_ENTRY)
                aqTEAPI = AQTEAPI(hll, AQ_HLL_ENTRY)
                is_new_connection = hll_connect_ps()
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                return (error(500, e), 500)

            return (ok(), 200)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return (error(500, e), 500)

    finally:
        if is_new_connection:
            hll_disconnect_ps()

    return


def hll_activate_screen(request, capture_ss=False, restore=False):
    global aqTEAPI
    clearSS()
    check_request_valid(request)
    content = request.get_json()
    print ('request {}').format(content)
    if aqTEAPI is None:
        try:
            hll = AQ_HLL_DLL_PATH
            aqTEAPI = AQTEAPI(hll, AQ_HLL_ENTRY)
            print ('HLL ACTIVATED', aqTEAPI)
        except Exception as e:
            return (
             error(500, e), 500)

    print ('LOADED HLL {}').format(aqTEAPI)
    try:
        print ('focussing on {}').format(AQ_WIN_TITLE)
        focusToSessionWindow_(restore=restore, title=('Session {}').format(hll_get_session_name()))
        print ('FOCUSSED ON WINDOW', AQ_WIN_TITLE)
    except Exception as e:
        print e

    if capture_ss:
        captureSS()
    print (
     'AQWINTITLE', AQ_WIN_TITLE)
    return


def hll_get_screen_text(request):
    is_new_connection = False
    try:
        try:
            hll_activate_screen(request)
            is_new_connection = hll_connect_ps()
            result = {}
            sname = hll_get_session_name()
            print ('session name {}').format(sname)
            for i in range(1, 25):
                pos = aqTEAPI.convertRowColToPosition(sname, i, 1)['position']
                print ('pos {}').format(pos)
                result[i] = aqTEAPI.copyPresentationSpaceToString(pos, 80)['text']

            return (
             ok({'text': result}, req=request), 200)
        except Exception as e:
            print e
            return (error('500', e, request), 500)

    finally:
        if is_new_connection:
            hll_disconnect_ps()

    return


def hll_sendkeys(request):
    is_new_connection = False
    try:
        try:
            hll_activate_screen(request)
            is_new_connection = hll_connect_ps()
            print request.get_json()
            text = request.get_json().get('text')
            for ch in text:
                aqTEAPI.sendKey(ch)

            return (ok(req=request), 200)
        except Exception as e:
            print e
            return (error('500', e, request), 500)

    finally:
        if is_new_connection:
            hll_disconnect_ps()

    return


def hll_pause(request):
    is_new_connection = False
    try:
        try:
            hll_activate_screen(request)
            is_new_connection = hll_connect_ps()
            ntime = request.get_json().get('time')
            aqTEAPI.pause(ntime)
            return (ok(req=request), 200)
        except Exception as e:
            print e
            return (error('500', e, request), 500)

    finally:
        if is_new_connection:
            hll_disconnect_ps()

    return


def hll_get_field_text_by_row_col(request):
    is_new_connection = False
    try:
        try:
            hll_activate_screen(request)
            is_new_connection = hll_connect_ps()
            row = request.get_json().get('row')
            col = request.get_json().get('col')
            length = request.get_json().get('length')
            result = aqTEAPI.convertRowColToPosition(hll_get_session_name(), row, col)
            position = result['position']
            print ('ROW COL IS {}').format(position)
            result = aqTEAPI.copyFieldToString(position)
            if not (length is None or length == ''):
                length = int(length)
                if len(result['text']) >= length:
                    result['text'] = result['text'][:length]
            return (
             ok(result, req=request), 200)
        except Exception as e:
            print e
            return (error('500', e, request), 500)

    finally:
        if is_new_connection:
            hll_disconnect_ps()

    return


def is_x3270(request):
    return AQ_TE_TYPE.lower() == 'x3270'


def x3270_startsession(request):
    try:
        x3270.start_session(request)
        return (ok(), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error(500, e, req=request), 500)

    return


def x3270_quit_session(request):
    try:
        x3270.quit_session(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_get_screen_text(request):
    try:
        result = x3270.get_screen_text(request)
        return (ok({'text': result}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_fill_field(request):
    try:
        x3270.fill_field(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_sendkeys(request, ret=True):
    try:
        x3270.send_keys(request, ret=ret)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_send_special_key(request):
    try:
        x3270.send_special_keys(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_search(request):
    try:
        result = x3270.search(request)
        return (ok(result, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_get_field_text_by_row_col(request):
    try:
        result = x3270.get_field_text_by_row_col(request)
        return (ok({'text': result}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_find_next_field(request):
    try:
        x3270.find_next_field(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_exec_cmd(request):
    try:
        x3270.exec_cmd(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_delete_field(request):
    try:
        x3270.delete_field(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_move_to(request):
    try:
        x3270.move_to(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def x3270_clearscreen(request):
    try:
        x3270.send_clear(request)
        return (ok({}, req=request), 200)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


def is_extra_client():
    global AQ_COM_ID
    return AQ_COM_ID is not None and AQ_COM_ID.lower() == 'extra.system'


def is_accmgr_client():
    return AQ_COM_ID is not None and AQ_COM_ID.lower() == 'accmgr.system'


def is_hostexplorer_client():
    return AQ_COM_ID is not None and AQ_COM_ID.lower() == 'hostexplorer'


def is_bluezone_client():
    return AQ_COM_ID is not None and AQ_COM_ID.lower() == 'bzwhll.whllobj'


def is_pccom_client():
    return AQ_COM_ID is not None and AQ_COM_ID.lower() == 'pcomm.auteclsession'


def get_com_screen_object(aqCOMAPI):
    print aqCOMAPI
    if is_hostexplorer_client():
        scr = aqCOMAPI.CurrentHost
    if is_bluezone_client():
        aqCOMAPI.Connect('')
        scr = aqCOMAPI
    elif is_pccom_client():
        aqCOMAPI.SetConnectionByName('A')
        scr = aqCOMAPI
    elif is_extra_client() or is_accmgr_client():
        scr = aqCOMAPI.ActiveSession.Screen
    else:
        raise Exception('Invalid COMID:' + AQ_COM_ID + ' registered')
    return scr


def com_activate_screen(request, capture_ss=False):
    clearSS()
    check_request_valid(request)
    sessionfile = request.get_json().get('sessionfile')
    title = AQ_WIN_TITLE
    if title is not None:
        try:
            focusToSessionWindow_(title=AQ_WIN_TITLE)
            print 'FOCUSSED ON WINDOW'
        except Exception as e:
            print 'error'
            print e

        if capture_ss:
            captureSS()
    pythoncom.CoInitialize()
    aqCOMAPI = Dispatch(AQ_COM_ID)
    scr = get_com_screen_object(aqCOMAPI)
    print ('COM ACTIVATE DONE {} {}').format(aqCOMAPI, AQ_COM_ID)
    return scr


def com_init_conn(request):
    try:
        try:
            os.remove('Screenshot.png')
        except Exception as e:
            pass

        check_request_valid(request)
        content = request.get_json()
        print ('request {}').format(content)
        comID = request.get_json().get('comid')
        if comID is None:
            comID = AQ_COM_ID
        pythoncom.CoInitialize()
        aqCOMAPI = Dispatch(comID)
        return (ok(), 200)
    except Exception as e:
        return (
         error(500, e), 500)

    return


def com_startsession(request):
    global AQ_WIN_TITLE
    try:
        print 'COM START SESSION...'
        check_request_valid(request)
        path = request.get_json().get('path')
        print 'STARTING COM BASED TERMINAL SESSION WITH:' + path
        AQ_WIN_TITLE = start_com_session(path)
        return (
         ok(req=request), 200)
    except Exception as e:
        print e
        return (error(500, e, request), 500)

    return


def com_sendkeys(request, transmit=True):
    try:
        activeScreen = com_activate_screen(request)
        print ('sending keys to', is_pccom_client())
        if is_extra_client() or is_accmgr_client():
            activeScreen.SendKeys(request.get_json().get('text'))
            if transmit == True:
                activeScreen.SendKeys('<Transmit>')
        elif is_hostexplorer_client():
            activeScreen.Keys(request.get_json().get('text'))
            if transmit == True:
                activeScreen.RunCmd('Enter')
        elif is_bluezone_client():
            activeScreen.WaitReady(10, 1)
            activeScreen.SendKey(request.get_json().get('text'))
        elif is_pccom_client():
            print (
             'sending keys:', request.get_json().get('text'))
            activeScreen.autECLPS.SendKeys(request.get_json().get('text'))
            if transmit == True:
                print 'sending enter'
                activeScreen.autECLPS.SendKeys('[enter]')
        return (ok(req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, req=request), 500)

    return


def com_putstring(request):
    try:
        text = request.get_json().get('text')
        row = request.get_json().get('row')
        col = request.get_json().get('col')
        activeScreen = com_activate_screen(request)
        if is_extra_client() or is_accmgr_client():
            activeScreen.PutString(text, row, col)
        elif is_hostexplorer_client():
            activeScreen.CursorRc(row, col)
            activeScreen.Keys(text)
        elif is_bluezone_client():
            activeScreen.WaitReady(10, 1)
            activeScreen.WriteScreen(text, row, col)
        elif is_pccom_client():
            if text == '<SET_CURSOR>':
                activeScreen.autECLPS.SetCursorPos(row, col)
            else:
                activeScreen.autECLPS.SetText(text, row, col)
        return (
         ok(req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, req=request), 500)

    return


def com_clear(request):
    try:
        row = request.get_json().get('row')
        col = request.get_json().get('col')
        activeScreen = com_activate_screen(request)
        if is_extra_client() or is_accmgr_client():
            activeScreen.PutString(' ' * activeScreen.cols, row, col)
        elif is_hostexplorer_client():
            activeScreen.CursorRc(row, col)
            activeScreen.Keys(' ' * activeScreen.Columns)
        elif is_bluezone_client():
            activeScreen.WaitReady(10, -1)
            activeScreen.SetCursor(row, col)
            activeScreen.WriteScreen(' ' * 80, row, 1)
        elif is_pccom_client():
            activeScreen.autECLPS.SetText(' ' * 80, row, 1)
        return (
         ok(req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, req=request), 500)

    return


def com_get_field_text_by_row_col(request):
    try:
        row = request.get_json().get('row')
        col = request.get_json().get('col')
        length = request.get_json().get('length')
        activeScreen = com_activate_screen(request)
        result = ''
        cols = 80
        if is_accmgr_client() or is_extra_client():
            cols = activeScreen.cols
        elif is_hostexplorer_client():
            cols = activeScreen.Columns
        if length is None or length == '':
            length = cols - int(col)
        if is_extra_client():
            cols = activeScreen.cols
            if length is None or length == '':
                length = cols - int(col)
            result = activeScreen.Area(int(row), int(col), int(row), int(col) + int(length)).Value
        elif is_accmgr_client():
            cols = activeScreen.cols
            if length is None or length == '':
                length = cols - int(col)
            result = activeScreen.GetString(int(row), int(col), int(length))
        elif is_hostexplorer_client():
            if length is None or length == '':
                length = 0
            result = activeScreen.TextRC(row, col, length)
        elif is_bluezone_client():
            result = activeScreen.ReadScreen(result, length, row, col)
        elif is_pccom_client():
            result = activeScreen.autECLPS.GetText(row, col, length).encode('UTF-8').strip()
        return (ok({'text': result}, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


def com_get_screen_text(request):
    try:
        print 'started getting screen text'
        activeScreen = com_activate_screen(request)
        print ('active screen is ', activeScreen)
        cols = 80
        rows = 24
        if is_accmgr_client() or is_extra_client():
            print (
             'USING EXTRA OR ACCMGR', activeScreen)
            rows = activeScreen.rows
            cols = activeScreen.cols
        elif is_hostexplorer_client():
            rows = activeScreen.Rows
        elif is_bluezone_client():
            rows = 24
        screenTextArr = {}
        for i in range(rows):
            if is_extra_client():
                screenTextArr[i + 1] = activeScreen.Area(i + 1, 1, i + 1, cols).Value
            elif is_accmgr_client():
                screenTextArr[i + 1] = activeScreen.GetString(i + 1, 1, cols)
            elif is_hostexplorer_client():
                screenTextArr[i + 1] = activeScreen.Row(i + 1)
            elif is_bluezone_client():
                scr_txt = ''
                scr_txt = activeScreen.ReadScreen(scr_txt, 80, i, 1)
                screenTextArr[i + 1] = scr_txt
            elif is_pccom_client():
                print 'getting text for pcom client'
                scr_txt = activeScreen.autECLPS.GetText(i + 1, 1, cols).encode('UTF-8').strip()
                print ('text is {}, row {}, col {}').format(scr_txt, i + 1, cols)
                screenTextArr[i + 1] = scr_txt

        print ('screentext is {}').format(screenTextArr)
        return (ok({'text': screenTextArr}, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/ping')
def api_te_ping():
    result = {'pingstatus': 'ok', 
       'message': 'PING success, remote aq server is ready!!!'}
    return (
     ok(result), 200)


@app.route('/te/init', methods=['POST'])
def api_te_init():
    if is_hll(request):
        return hll_init_conn(request)
    else:
        if is_x3270(request):
            return (ok(), 200)
        return com_init_conn(request)

    return


@app.route('/te/startsession', methods=['POST'])
def api_te_startsession():
    print 'request recieved'
    if is_hll(request):
        return hll_startsession(request)
    else:
        if is_hostexplorer_client():
            return (ok(), 200)
        if is_x3270(request):
            return x3270_startsession(request)
        return com_startsession(request)

    return


@app.route('/te/stopteprocess', methods=['POST'])
def stop_te_process():
    try:
        import os
        proc_name = request.get_json().get('pname')
        os.system(('taskkill /f /im {}').format(proc_name))
        return (ok(), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/disconnect', methods=['POST'])
def api_te_disconnect():
    global aqTEAPI
    try:
        if is_hll(request):
            hll_disconnect_ps()
            aqTEAPI.unload()
            aqTEAPI = None
            if AQ_TE_APP is not None:
                AQ_TE_APP.top_window().close()
            if AQ_TE_APP is None and AQ_TE_WIN is not None:
                try:
                    AQ_TE_WIN['found_window'].close()
                except Exception as e:
                    print (
                     'Error closing window', e)

        elif is_x3270(request):
            return x3270_quit_session(request)
        activeScreen = com_activate_screen(request)
        if activeScreen is not None:
            if is_bluezone_client():
                activeScreen.Exit()
        aqCOMAPI = None
        pythoncom.CoUninitialize()
        try:
            AQ_TE_APP.top_window().close()
        except:
            pass

        return (
         ok(), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    print 'request recieved'
    return


@app.route('/te/screentext', methods=['POST'])
def api_te_get_screen_text():
    if is_hll(request):
        return hll_get_screen_text(request)
    else:
        if is_x3270(request):
            return x3270_get_screen_text(request)
        return com_get_screen_text(request)

    return


@app.route('/te/fieldtext_by_row_col', methods=['POST'])
def api_te_get_field_text_by_row_col():
    if is_hll(request):
        return hll_get_field_text_by_row_col(request)
    else:
        if is_x3270(request):
            return x3270_get_field_text_by_row_col(request)
        return com_get_field_text_by_row_col(request)

    return


@app.route('/te/sendkeys', methods=['POST'])
def api_te_sendkeys():
    if is_hll(request):
        resp = hll_sendkeys(request)
        aqTEAPI.sendKey('@E')
    elif is_x3270(request):
        resp = x3270_sendkeys(request)
    else:
        resp = com_sendkeys(request, True)
    return resp


@app.route('/te/pause', methods=['POST'])
def api_te_pause():
    if is_hll(request):
        return hll_pause(request)
    else:
        return (
         ok(req=request), 200)

    return


@app.route('/te/sendkeysnoreturn', methods=['POST'])
def api_te_sendkeys_no_return():
    if is_hll(request):
        return hll_sendkeys(request)
    else:
        if is_x3270(request):
            return x3270_sendkeys(request, ret=False)
        return com_sendkeys(request, False)

    return


@app.route('/te/fieldtext_by_pos', methods=['POST'])
def api_te_get_field_text_by_pos():
    is_new_connection = False
    if is_hll(request):
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                position = request.get_json().get('position')
                length = request.get_json().get('length')
                print ('ROW COL IS {}').format(aqTEAPI.convertPositionToRowCol(sname, position))
                result = aqTEAPI.copyFieldToString(position)
                if not (length is None or length == ''):
                    length = int(length)
                    if len(result['text']) >= length:
                        result['text'] = result['text'][:length]
                return (
                 ok(result, req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         error('500', 'get field text by position api is not supported for X3270 and com based session'), 500)
    return


@app.route('/te/field_text_by_srchtext', methods=['POST'])
def api_te_get_field_text_by_srchtext():
    is_new_connection = False
    if is_hll(request):
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                srchtext = request.get_json().get('srchtext')
                ftype = 'NU'
                if 'ftype' in request.get_json():
                    ftype = request.get_json().get('ftype')
                position = aqTEAPI.findEntryField(srchtext, ftype)
                result = aqTEAPI.copyFieldToString(position)
                return (ok(result, req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         error('500', 'get field text by search text api is not supported for com based session'), 500)
    return


@app.route('/te/clear_field_text_by_srchtext', methods=['POST'])
def api_te_clear_field_text_by_srchtext():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                srchtext = request.get_json().get('srchtext')
                ftype = 'NU'
                if 'ftype' in request.get_json():
                    ftype = request.get_json().get('ftype')
                length = aqTEAPI.findEntryFieldLength(srchtext, ftype)
                print ('current length is {}').format(length)
                print ('empty text is {}.').format(' ' * length)
                aqTEAPI.fillEntryField(srchtext, ' ' * length, ftype)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         error('500', 'clear field text by search text api is not supported for X3270 and com based session'), 500)
    return


@app.route('/te/clear_text_by_row_col', methods=['POST'])
def api_te_clear_field_text_by_row_col():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                text = request.get_json().get('text')
                row = request.get_json().get('row')
                col = request.get_json().get('col')
                print 'CONVERTING ROW COL TO POS'
                result = aqTEAPI.convertRowColToPosition(sname, row, col)
                pos = result['position']
                length = aqTEAPI.findEntryFieldLengthByPos(pos)
                print ('LENGTH IS {}').format(length)
                position = aqTEAPI.copyStringToField(' ' * length, pos)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        if is_x3270(request):
            return x3270_delete_field(request)
        else:
            return com_clear(request)

    return


@app.route('/te/move_to_element_by_srchtext', methods=['POST'])
def api_te_move_to_element_by_srchtext():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                srchtext = request.get_json().get('srchtext')
                ftype = 'NU'
                if 'ftype' in request.get_json():
                    ftype = request.get_json().get('ftype')
                position = aqTEAPI.findEntryField(srchtext, ftype)
                aqTEAPI.moveCursor(position)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         ok(req=request), 200)
    return


@app.route('/te/move_to_element_by_row_col', methods=['POST'])
def api_te_move_to_element_by_row_col():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                row = request.get_json().get('row')
                col = request.get_json().get('col')
                print 'CONVERTING ROW COL TO POS'
                result = aqTEAPI.convertRowColToPosition(sname, row, col)
                pos = result['position']
                position = aqTEAPI.moveCursor(pos)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         ok(req=request), 200)
    return


@app.route('/te/entertext_by_srchtext', methods=['POST'])
def api_te_enter_text_in_field_by_srchtext():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                srchtext = request.get_json().get('srchtext')
                text = request.get_json().get('text')
                if text == '<CLEAR_FIELD>':
                    return api_te_clear_field_text_by_srchtext()
                if text == '<SET_CURSOR>':
                    return api_te_move_to_element_by_srchtext()
                ftype = 'NU'
                if 'ftype' in request.get_json():
                    ftype = request.get_json().get('ftype')
                print ('data {} {} {} {}').format(sname, srchtext, text, ftype)
                aqTEAPI.fillEntryField(srchtext, text, ftype)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        return (
         error('500', 'enter text by fiels using search text api is not supported for X3270 and com based session', request), 500)
    return


@app.route('/te/entertext_by_row_col', methods=['POST'])
def api_te_enter_text_by_row_col():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                sname = hll_get_session_name()
                text = request.get_json().get('text')
                print ('ENTERING', text)
                if text == '<CLEAR_FIELD>':
                    return api_te_clear_field_text_by_row_col()
                if text == '<SET_CURSOR>':
                    return api_te_move_to_element_by_row_col()
                row = request.get_json().get('row')
                col = request.get_json().get('col')
                print 'CONVERTING ROW COL TO POS'
                result = aqTEAPI.convertRowColToPosition(sname, row, col)
                pos = result['position']
                position = aqTEAPI.copyStringToField(text, pos)
                return (ok({'position': position}, req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    else:
        if is_x3270(request):
            return x3270_fill_field(request)
        else:
            return com_putstring(request)

    return


@app.route('/te/capture')
def capture():
    encoded_string = ''
    captureSS()
    try:
        with open('Screenshot.png', 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
    except:
        pass

    result = {'image': encoded_string}
    return (
     ok(result), 200)


@app.route('/te/position', methods=['POST'])
def api_te_position():
    if is_hll(request):
        return (error('500', 'position get api is not supported for hll session'), 500)
    try:
        if is_extra_client() or is_accmgr_client():
            screen = com_activate_screen(request)
            result = {'row': (screen.Row), 'col': (screen.Col)}
        elif is_hostexplorer_client():
            pos = com_activate_screen(request).Cursor
            row = int(pos) / 80 + 1
            col = int(pos) % 80
            result = {'row': row, 'col': col}
        return (
         ok(result, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/waithostquiet', methods=['POST'])
def api_te_wait_host_quiet():
    if is_hll(request):
        return (error('500', 'wait host quiet api is not supported for hll session'), 500)
    try:
        if is_extra_client() or is_accmgr_client():
            com_activate_screen(request).WaitHostQuiet()
        return (
         ok(req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/moveto', methods=['POST'])
def api_te_move_to():
    if is_hll(request):
        return (error('500', 'moveto api is not supported for hll session', request), 500)
    if is_x3270(request):
        return x3270_move_to(request)
    try:
        row = request.get_json().get('row')
        col = request.get_json().get('col')
        if is_extra_client() or is_accmgr_client():
            result = com_activate_screen(request).MoveTo(row, col)
        elif is_hostexplorer_client():
            result = com_activate_screen(request).CursorRc(row, col)
        elif is_pccom_client():
            com_activate_screen(request).autECLPS.SetCursorPos(row, col)
        return (
         ok({'text': result}, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/selection', methods=['POST'])
def api_te_selection():
    if is_hll(request):
        return (error('500', 'selection api is not supported for hll session', request), 500)
    try:
        result = {}
        if is_extra_client() or is_accmgr_client():
            area = com_activate_screen(request).Selection
            result = {'left': (area.Left), 'right': (area.Right), 'top': (area.Top), 
               'bottom': (area.Bottom)}
        return (
         ok({'text': result}, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/search', methods=['POST'])
def api_te_search():
    if is_hll(request):
        return (error('500', 'selection api is not supported for hll session', request), 500)
    if is_x3270(request):
        return x3270_search(request)
    try:
        text = request.get_json().get('text')
        if is_extra_client() or is_accmgr_client():
            area = com_activate_screen(request).Search(text)
            result = {'left': (area.Left), 'right': (area.Right), 'top': (area.Top), 
               'bottom': (area.Bottom)}
        elif is_hostexplorer_client():
            pos = com_activate_screen(request).Search(text, 0, 1, 1)
            print ('search pos', pos)
            if pos[0] > 0:
                row = pos[1]
                col = pos[2]
            else:
                row = -1
                col = -1
            result = {'left': col, 'top': row}
        return (
         ok(result, req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


@app.route('/te/clearscreen', methods=['POST'])
def api_te_clearscreen():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                aqTEAPI.sendKey('@C')
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    elif is_x3270(request):
        return x3270_clearscreen(request)
    try:
        screen = com_activate_screen(request)
        if is_extra_client() or is_accmgr_client():
            screen.SendKeys('<Clear>')
        elif is_hostexplorer_client():
            screen.RunCmd('clear')
        elif is_bluezone_client():
            screen.SendKeys('<Clear>')
        return (ok(req=request), 200)
    except Exception as e:
        print e
        return (error('500', e, request), 500)

    return


def te_press_and_hold_key_(request):
    key_map = {'shift': 'shift', 
       'ctrl': 'ctrl', 
       'alt': 'alt'}
    key = request.get_json().get('key')
    mode = request.get_json().get('mode')
    if key in key_map.keys():
        keyStr = key_map[key]
        print ('press and hold', keyStr)
        if mode == 'down':
            pyautogui.keyDown(str(keyStr))
        else:
            pyautogui.keyUp(str(keyStr))
    else:
        acceptable_keys = ('|').join('%s' % k for k in key_map.keys())
        raise Exception('Invalid Key ' + key + ' sent. Accepted Keys are: ' + acceptable_keys)
    return


@app.route('/te/presskey', methods=['POST'])
def te_press_key():
    try:
        key = request.get_json().get('key')
        pyautogui.keyDown(str(key))
        time.sleep(0.01)
        pyautogui.keyUp(str(key))
        return (ok(), 200)
    except Exception as e:
        print e
        return (error(500, e, req=request), 500)

    return


@app.route('/te/pressandholdkey', methods=['POST'])
def te_press_and_hold_key():
    try:
        te_press_and_hold_key_(request)
        return (ok(), 200)
    except Exception as e:
        print e
        return (error(500, e, req=request), 500)

    return


@app.route('/te/send_special_key', methods=['POST'])
def api_te_send_special_key():
    if is_hll(request):
        is_new_connection = False
        try:
            try:
                hll_activate_screen(request)
                is_new_connection = hll_connect_ps()
                key = request.get_json().get('key')
                if key == '':
                    return (ok(req=request), 200)
                sname = hll_get_session_name()
                keyMap = {'Escape': '@', 
                   'ENTER': '@E', 
                   'TAB': '@T', 
                   'PAGEUP': '@u', 
                   'PAGEDOWN': '@v', 
                   '@': '@@', 
                   'A1': '@x', 
                   'A2': '@y', 
                   'A3': '@z', 
                   'A4': '@+', 
                   'A5': '@%', 
                   'A6': '@&', 
                   'A7': "@'", 
                   'A8': '@(', 
                   'A9': '@)', 
                   'A10': '@*', 
                   'F1': '@1', 
                   'F2': '@2', 
                   'F3': '@3', 
                   'F4': '@4', 
                   'F5': '@5', 
                   'F6': '@6', 
                   'F7': '@7', 
                   'F8': '@8', 
                   'F9': '@9', 
                   'F10': '@a', 
                   'F11': '@b', 
                   'F12': '@c', 
                   'F13': '@d', 
                   'F14': '@e', 
                   'F15': '@f', 
                   'F16': '@g', 
                   'F17': '@h', 
                   'F18': '@i', 
                   'F19': '@j', 
                   'F20': '@k', 
                   'F21': '@l', 
                   'F22': '@m', 
                   'F23': '@n', 
                   'F24': '@o', 
                   'AltCursor': '@$', 
                   'Attention': '@A@Q', 
                   'Backspace': '@<', 
                   'Backtab': '@B', 
                   'Clear': '@C', 
                   'CursorDown': '@V', 
                   'CursorLeft': '@L', 
                   'CursorRight': '@Z', 
                   'CursorSelect': '@A@J', 
                   'CursorUp': '@U', 
                   'Delete': '@D', 
                   'Dup': '@S@x', 
                   'EraseEOF': '@F', 
                   'EraseInput': '@A@F', 
                   'FieldExit': '@A@E', 
                   'FieldMark': '@S@y', 
                   'FieldMinus': '@A@-', 
                   'FieldPlus': '@A@+', 
                   'Home': '@O', 
                   'End': '@q', 
                   'Insert': '@I', 
                   'NewLine': '@N', 
                   'Print': '@P', 
                   'Reset': '@R', 
                   'SysRequest': '@A@H', 
                   'Help': '@H', 
                   'BackwardWord': '@A@z', 
                   'ForwardWord': '@A@y'}
                keyMap = {k.lower(): v for k, v in keyMap.items()}
                print ('key Map {}').format(keyMap)
                if key.lower() in keyMap:
                    aqTEAPI.sendKey(keyMap[key.lower()])
                else:
                    print ('sending unmapped key {}').format(key)
                    aqTEAPI.sendKey(key)
                return (ok(req=request), 200)
            except Exception as e:
                print e
                return (error('500', e, request), 500)

        finally:
            if is_new_connection:
                hll_disconnect_ps()

    elif is_x3270(request):
        return x3270_send_special_key(request)
    keyMap = {'enter': '<Transmit>', 
       'tab': '<Tab>', 
       'down': '<Down>', 
       'Attention': '<Attn>', 
       'backspace': '<BackSpace>'}
    screen = com_activate_screen(request)
    key = request.get_json().get('key')
    if key == '\\' or key == '/':
        SendKeys(key)
        return (
         ok(req=request), 200)
    if is_extra_client() or is_accmgr_client():
        if key.lower() in keyMap:
            screen.SendKeys(keyMap[key.lower()])
            screen.WaitHostQuiet()
            return (
             ok(req=request), 200)
        else:
            return (
             error('500', 'Invalid Key:' + key, request), 500)

    elif is_hostexplorer_client():
        hostexplorerKeys = {'enter': 'Enter', 'tab': 'Tab', 
           'down': 'Down', 
           'newline': 'NewLine', 
           'reset': 'Reset', 
           'erase-eof': 'Erase-EOF', 
           'erase-eol': 'Erase-EOL', 
           'erase-line': 'Erase-Line', 
           'erase-input': 'Erase-Input', 
           'clear': 'Clear', 
           'back-tab': 'Back-Tab', 
           'back-space': 'Back-Space', 
           'left': 'Left', 
           'right': 'Right', 
           'up': 'Up', 
           'down': 'Down', 
           'selectall': 'Edit-SelectAll', 
           'copy': 'Edit-Copy', 
           'paste': 'Edit-Paste', 
           'home': 'Home', 
           'end': 'Cursor-EOL', 
           'toggle-capture': 'Toggle-Capture'}
        for i in range(1, 13):
            hostexplorerKeys['f' + str(i)] = 'Pf' + str(i)

        for i in range(1, 4):
            hostexplorerKeys['pa' + str(i)] = 'Pa' + str(i)

        if key.lower() in hostexplorerKeys:
            screen.RunCmd(hostexplorerKeys[key.lower()])
            return (
             ok(req=request), 200)
        return (error('500', 'Invalid Key:' + key, request), 500)
    elif is_bluezone_client():
        bzKeys = {'enter': '@E', 'tab': '@T', 
           'down': '@X', 
           'pa1': '@x', 
           'pa2': '@y', 
           'pa3': '@z', 
           'pa4': '@+', 
           'pa5': '@%'}
        for i in range(1, 10):
            bzKeys['f' + str(i)] = '@' + str(i)

        for i in range(1, 4):
            bzKeys['pf' + str(i)] = '@A@' + str(i)

        if key.lower() in bzKeys:
            screen.SendKey(bzKeys[key.lower()])
            return (
             ok(req=request), 200)
        screen.SendKey(key)
        return (ok(req=request), 200)
    elif is_pccom_client():
        keys = {}
        for i in range(1, 24):
            keys['f' + str(i)] = '[pf' + str(i) + ']'

        for i in range(1, 4):
            keys['a' + str(i)] = '[pa' + str(i) + ']'

        screen.autECLOIA.WaitForInputReady
        if key.strip() == '':
            return (ok(req=request), 200)
        if key.lower() in keys:
            screen.autECLPS.SendKeys(keys[key.lower()])
            return (
             ok(req=request), 200)
        screen.autECLPS.SendKeys('[' + key.lower() + ']')
        return (ok(req=request), 200)
    return


@app.route('/te/isready', methods=['POST'])
def is_ready():
    if is_hll(request):
        return (ok({'res': 'true'}, req=request), 200)
    screen = com_activate_screen(request)
    print screen.autECLOIA
    print screen.autECLOIA.InputInhibited
    ready = screen.autECLOIA.InputInhibited
    res = 'no'
    if ready == 0:
        res = 'yes'
    return (ok({'res': res}, req=request), 200)


@app.route('/te/ismesswaiting', methods=['POST'])
def is_messwaiting():
    if is_hll(request):
        return (ok({'res': 'yes'}, req=request), 200)
    screen = com_activate_screen(request)
    print screen.autECLOIA
    mess_waiting = screen.autECLOIA.MessageWaiting
    res = 'no'
    if mess_waiting:
        res = 'yes'
    return (ok({'res': res}, req=request), 200)


@app.route('/te/iscommstarted', methods=['POST'])
def is_commstarted():
    if is_hll(request):
        return (ok({'res': 'yes'}, req=request), 200)
    screen = com_activate_screen(request)
    print screen.autECLOIA
    commstarted = screen.autECLOIA.CommStarted
    res = 'no'
    if commstarted:
        res = 'yes'
    return (
     ok({'res': res}, req=request), 200)


@app.route('/te/refresh-screen', methods=['POST'])
def refresh_screen():
    app_dialog = None
    if AQ_TE_APP is not None:
        app_dialog = AQ_TE_APP.top_window()
    if app_dialog is None:
        hwnd = win32gui.GetForegroundWindow()
        app_dialog = application.Application().connect(handle=hwnd).top_window()
    if request.args.get('maximize', 'false').lower() == 'true':
        app_dialog.minimize()
        time.sleep(0.5)
        app_dialog.maximize()
    try:
        win32gui.SetForegroundWindow(app_dialog.handle)
    except:
        pass

    win32gui.InvalidateRect(app_dialog.handle, None, True)
    win32gui.UpdateWindow(app_dialog.handle)
    return


@app.route('/te/test', methods=['POST'])
def api_te_test():
    try:
        if is_x3270(request):
            return x3270_find_next_field(request)
        else:
            return (
             ok({'test': 'success'}, req=request), 200)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


@app.route('/te/exec', methods=['POST'])
def api_te_exec():
    try:
        if is_hll(request):
            return (error('500', 'exec api is not supported for hll session', request), 500)
        else:
            if is_x3270(request):
                return x3270_exec_cmd(request)
            return (error('500', 'exec api is not supported for com based session', request), 500)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return (error('500', e, request), 500)

    return


if __name__ == '__main__':
    try:
        iniFile = 'te.ini'
        if len(sys.argv) > 1:
            iniFile = str(sys.argv[1])
        print iniFile
        try:
            config = ConfigParser()
            config.read(iniFile)
            if config.get('config', 'enabled').lower() != 'true':
                print 'TE SUPPORT NOT ENABLED'
                sys.exit(0)
        except Exception as e:
            print ('TE SUPPORT NOT ENABLED {}').format(e)
            sys.exit(0)

        print ('config is {}').format(config)
        teConfig = config.get('config', 'name')
        print ('teconfig is {}').format(teConfig)
        print ('teConfig te support for {}').format(teConfig)
        AQ_TE_TYPE = config.get(teConfig, 'type')
        if AQ_TE_TYPE.lower() == 'com':
            AQ_COM_ID = config.get(teConfig, 'comid')
        elif AQ_TE_TYPE.lower() == 'hll':
            AQ_HLL_DLL_PATH = config.get(teConfig, 'dll')
            AQ_HLL_ENTRY = config.get(teConfig, 'hll_entry')
        AQ_TE_EXES = config.get(teConfig, 'exes').split(',')
        AQ_TE_WIN_TITLE = config.get(teConfig, 'session_window_title')
        print AQ_TE_TYPE
        print AQ_COM_ID
        print AQ_TE_EXES
        print ('AQ_HLL_ENTRY is {}').format(AQ_HLL_ENTRY)
        print ('AQ_HLL_DLL_PATH is {}:').format(AQ_HLL_DLL_PATH)
        port = 9995
        if config.get('config', 'port') is not None or config.get('config', 'port') != '':
            port = int(config.get('config', 'port'))
        app.run(debug=False, host='0.0.0.0', port=port, threaded=False)
    except Exception as e:
        print (
         'TE SERVER START FAILED', e)
        sys.exit(0)

return

# okay decompiling AQTEServer.exe_extracted/AQTEServer.pyc
