EclipseRunner
=============

From a terminal, run a java program located in an Eclipse project without having 
to build a jar.  You can use this to plug into the unix command piping.


  Usaage (Note options before '-exec' are options for this script, options after 
  are passed the java script:
  
  EclipseRunner.py [options] -exec {java command line here}

  Options:
  
    -h, --help            show this help message and exit
    -p PROJECT, --project=PROJECT
                          set the Eclipse project directory : default - "."
    -P DEPENDENT_PROJECT, --dependent_project=DEPENDENT_PROJECT
                          add a path for dependent project in the form "project-
                          name:path"
    -w WORKSPACE, --workspace=WORKSPACE
                          set the Eclipse workspace directory : default - parent
                          of project directory
    -v, --verbose         provides information about the processing
    -A                    turn off java assertions
    -c EXTRA_CLASSPATH    Add additional classpath entries (added to front of
                          classpath)
    -O JAVA_OPTIONS       Add a java option. (i.e. to set -Xmx1024M on the java
                          execution you would use -O Xmx1024M or to set a system
                          property -Dname=value you would use -O Dname=value)
    -S SYS_PROPERTIES     Add system properties to the java execution (adds a -D
                          value to the java exec command)
    -m MEMORY, --memory=MEMORY
                          set the java's max memory : default - 512
    -d, --debug           start java with remote debugging
    -t TRANSPORT, --jdwp-transport=TRANSPORT
                          the jdwp transport : default - dt_socket
    -a ADDRESS, --jdwp-address=ADDRESS
                          the jdwp address : default - 8000
    -s, --jdwp-suspend    if debugging, suspend at start up until debugger is
                          attached
    -V MAPPINGS, --variable-mapping=MAPPINGS
                          override an eclipse variable mapping

  
  Examples: 
  
  Run fully.qualified.Classname
  
    EclipseRunner.py -exec fully.qualified.ClassName --script-option1 1 --script-option2 2
    
  Run remote debugger, suspending and waiting for debugger to attach, on class fully.qualified.Classname

    EclipseRunner.py -d -s -exec fully.qualified.ClassName --script-option1 1 --script-option2 2
    
  

