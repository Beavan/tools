#!/bin/env python3
import hashlib
import logging
import os
import subprocess
import sys
import threading
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CURRENT_MSG_MD5 = ""  # 全局变量,用于存储剪切板中最新内容的MD5值,当检测到值发送变化时,才会剪切板同步


def check_dependencies():
    check_dependencies = ['xclip']
    for dep in check_dependencies:
        r = subprocess.run(['which', dep], capture_output=True)
        if r.returncode != 0:
            logging.error(f'{dep} is not installed')
            sys.exit(1)


def get_clipboard_content(display=os.environ.get('DISPLAY')):  # 返回成功获取内容(bytes)和可能发生的错误
    cmd = f"xclip -selection clipboard -d {display} -o"
    getResult = subprocess.run(cmd, shell=True, capture_output=True)
    if getResult.returncode == 0:
        return getResult.stdout, None
    else:
        return None, getResult.stderr


def sync_clipboard(srcDisplay, destDisplay, interval=1):
    while True:
        # 使用xclip获取指定XServer中剪切板内容
        getClipBytes, err = get_clipboard_content(srcDisplay)
        if err is None:
            md5 = hashlib.md5(getClipBytes).hexdigest()
            global CURRENT_MSG_MD5
            if md5 != CURRENT_MSG_MD5:
                # 使用`xclip -o`获取剪切板内容,不要打开stdout和stderr,否则会卡住
                cmd = f"xclip -selection clipboard -d {destDisplay}"
                writeResult = subprocess.run(cmd, shell=True, input=getClipBytes, timeout=5)
                if writeResult.returncode == 0:
                    with threading.Lock():  # 加锁
                        CURRENT_MSG_MD5 = md5
                    logging.info(f"写入剪切板({destDisplay})成功,{getClipBytes.decode('utf-8')}")
                else:
                    logging.error(f"写入剪切板({destDisplay})失败")
        else:
            logging.error(f"读取剪切板({srcDisplay})失败,{err.decode('utf-8').strip()}")
        time.sleep(interval)  # 循环等待间隔时间


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    current_display = os.environ.get('DISPLAY')  # 获取当前XServer
    parser.add_argument('-s', '--src', type=str, default=current_display, help='源XServer')
    parser.add_argument('-d', '--dest', type=str, default=current_display, help='目标XServer')
    parser.add_argument('-i', '--interval', type=int, default=1, help='同步间隔时间(秒)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pull', action='store_true', help='从目标XServer同步到源XServer')
    group.add_argument('--push', action='store_true', help='从源XServer同步到目标XServer')
    group.add_argument('--sync', action='store_true', help='双向同步源XServer和目标XServer')
    args = parser.parse_args()

    # 检查源XServer和目标XServer是否相同
    if args.src == args.dest:
        logging.error("源XServer和目标XServer不能相同")
        sys.exit(1)
    logging.info(f"源X(当前)Server: {args.src}, 目标XServer: {args.dest}")
    check_dependencies()  # 检查程序依赖组件

    # 根据命令行参数决定同步方向
    if args.pull:
        sync_clipboard(args.dest, args.src, args.interval)
    elif args.push:
        sync_clipboard(args.src, args.dest, args.interval)
    elif args.sync:
        threading.Thread(target=sync_clipboard, args=(args.src, args.dest, args.interval)).start()
        time.sleep(args.interval + 1)  # 解决启动后由于CURRENT_MSG_MD5为空导致首次重复同步问题
        threading.Thread(target=sync_clipboard, args=(args.dest, args.src, args.interval)).start()
