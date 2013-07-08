#! /usr/bin/env python

import os, os.path
import xml.parsers.expat
import platform


CLASSPATH = 'CLASSPATH'
JAVA_HOME = 'JAVA_HOME'
VARIABLE_MAPPING_FILE = '.metadata/.plugins/org.eclipse.core.runtime/.settings/org.eclipse.jdt.core.prefs'
VARIABLE_PREFIX = 'org.eclipse.jdt.core.classpathVariable'

class State:
    def __init__(self, variableMapping, isVerbose, dependent_projects):
        self.values = []
        self.projects = []
        self.isVerbose = isVerbose or False
        self.variableMapping = variableMapping
        self.dependent_projects = self.__extract_dependent_projects(dependent_projects)
        if self.isVerbose:
            print "=========  Variable Mappings ======="
            for (key, value) in self.variableMapping.items():
                print '%s : %s' % (key, value)
            for (name, location) in self.dependent_projects.items():
                print '%s => %s' % (name, location)
            print "===================================="
        
    def __extract_dependent_projects(self, dependent_projects):
        result = {}
        for project in dependent_projects:
            (name, location) = project.split(':')
            result[name.strip()] = location.strip()
        return result

    def isDependent(self, project):
        return project in self.dependent_projects

    def getDependent(self, project):
        return self.dependent_projects[project]
    
    def addProject(self, project):
        if project not in self.projects:
            self.projects.append(project)
            return True
        else:
            return False
        
    def getVariable(self, variable):
        return self.variableMapping[variable]
    
    def append(self, value):
        if platform.system() == 'Windows':
            value = value.replace('/', '\\')
            value = value.replace('C\\:', 'C:')
        if value not in self.values:
            if self.isVerbose:
                print "Adding entry : %s" % value
            self.values.append(value)
        else:
            if self.isVerbose:
                print "Ignoring entry (duplicate) : %s" % value
            
    def __repr__(self):
        return str(self.values)
    
def handleVar(attrs, state):
    vals = attrs['path'].split('/', 1)
    newValue = state.getVariable(vals[0])
    newPath = os.path.join(newValue, vals[1])
    state.append(newPath)
    
def handleSrc(attrs, state, dir):
    if attrs.has_key('output'):
        state.append(os.path.join(dir, attrs['output']))
    elif attrs['path'].startswith('/'):
        name = attrs['path'][1:]
        if state.isDependent(name):
            path = state.getDependent(name)
        else:
            path = os.path.join(dir, '..', attrs['path'][1:])
            path = os.path.abspath(path)
        processProject(path, state)

def makeHandlers(state, dir):
    handlers = {}
    handlers['var'] = lambda attrs : handleVar(attrs, state)
    handlers['output'] = lambda attrs : state.append(os.path.join(dir, attrs['path']))
    handlers['lib'] = lambda attrs : state.append(os.path.join(dir, attrs['path']))
    handlers['con'] = lambda attrs : ()
    handlers['src'] = lambda attrs : handleSrc(attrs, state, dir)
    
    return handlers

def startElement(name, attrs, handlers):
    if 'classpathentry' == name:
        handlers[attrs['kind']](attrs)

def processProject(dir, state):
    dir = os.path.abspath(dir)
    if state.isVerbose:
        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'

    if not state.addProject(dir):
        if state.isVerbose:
            print 'Project ignored (already processed) : %s' % dir
    else:
        if state.isVerbose:
            print 'Processing project = %s' % dir
        filename = os.path.join(dir, '.classpath')
        handlers = makeHandlers(state, dir)
        f = open(filename)
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = lambda name, attrs : startElement(name, attrs, handlers)
        parser.Parse(f.read())
    if state.isVerbose:
        print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<< : %s" % dir



class NoVariableMappingsError(Exception):
    def __init__(self, workspaceDir):
        self.workspace = workspaceDir

    def __str__(self):
        return 'Invalid workspace directory "%s" could not find the variable mapping file "%s"' % (self.workspace, VARIABLE_MAPPING_FILE)

def getVariableMappings(workspaceDir):
    try:
        file = open(os.path.join(workspaceDir, VARIABLE_MAPPING_FILE), 'r')
    except IOError, e:
        raise NoVariableMappingsError(workspaceDir)
    
    mapping = {}
    for line in file:
        if line.startswith(VARIABLE_PREFIX):
            tmp = line.split('=')
            key = tmp[0].rsplit('.', 1)[1].strip()
            value = tmp[1].strip()
            mapping[key] = value
    return mapping

