#!/usr/bin/python

import os
import logging
import sys
import subprocess
import csv
import codecs
import argparse

class PrepareFilter:
    """
    filter convert ["xxx","yyy"] to ["xxx","","yyy","","","General","Pass"]
    """
    def __init__(self, column6, column7):
        self.column6 = column6
        self.column7 = column7


    def run(self, list):
        return [list[0],"",list[1],"","",self.column6,self.column7]

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

class PrefixChainFilter (BaseChainFilter):
    """
    filter that searches prefix in second section before /
    add move in into other group
    """
    def __init__(self, chain,prefix):
        super(PrefixChainFilter,self).__init__(chain)
        self.prefix = prefix

    def runInside(self, list):
        slashIndex = list[0].find('/')
        if slashIndex!=-1:
            firstPart = list[0][:slashIndex]
            if firstPart == self.prefix:
                logging.debug('Find prefix '+self.prefix+' into '+list[0])
                list[0] = list[0][slashIndex+1:]
                list[5] = firstPart
                return list


class UsernameChainFilter (BaseChainFilter):
    """
    filter that searches username in last section after /
    add move it into other column
    """
    def __init__(self, chain,usernameSubstring):
        super(UsernameChainFilter,self).__init__(chain)
        self.usernameSubstring = usernameSubstring

    def runInside(self, list):
        slashIndex = list[0].rfind('/')
        if slashIndex!=-1:
            lastPart = list[0][slashIndex+1:]
            if lastPart.find(self.usernameSubstring)!=-1:
                logging.debug('Find username '+self.usernameSubstring+' into '+lastPart)
                list[1] = lastPart
                list[0] = list[0][:slashIndex]
                return list


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
        if (len(splitFirstPart)!=2 or splitFirstPart[0]=="" or splitFirstPart[0].find('.')==-1):
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
    parser = argparse.ArgumentParser(
        usage="pass_to_csv [-h] [-v] -6 General -7 Pass [-u user] ... [-u user] [-p prefix] [-p prefix]",
                                     description="Export from passwordstore.org storage to csv file")
    parser.add_argument('-6','--column6',help='default value for column 6')
    parser.add_argument('-7','--column7',help='default value for column 7')
    parser.add_argument('-u','--username',help='substring for check username existing',action='append')

    parser.add_argument('-v','--verbose',help='show verbose information',action='store_true')
    parser.add_argument('-p','--prefix',help='prefix of name for selecting groups',action='append')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
    directory_prefix = home+'/.password-store'
    try:
        csvfile = csv.writer(sys.stdout)
        chain = DropSlashFilter (identityFunctor())
        #test for username
        if (args.username):
            for u in args.username:
                chain = UsernameChainFilter(chain,u)
        if (args.prefix):
            for p in args.prefix:
                chain = PrefixChainFilter(chain,p)
        chain = URLChainFilter(chain)
        chain = URLWithoutUsernameChainFilter(chain)


        scandir("", directory_prefix,
                filterWithFunctor(csvfile,
                DotFilters(PrepareFilter(args.column6,args.column7),chain)))

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
