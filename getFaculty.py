import urllib2
import re
import pickle
from bs4 import BeautifulSoup

url = "http://whitepages.tufts.edu/structuredetails.cgi?Faculty/Staff+ou=School%20of%20Arts,%20Sciences,%20and%20Engineering"

def getFaculty():
    faculty = []
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    depts = soup.findAll('a', href=re.compile('department.?'))
    for dept in depts:
        department = dept.string
        department = department.strip('\ ;')
        deptURL = 'http://whitepages.tufts.edu/'+dept['href']
        deptSoup = BeautifulSoup(urllib2.urlopen(deptURL).read())
        people = deptSoup.findAll('a',href=re.compile('ldapentry.?'))
        department = re.sub('\ *-\ *A&S', '', department)
        for p in people:
            name = str(p.string.encode('utf-8'))
            person = {'department':department,
                      'name':name,
                      'aliases':mixNames(name)}
            faculty.append(person)
    return faculty

def mixNames(name):
    halfSplitname = re.split(', ', name)
    lastname = halfSplitname[0]
    splitname = re.split(' ', halfSplitname[1])
    firstname = splitname[0]
    re.sub('.', '', firstname)
    splitname.pop(0)

    istring = ""
    istring1 = ""
    for initial in splitname:
        initial = re.sub('[(.)]', '', initial)
        if initial != "":
            istring += initial + " "
            istring1 += initial[0] + " "

    mixedNames = []
    mixedNames.append(firstname + " " + lastname)
    if istring != "":
        mixedNames.append(firstname + " " + istring  + lastname)
        if istring1 != istring:
            mixedNames.append(firstname + " " + istring1 + lastname)
    if firstname != firstname[0]:
        mixedNames.append(firstname[0] + " " + lastname)
        if istring != "":
            mixedNames.append(firstname[0] + " " + istring  + lastname)
            if istring1 != istring:
                mixedNames.append(firstname[0] + " " + istring1 + lastname)

    return mixedNames

faculty = getFaculty()
f = open('pickledFaculty.txt', 'wb')
pickle.dump(faculty, f)
