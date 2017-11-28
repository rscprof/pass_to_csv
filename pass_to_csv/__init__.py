#/usr/bin/python
"""
Export from password.store to csv file
"""

import os
import logging
import sys
import subprocess
import csv
import codecs
import argparse
import gettext

import gettext
gettext.install('pass_to_csv')



class PrepareFilter:
    """
    filter convert ["xxx", "yyy"] to ["xxx", "", "yyy", "", "", "General", "Pass"]
    """
    def __init__(self, column6, column7):
        self.column6 = column6
        self.column7 = column7


    def run(self, listpass):
        """
        run filter
        """
        return [listpass[0], "", listpass[1], "", "", self.column6, self.column7]

class DotFilters:
    """
    composion of two filters
    """
    def __init__(self, filter1, filter2):
        self.filter1 = filter1
        self.filter2 = filter2

    def run(self, listpass):
        """
        run filter
        """
        return self.filter2.run(self.filter1.run(listpass))

class BaseChainFilter(object):
    """
    This is the abstract base class for
    chain of responsibility of filters

    Only one filter must be used

    The method runinside of it must return not None

    """
    def __init__(self, chain):
        self.chain = chain

    def runinside(self, listpass):
        """
        This is the method only for override
        """
        return listpass

    def run(self, listpass):
        """
        run filter
        """
        result = self.runinside(listpass)
        if result is None:
            return self.chain.run(listpass)
        return result

class PrefixChainFilter(BaseChainFilter):
    """
    filter that searches prefix in second section before /
    add move in into other group
    """
    def __init__(self, chain, prefix):
        super(PrefixChainFilter).__init__(chain)
        self.prefix = prefix

    def runinside(self, listpass):
        slashindex = listpass[0].find('/')
        if slashindex != -1:
            firstpart = listpass[0][:slashindex]
            if firstpart == self.prefix:
                logging.debug('Find prefix '+self.prefix+' into '+listpass[0])
                listpass[0] = listpass[0][slashindex+1:]
                listpass[5] = firstpart
                return listpass


class UsernameChainFilter(BaseChainFilter):
    """
    filter that searches username in last section after /
    add move it into other column
    """
    def __init__(self, chain, usernamesubstring):
        super(UsernameChainFilter).__init__(chain)
        self.usernamesubstring = usernamesubstring

    def runinside(self, listpass):
        """
        find usernameSubstring in last part of listpath[0] and if it exists then
        username moves to other item of array
        """
        slashindex = listpass[0].rfind('/')
        if slashindex != -1:
            lastpart = listpass[0][slashindex+1:]
            if lastpart.find(self.usernamesubstring) != -1:
                logging.debug('Find username '+self.usernamesubstring+' into '+lastpart)
                listpass[1] = lastpart
                listpass[0] = listpass[0][:slashindex]
                return listpass


class DropSlashFilter(BaseChainFilter):
    """
    filter that deletes / in front of string
    """
    def runinside(self, listpass):
        if listpass[0][0:1] == '/' and listpass[0].find('/', 1) == -1:
            listpass[0] = listpass[0][1:]
            return listpass



class URLWithoutUsernameChainFilter(BaseChainFilter):
    """
    filter that converts ["/xxx.yyy", "", "zzz", "", ""] into ["xxx.yyy", "", "zzz", "xxx.yyy", ""]
    """
    def runinside(self, listpass):
        name = listpass[0]
        if (name[0:1] == '/')and(name[1:].find('.') > 0):
            listpass[0] = name[1:]
            listpass[3] = name[1:]
            return listpass


class URLChainFilter(BaseChainFilter):
    """
    filter that convert ["xxx/yyy", "", "zzz", "", ""] into ["yyy", "yyy", "zzz", "xxx", ""]
    if it is imposiible then filter start chain filter
    """
    def runinside(self, listpass):
        name = listpass[0]
        splitfirstpart = name.split('/')
        if len(splitfirstpart) != 2 or splitfirstpart[0] == "" or splitfirstpart[0].find('.') == -1:
            return None
        listpass[0] = splitfirstpart[0]
        listpass[1] = splitfirstpart[1]
        listpass[3] = splitfirstpart[0]
        return listpass



