import urllib
import urllib2
import re
import csv
import pickle
from xml.dom import minidom
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

baseURL = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
database = "pubmed"

def parseXMLForIDs(data):
    xmldoc = minidom.parseString(data)
    ids = xmldoc.getElementsByTagName('Id')
    return set(map(lambda id: str(id.childNodes[0].nodeValue), ids))

def getCount(term):
    params = {'db':database,
              'term':term,
              'retmode':'xml'}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    xmldoc = minidom.parseString(data)
    return xmldoc.getElementsByTagName('Count')[0].childNodes[0].nodeValue

def IDsForAuthor(author):
    term = author + '[Author]'
    params = {'db':database,
              'term':term,
              'retmode':'xml',
              'retmax':getCount(term)}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    return parseXMLForIDs(data)

def IDsForAuthorWithMax(author, maxResults):
    params = {'db':database,
              'term':author+'[author]',
              'retmode':'xml',
              'retmax':str(maxResults)}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    return parseXMLForIDs(data)

def IDsForAuthorWithAffiliation(author, affiliation):
    term = author+'[Author] AND '+affiliation+'[Affiliation]'
    params = {'db':database,
              'term':term,
              'retmode':'xml',
              'retmax':getCount(term)}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    return parseXMLForIDs(data)

def IDsForAuthorWithAffiliationWithMax(author, affiliation, maxResults):
    term = author+'[Author] AND '+affiliation+'[Affiliation]'
    params = {'db':database,
              'term':term,
              'retmode':'xml',
              'retmax':str(maxResults)}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    return parseXMLForIDs(data)

def dataForID(id):
    params = {'db':database,
              'id':id,
              'retmode':'xml'}
    url = baseURL + urllib.urlencode(params)
    data = urllib.urlopen(url).read()
    return data

def getAliasesFromFile(filename):
    f = open(filename, 'r')
    people = f.readlines()
    del people[-1]
    authorAliasList = []
    for p in people:
        names = p.strip("\n").split("\t")
        authorAliasList.append(names)
    return authorAliasList

def getIDsForAliases(facultyList, affiliation):
    listOfIDSets = []
    i = 0
    for person in facultyList:
        listOfIDSets.append(set())
        for alias in person['aliases']:
            IDs_affil = IDsForAuthorWithAffiliation(alias, affiliation)
            listOfIDSets[i] = listOfIDSets[i].union(IDs_affil)
        print "Done with " + facultyList[i]['name']
        i += 1
    return listOfIDSets

def computeConnections(listOfIDSets):
    i = 0
    connections = []
    for s in listOfIDSets:
        temp = []
        for j in range(len(listOfIDSets)):
            if (i!=j and not s.isdisjoint(listOfIDSets[j])):
                weight = len(s.intersection(listOfIDSets[j]))
                temp.append([j, weight])
        connections.append(temp)
        i += 1
    return connections

def makeGraph(connections):
    graph = map(lambda s: list(s), connections)
    return graph

def writeGraph(graph, nodesFile, edgesFile):

    # Nodes
    i = 0
    writer = csv.writer(open(nodesFile, 'w'))
    writer.writerow(['ID', 'Name', 'Department'])
    for i in range(len(graph)):
        writer.writerow([i, faculty[i]['name'], faculty[i]['department']])

    # Edges
    edges = []
    i = 0
    for s in graph:
        for x in s:
            edges.append([i, x[0], 'Undirected', x[1]])
        i += 1
    writer = csv.writer(open(edgesFile, 'w'))
    writer.writerow(['Source', 'Target', 'Type', 'Weight'])
    i = 0
    for e in edges:
        writer.writerow(e)
        i += 1

#faculty = getFaculty()
faculty = pickle.load(open('pickledFaculty.txt', 'rb'))
#mathfac = filter(isGoodDepartment, faculty)
#listOfIDSets = getIDsForAliases(faculty, 'Tufts')
#IDFile = open('pickledIDs.txt', 'wb')
#pickle.dump(listOfIDSets, IDFile)
listOfIDSets = pickle.load(open('pickledIDs.txt', 'rb'))
connections = computeConnections(listOfIDSets)
writeGraph(connections, "nodes_affil_weights.csv", "edges_affil_weights.csv")

goodDepartments = ["American Studies",
                   "Anthropology",
                   "Art and Art History",
                   "Biology",
                   "Biomedical Engineering",
                   "Chemical Engineering",
                   "Chemisty",
                   "Child Development",
                   "Civil & Envir Engineering",
                   "Classics",
                   "Community Health",
                   "Computer Science",
                   "Drama and Dance",
                   "Economics",
                   "Education",
                   "Electrical & Computer Engineer",
                   "English",
                   "Geology"] # etc...

