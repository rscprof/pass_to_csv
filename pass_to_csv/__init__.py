#!/usr/bin/python

import os
import logging
import sys
import subprocess
import csv
import codecs

class PrepareFilter:
    """
    filter convert ["xxx","yyy"] to ["xxx","","yyy","","","General","Pass"]
    """
    def run(self, list):
        return [list[0],"",list[1],"","","General","Pass"]

class DotFilters:
    """
    composion of two filters
    """
    def __init__(self, filter1, filter2):
        self.filter1 = filter1
        self.filter2 = filter2

    def run(self,list):
        return self.filter2.run(self.filter1.run(list))

class BaseChainFilter:
    def __init__(self, chain):
        self.chain = chain
    def run(self,list):
        result = self.runInside(list)
        if result is None:
            return self.chain.run(list)
        else:
            return result


class DropSlashFilter (BaseChainFilter):
    """
    filter that deletes / in front of string
    """
    def runInside(self, list):
        if list[0][0:1]=='/' and list[0].find('/',1)==-1:
            list[0]=list[0][1:]
            return list
        else:
            return None



class URLWithoutUsernameChainFilter (BaseChainFilter):
    """
    filter that converts ["/xxx.yyy","","zzz","",""] into ["xxx.yyy","","zzz","xxx.yyy",""]
    """
    def runInside(self, list):
        name = list[0]
        password = list[2]
        if (name[0:1]=='/')and(name[1:].find('.')>0):
            list[0]=name[1:]
            list[3]=name[1:]
            return list
        else:
            return None


class URLChainFilter (BaseChainFilter):
    """
    filter that convert ["xxx/yyy","","zzz","",""] into ["yyy","yyy","zzz","xxx",""]
    if it is imposiible then filter start chain filter
    """
    def runInside(self,list):
        name = list[0]
        password = list[2]
        splitFirstPart = name.split('/')
        if (len(splitFirstPart)!=2 or splitFirstPart[0]==""):
            return None
        list[0] = splitFirstPart[0]
        list[1] = splitFirstPart[1]
        list[3] = splitFirstPart[0]
        return list



class identityFunctor:
    """
        functor that return his argument
    """
    def run(self,list):
        return list

class filterWithFunctor:
    """
    This is class-adapter of csv, that use functor to do
    with array (name,password)
    """
    def __init__ (self, parentcsv, functor):
        self.parentcsv = parentcsv
        self.functor = functor

    def writerow(self,list):
        self.parentcsv.writerow(self.functor.run(list))

class filter:
    """
    This is an example of class-adapter for csv
    """
    def __init__(self,parentcsv):
        self.parentcsv = parentcsv

    def writerow(self,list):
        self.parentcsv.writerow(list)

def main():
    home = os.environ['HOME']
#    logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
    directory_prefix = home+'/.password-store'
    try:
        csvfile = csv.writer(sys.stdout)
        scandir("", directory_prefix,
                filterWithFunctor(csvfile,
                DotFilters(PrepareFilter(),
                           URLWithoutUsernameChainFilter(
                                  URLChainFilter(
                                      DropSlashFilter(identityFunctor()))))))
    except FileNotFoundError as err:
        if (err.filename == directory_prefix):
            print("Password storage doesn't exist")
        else:
            raise err


def scandir(directory, directory_prefix, csv):
    """
    scan directory in password storage, that keep in directory_prefix
    and store results in csv by method writerow by sending array with
    two elements: name and password

    :param directory: name of directory inside password storage
    :param directory_prefix: directory where password storage is
    :param csv: object, that gets all pairs of name and passwords
    """

    result = []
    path = directory_prefix
    if directory != '':
        path += '/'+directory
    for file in os.scandir(path):
        if file.is_dir():
            if file.name != '.git':
                logging.debug('scanning directory '+file.name)
                newdirectory = directory
                if directory != '':
                    newdirectory += '/'
                newdirectory += file.name
                result = result + scandir(newdirectory, directory_prefix, csv)
        elif file.is_file() and file.name[-4:] == '.gpg':
            logging.debug('scanning file '+file.name)
            name = directory+'/'+file.name[:-4]
            password = subprocess.run(['pass', name], stdout=subprocess.PIPE)
            if password.returncode == 0:
                csv.writerow([name, password.stdout.rstrip().decode("utf-8")])
            else:
                sys.exit('Cannot get the password for ' +
                         directory + '/' + file.name)
    return result


if __name__ == "__main__":
    # execute only if run as a script
    main()