class IdentityFunctor:
    """
        functor that return his argument
    """
    def run(self, arg):
        """
        identity function :-)
        """
        return arg

class FilterWithFunctor:
    """
    This is class-adapter of csv, that use functor to do
    with array (name, password)
    """
    def __init__(self, parentcsv, functor):
        self.parentcsv = parentcsv
        self.functor = functor

    def writerow(self, arg):
        """
        save the arg, that went through function
        """
        self.parentcsv.writerow(self.functor.run(arg))

class FilterExample:
    """
    This is an example of class-adapter for csv
    """
    def __init__(self, parentcsv):
        self.parentcsv = parentcsv

    def writerow(self, arg):
        """
        Only save to csv
        """
        self.parentcsv.writerow(arg)

def main():
    """
    Main function in program
    """
    home = os.environ['HOME']
    parser = argparse.ArgumentParser(
        usage=
        _('pass_to_csv [-h] [-v] -6 General -7 Pass [-u user] ... [-u user] [-p prefix] [-p prefix]'),
        description=_('Export from passwordstore.org storage to csv file'))
    parser.add_argument('-6', '--column6', help=_('default value for column 6'))
    parser.add_argument('-7', '--column7', help=_('default value for column 7'))
    parser.add_argument('-u', '--username',
                        help=_('substring for check username existing'), action='append')


    parser.add_argument('-v', '--verbose', help=_('show verbose information'), action='store_true')
    parser.add_argument('-p', '--prefix',
                        help=_('prefix of name for selecting groups'), action='append')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    directory_prefix = home+'/.password-store'
    try:
        csvfile = csv.writer(sys.stdout)
        chain = DropSlashFilter(IdentityFunctor())
        #test for username
        if args.username:
            for username in args.username:
                chain = UsernameChainFilter(chain, username)
        if args.prefix:
            for prefix in args.prefix:
                chain = PrefixChainFilter(chain, prefix)
        chain = URLChainFilter(chain)
        chain = URLWithoutUsernameChainFilter(chain)


        scandir("", directory_prefix,
                FilterWithFunctor(csvfile,
                                  DotFilters(PrepareFilter(args.column6, args.column7), chain)))

    except FileNotFoundError as err:
        if err.filename == directory_prefix:
            print(_('Password storage doesn\'t exist'))
        else:
            raise err


def scandir(directory, directory_prefix, writer):

    """
    scan directory in password storage, that keep in directory_prefix
    and store results in writer by method writerow by sending array with
    two elements: name and password

    :param directory: name of directory inside password storage
    :param directory_prefix: directory where password storage is
    :param writer: object, that gets all pairs of name and passwords
    """

    result = []
    path = directory_prefix
    if directory != '':
        path += '/'+directory
    for filestruct in os.scandir(path):
        if filestruct.is_dir():
            if filestruct.name != '.git':
                logging.debug('scanning directory '+filestruct.name)
                newdirectory = directory
                if directory != '':
                    newdirectory += '/'
                newdirectory += filestruct.name
                result = result + scandir(newdirectory, directory_prefix, writer)
        elif filestruct.is_file() and filestruct.name[-4:] == '.gpg':
            logging.debug('scanning file '+filestruct.name)
            name = directory+'/'+filestruct.name[:-4]
            password = subprocess.run(['pass', name], stdout=subprocess.PIPE)
            if password.returncode == 0:
                writer.writerow([name, password.stdout.rstrip().decode("utf-8")])
            else:
                sys.exit('Cannot get the password for ' +
                         directory + '/' + filestruct.name)
    return result


if __name__ == "__main__":
    # execute only if run as a script
    main()
