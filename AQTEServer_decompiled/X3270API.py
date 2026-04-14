# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.10.0 (default, Mar  2 2025, 19:23:58) [Clang 16.0.0 (clang-1600.0.26.3)]
# Embedded file name: X3270API.py
from py3270aq import Emulator
from PIL import Image, ImageDraw, ImageFont
import time, os, sys
sessions = {}
model = 2
import traceback

def save_image(file_path):
    image = Image.new('RGB', (800, 800), color='black')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('arial.ttf', 20)
    f = open(file_path, 'r')
    text = f.read()
    f.close()
    draw.text((5, 5), text, font=font, align='left')
    image.save('screenshot.png')
    return


def clearSS():
    try:
        os.remove('Screenshot.png')
        os.remove('Screenshot.txt')
    except Exception as e:
        try:
            pass
        finally:
            e = None
            del e

    return


def captureSS(request):
    try:
        print_request(request)
        clearSS()
        sname = 'default'
        getSession(sname).exec_command(('PrintText(file,{0})').format('screenshot.txt').encode('ascii'))
        save_image('screenshot.txt')
    except Exception as e:
        try:
            raise
        finally:
            e = None
            del e

    return


def getSession(sname):
    if sname == '' or sname is None:
        sname = 'default'
    check_session(sname)
    return sessions[sname]


def read_session(sfile):
    sinfo = {}
    with open(sfile) as f:
        for line in f:
            key, val = line.split('=', 1)
            sinfo[key.strip().lower()] = val.strip()

    return sinfo


def start_session(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        if sname is None or sname == '':
            sname = 'default'
        sfile = request.get_json().get('path')
        sinfo = read_session(sfile)
        if 'host' not in sinfo:
            raise Exception('Invalid Session File. Host property not found')
        if sname in sessions:
            try:
                getSession(sname).terminate()
                time.sleep(1)
            except Exception as e:
                try:
                    raise
                finally:
                    e = None
                    del e

        em = Emulator(visible=True)
        em.connect(sinfo['host'])
        sessions[sname] = em
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        raise e

    return


def check_session(sname):
    if sname not in sessions:
        raise Exception(('Invalid session {} used. Session not initialized').format(sname))
    return True


def print_request(request):
    print ('Request:{}').format(request.get_json())
    return


def quit_session(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        getSession(sname).terminate()
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def get_screen_text(request):
    try:
        print 'started getting screen text'
        print_request(request)
        sname = request.get_json().get('sname')
        rows = 24
        cols = 80
        screenTextArr = {}
        sess = getSession(sname)
        for i in range(rows):
            print sess.string_get(i + 1, 1, cols)
            screenTextArr[i + 1] = sess.string_get(i + 1, 1, cols)

        print ('screentext is {}').format(screenTextArr)
        return screenTextArr
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def delete_field(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        move_to(request)
        getSession(sname).delete_field()
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def fill_field(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        text = request.get_json().get('text')
        row = int(request.get_json().get('row'))
        col = int(request.get_json().get('col'))
        getSession(sname).fill_field(row, col, text, len(text))
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def send_keys(request, ret=True):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        text = request.get_json().get('text')
        getSession(sname).send_string(text)
        if ret:
            getSession(sname).send_enter()
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def send_special_keys(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        key = request.get_json().get('key').lower()
        if key == '\\' or key == '/':
            getSession(sname).send_string(key)
            return
        if key == 'clear':
            getSession(sname).send_clear()
            time.sleep(1)
            return
        if key == 'enter':
            getSession(sname).send_enter()
            time.sleep(1)
            return
        if key == 'tab':
            getSession(sname).exec_command('Tab')
            time.sleep(1)
            return
        if key == 'erase-line':
            getSession(sname).exec_command('EraseEOF')
            time.sleep(1)
            return
        functionKeys = {}
        for i in range(1, 25):
            functionKeys['f' + str(i)] = str(i)

        if key in functionKeys:
            getSession(sname).exec_command(('PF({})').format(functionKeys[key]))
            time.sleep(1)
            return
        paKeys = {}
        for i in range(1, 13):
            paKeys['pa' + str(i)] = str(i)

        if key in paKeys:
            cmd = ('PA({})').format(paKeys[key])
            print ('Sending Command {}').format(cmd)
            getSession(sname).exec_command(cmd)
            time.sleep(1)
            return
        raise Exception('Invalid Key:' + key)
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def send_clear(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        getSession(sname).send_clear()
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def get_field_text_by_row_col(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        row = int(request.get_json().get('row'))
        col = int(request.get_json().get('col'))
        length = request.get_json().get('length')
        if length == '' or length is None:
            length = 80
        print ('length is {}').format(length)
        return getSession(sname).string_get(row, col, int(length))
    except Exception as e:
        try:
            traceback.print_stack(file=sys.stdout)
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def move_to(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        row = int(request.get_json().get('row'))
        col = int(request.get_json().get('col'))
        return getSession(sname).move_to(row, col)
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def search(request):
    try:
        print_request(request)
        sname = request.get_json().get('sname')
        text = request.get_json().get('text')
        txtParts = text.split(':::')
        print ('TEXT PARTS {}').format(txtParts)
        index = 0
        if len(txtParts) > 1:
            index = int(txtParts[1])
        return find_screen_text(sname, text, int(index))
    except Exception as e:
        try:
            traceback.print_stack(file=sys.stdout)
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def find_next_field(request):
    result = {'top': (-1), 'left': (-1)}
    try:
        rows = 24
        cols = 80
        sname = request.get_json().get('sname')
        text = request.get_json().get('text')
        sess = getSession(sname)
        for i in range(rows):
            rowText = sess.string_get(i + 1, 1, cols)
            if text.lower() in rowText.lower():
                result['top'] = i + 1
                result['left'] = rowText.index(text) + 1
                break

        left = result['left']
        top = result['top']
        print ('FOUND TEXT AT {} {}').format(left, top)
        sess.move_to(left, top)
        print ('EXEC {}').format(sess.exec_command('Tab'))
        return result
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def find_screen_text(sname, text, index=0):
    result = {'top': (-1), 'left': (-1)}
    try:
        rows = 24
        cols = 80
        sess = getSession(sname)
        matches = []
        for i in range(rows):
            rowText = sess.string_get(i + 1, 1, cols)
            if text.lower() in rowText.lower():
                result['top'] = i + 1
                result['left'] = rowText.index(text) + 1
                matches.append(result)

        print ('FOUND MATCHED {} REQUIRED {}').format(len(matches), index)
        if len(matches) > index:
            result = matches[index]
        return result
    except Exception as e:
        try:
            traceback.print_stack(file=sys.stdout)
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


def exec_cmd(request):
    result = {'top': (-1), 'left': (-1)}
    try:
        rows = 24
        cols = 80
        sname = request.get_json().get('sname')
        sess = getSession(sname)
        command = request.get_json().get('cmd')
        sess.exec_command(command)
        return {'status': 'ok'}
    except Exception as e:
        try:
            print e
            raise Exception(e)
        finally:
            e = None
            del e

    return


return

# okay decompiling AQTEServer.exe_extracted/PYZ-00.pyz_extracted/X3270API.pyc