def splitArgs(args):
    if len(args) < 2:
        raise 'No -exec command found'

    # Separate my arguments from the java arguments
    index = 1
    while index < len(args):
        arg = args[index]
        if arg.strip() == '-exec':
            break
        index += 1
    myargs = args[:index]
    progargs = args[index+1:]
    return (myargs, progargs)

def parseOpts(myargs):
    from optparse import OptionParser
    parser = OptionParser()

    # Define command line arguments for the script
    parser.add_option('-p', '--project', default='.', help='set the Eclipse project directory : default - "."')
    parser.add_option('-P', '--dependent_project', action='append', default=[], help='add a path for dependent project in the form "project-name:path"')
    parser.add_option('-w', '--workspace', help="set the Eclipse workspace directory : default - parent of project directory")
    parser.add_option('-v', '--verbose', action='store_true', help="provides information about the processing")

    # define arguments to control how java is run
    parser.add_option('-A',  dest='assertions_off', action='store_true', help="turn off java assertions")
    parser.add_option('-c',  dest='extra_classpath', action='append', default=[], help="Add additional classpath entries (added to front of classpath)")
    parser.add_option('-S',  dest='sys_properties', action='append', default=[], help="Add system properties to the java execution (adds a -D value to the java exec command)")
    parser.add_option('-m', '--memory', type='int', default=512, help="set the java's max memory : default - 512")
    parser.add_option('-d', '--debug', action='store_true', help="start java with remote debugging")
    parser.add_option('-t', '--jdwp-transport', dest='transport', default='dt_socket',  help="the jdwp transport : default - dt_socket")
    parser.add_option('-a', '--jdwp-address', dest='address', type='int', default='8000',  help="the jdwp address : default - 8000")
    parser.add_option('-s', '--jdwp-suspend', dest='suspend', action='store_const', const='y', help="if debugging, suspend at start up until debugger is attached")
    parser.add_option('-V', '--variable-mapping', dest='mappings', action='append', help="override an eclipse variable mapping")
    

    # process command line arguments
    (options, args) = parser.parse_args(myargs)
    
        
    return options

def main(options, progArgs):
    projectDir = options.project
    workspaceDir = options.workspace
    isVerbose = options.verbose
    isDebug = options.debug
    
    if not workspaceDir:
        workspaceDir = os.path.join(projectDir, '..')

    if isVerbose:
        print "-----------------------------"
        print "Workspace directory : %s" % workspaceDir
        print "Project directory   : %s" % projectDir
        print "-----------------------------"
    variableMapping = getVariableMappings(workspaceDir)
    
    if options.mappings:
        for varMapping in options.mappings:
            vmValue = varMapping.split('=')
            variableMapping[vmValue[0]] = vmValue[1] 
    
    # parse the classpath from eclipse files
    state = State(variableMapping, isVerbose, options.dependent_project)
    processProject(projectDir, state)
  
    # add the classpath to the environment
    classpath = os.pathsep.join(state.values)
    if state.isVerbose:
        print "=============================================="
        print "Final Classpath:"
        print classpath
        print "=============================================="
    if os.environ.has_key(CLASSPATH):
        classpath = os.environ[CLASSPATH] + classpath
    extra_paths = os.pathsep.join(options.extra_classpath)
    classpath = os.pathsep.join((extra_paths, classpath))
    os.putenv(CLASSPATH, classpath)

    cmd = 'java'
    if os.environ.has_key(JAVA_HOME):
        cmd = '"%s/bin/java"' % os.environ[JAVA_HOME]

    for sysprop in options.sys_properties:
        cmd = '%s -D%s' % (cmd, sysprop)
    cmd = '%s -Xmx%sM' % (cmd, options.memory)
    if os.environ.has_key('JAVA_OPTS'):
        cmd = '%s %s' % (cmd, os.environ['JAVA_OPTS'])
    if not options.assertions_off:
        cmd = '%s %s'% (cmd, '-ea')
     
    if isDebug:
        suspend = options.suspend or 'n'
        debug_params = '-Xdebug -Xrunjdwp:transport=%s,address=%s,server=y,suspend=%s' % (options.transport, options.address, suspend)
        cmd = '%s %s' % (cmd, debug_params)
        
    cmd = '%s %s' % (cmd, ' '.join(progArgs))
    
    if state.isVerbose:
        print '\n\n======================================='
        print "Running command:"
        print cmd
        print '=======================================\n\n'
    return os.system(cmd)
    

if __name__ == '__main__':
    import sys
    
    (myargs, progargs) = splitArgs(sys.argv)
    options = parseOpts(myargs)
    retval = main(options, progargs)
    print "eclipserunner ret = " + str(retval)
    sys.exit(1)
