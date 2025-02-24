## =================================================================== ##
#  this is file test.py, created at 27-Apr-2014                #
#  maintained by Gustavo Rabello dos Anjos                              #
#  e-mail: gustavo.rabello@gmail.com                                    #
## =================================================================== ##


import paramiko,os,shutil
from subprocess import call
from stat import S_ISDIR

server ='labmfa.coppe.ufrj.br'
username = 'labmfa.coppe'
password = ''
port = 60027

transport = paramiko.Transport((server, port))
transport.connect(username=username, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)

def isdir(path):
 try:
  return S_ISDIR(sftp.stat(path).st_mode)
 except IOError:
  return False

def rm(path):
 files = sftp.listdir(path=path)
 if 'html' in files:
  files.remove('html')
 while files != 0:

  if not path.endswith("/"):
   path = "%s/" % path
 
  # remove dir if files is empty
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

def genSite():
 # removing local directory paginas
 directory = './output'
 if os.path.exists(directory):
  shutil.rmtree(directory)

 # generating webpage into paginas folder
 call(['pelican',''])


def upload(localpath,remotepath):
 #  recursively upload a full directory
 os.chdir(os.path.split(localpath)[0])
 parent=os.path.split(localpath)[1]
 for walker in os.walk(parent):
  try:
   #print (walker,remotepath,os.path.join(remotepath,walker[0]))
   if walker[0] == 'output':
    remotedir = 'html' #(walker[0]).replace(parent,'')
   else:
    remotedir = (walker[0]).replace(parent+'/','')
   sftp.mkdir(os.path.join(remotepath,remotedir))
  except:
   pass
  for file in walker[2]: # todos os arquivos em / (index.html)
   if walker[0] == 'output':
    remotedir = (walker[0]).replace(parent,'')
    #print (os.path.join(remotepath,remotedir,file))
    sftp.put(os.path.join(walker[0],file),
             os.path.join(remotepath,remotedir,file))
   else: # todos os diretorios
    remotedir = (walker[0]).replace(parent+'/','')
    #print (os.path.join(remotepath,remotedir,file))
    #print (os.path.join(walker[0],file))
    sftp.put(os.path.join(walker[0],file),
             os.path.join(remotepath,remotedir,file))


if __name__ == "__main__":
 print ("")
 print ("---> removing server web site...")
 rm('/html/')
 print ("---> generation local web site...")
 genSite()
 print ("---> uploading web site from local to server...")
 upload('./output','./html')
 print ("---> closing sftp connection. Done!")
 sftp.close
 print ("")

