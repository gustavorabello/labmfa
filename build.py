# -*- coding: utf-8 -*-
## =================================================================== ##
#  File: build.py
#  Created: 31-Oct-2025
#  Maintained by: Gustavo Rabello dos Anjos
#  E-mail: gustavo.rabello@gmail.com
#  Description: Deploys local Pelican static site to remote server via SFTP
#  Compatible with Python 3.13+
## =================================================================== ##

import user
import paramiko, os, shutil, time
from subprocess import call
from stat import S_ISDIR
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Server authentication (from user.py)
server = user.server
username = user.username
password = user.password
port = user.port

# Connect via SFTP
transport = paramiko.Transport((server, port))
transport.connect(username=username, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)


def isdir(path):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        return False


def rm(path):
    """Remove remote directory contents recursively."""
    try:
        files = sftp.listdir(path=path)
    except IOError:
        print(Fore.RED + "⚠️  Remote path not found: " + path)
        return

    if 'html' in files:
        files.remove('html')

    while files != 0:
        if not path.endswith("/"):
            path = "%s/" % path

        if not len(files):
            if path == '/':
                break
            if path != '/html/':
                sftp.rmdir(path)
            return

        for f in files:
            filepath = "%s/%s" % (path, f)
            if isdir(filepath):
                rm(filepath)
            else:
                sftp.remove(filepath)

        files = sftp.listdir(path=path)

    print(Fore.YELLOW + "🧹  Remote directory cleaned: " + Fore.CYAN + path)


def genSite():
    """Generate static site locally with Pelican."""
    directory = './output'
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(Fore.YELLOW + "🗑️  Removed old local directory: " + Fore.CYAN + directory)

    print(Fore.GREEN + "⚙️  Generating Pelican site...")
    call(['pelican', ''])
    print(Fore.GREEN + "✅  Site generation complete.")


def upload(localpath, remotepath):
    """Recursively upload local site to remote server."""
    print(Fore.BLUE + "🚀  Uploading local site to server...")
    os.chdir(os.path.split(localpath)[0])
    parent = os.path.split(localpath)[1]
    for walker in os.walk(parent):
        try:
            if walker[0] == 'output':
                remotedir = 'html'
            else:
                remotedir = (walker[0]).replace(parent + '/', '')
            sftp.mkdir(os.path.join(remotepath, remotedir))
        except:
            pass

        for file in walker[2]:
            if walker[0] == 'output':
                remotedir = (walker[0]).replace(parent, '')
                sftp.put(os.path.join(walker[0], file),
                         os.path.join(remotepath, remotedir, file))
            else:
                remotedir = (walker[0]).replace(parent + '/', '')
                sftp.put(os.path.join(walker[0], file),
                         os.path.join(remotepath, remotedir, file))
    print(Fore.BLUE + "✅  Upload complete.")


if __name__ == "__main__":
    print("")
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════")
    print(Style.BRIGHT + Fore.CYAN + "🌐  DEPLOY SCRIPT – LABMFA WEBSITE")
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════")
    start = time.time()

    print("\n" + Fore.YELLOW + "→ Step 1:" + Fore.RESET + " Removing old site on server...")
    rm('/html/')

    print("\n" + Fore.YELLOW + "→ Step 2:" + Fore.RESET + " Generating local Pelican site...")
    genSite()

    print("\n" + Fore.YELLOW + "→ Step 3:" + Fore.RESET + " Uploading site to server...")
    upload('./output', './html')

    print("\n" + Fore.YELLOW + "→ Step 4:" + Fore.RESET + " Closing SFTP connection...")
    sftp.close()

    elapsed = time.time() - start
    print("\n" + Style.BRIGHT + Fore.GREEN + "✅  Deployment finished successfully!")
    print(Fore.CYAN + "⏱️  Total time: %.2f seconds" % elapsed)
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════\n")
