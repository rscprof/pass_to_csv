#!/usr/bin/python 

import os,logging,sys,subprocess,csv

def main():
    home=os.environ['HOME']
    #logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
    directory_prefix = home+'/.password-store'
    try:
        csvfile = csv.writer(sys.stdout)
        scandir("",directory_prefix,csvfile)
    except FileNotFoundError as err:
        if (err.filename==directory_prefix):
            print("Password storage doesn't exist")
        else: 
            raise err



def scandir (directory,directory_prefix,csv):
    result=[]
    path=directory_prefix
    if directory!='':
        path+='/'+directory
    for file in os.scandir(path):
        if file.is_dir():
           if (file.name!='.git'):
               logging.debug ('scanning directory '+file.name)
               newdirectory=directory
               if (directory!=''):
                   newdirectory+='/'
               newdirectory+=file.name 
               result=result+scandir (newdirectory,directory_prefix,csv)
        elif file.is_file() and file.name[-4:]=='.gpg':
            logging.debug ('scanning file '+file.name)
            name = directory+'/'+file.name[:-4]
            password = subprocess.run(['pass',name],stdout=subprocess.PIPE)
            if password.returncode==0:
                csv.writerow([name,password.stdout.rstrip()])
            else:
                sys.exit('Cannot get the password for '+directory+'/'+file.name)
    return result

if __name__ == "__main__":
    # execute only if run as a script
    main()
    
    
