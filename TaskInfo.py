'''
Created on Aug 5, 2013

@author: t-xche
'''
from CommonInfo import *

class TaskInfo:
    def __init__(self):
        self.taskId = None
        #self.clientSock = None
        self.binaryPath = None
        self.operPlatform = None
        self.taskStatus = CommonInfo._TESTCASE_WAITING
        self.recvStatus = False
        self.testResult = None
        self.outputDir = CommonInfo.outputDir
        #self.outputDir = "C:\\bvttest\\testOutput\\"