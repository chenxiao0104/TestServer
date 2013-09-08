import multiprocessing
import time
import os
import subprocess
from CommonInfo import *
from BvtTest import *

class TestController(multiprocessing.Process):
    def __init__(self,waitList,runList,tLock):
        multiprocessing.Process.__init__(self)
        self.waitTaskList = waitList
        self.runTaskList = runList
        self.taskLock = tLock
        self.taskQueue = multiprocessing.Queue()
        #self.androidRun = False
        #self.iosRun = False
        self._RUN_INTERVAL = 3
        
    def changeWaitTaskStatus(self,info):
        self.taskLock.acquire()
        info.taskStatus = CommonInfo._TESTCASE_RUNNING
        self.runTaskList.append(info)
        index = 0
        for e in self.waitTaskList:
            if(e.taskId == info.taskId):
                break
            index += 1
        del self.waitTaskList[index]
        self.taskLock.release()
        
    def changeRunTaskStatus(self,info):
        self.taskLock.acquire()
        index = 0
        for eachTask in self.runTaskList:
            if(eachTask.taskId == info.taskId):
                break
            index += 1
        if(index<len(self.runTaskList)):
            del self.runTaskList[index]
            info.taskStatus = CommonInfo._TESTCASE_FINISH
            self.runTaskList.append(info)
        self.taskLock.release()
    
    '''
    处理已经完成任务
    '''
    def handleAccomplishTask(self):
        while (self.taskQueue.empty()==False):
            info = self.taskQueue.get()
            '''
            if(info.operPlatform == CommonInfo._OPER_ANDROID):
                self.androidRun = False
            elif(info.operPlatform == CommonInfo._OPER_IOS):
                self.iosRun = False
                '''
            self.changeRunTaskStatus(info)
            #self.delFile(info)
        
    def run(self):
        print('Test Controller start.')
        while True:
            time.sleep(self._RUN_INTERVAL)
            #print('Let me check.')
            self.handleAccomplishTask()
            if(self.waitTaskList == []):
                print("No Case to be running.")
                continue
            
            self.taskLock.acquire()
            for eachTask in self.waitTaskList:
                #only one android or ios test can run
                '''
                if(eachTask.operPlatform == CommonInfo._OPER_ANDROID):
                    if(self.androidRun == False):
                        self.androidRun = True
                    else:
                        continue
                if(eachTask.operPlatform == CommonInfo._OPER_IOS):
                    if(self.iosdRun == False):
                        self.iosRun = True
                    else:
                        continue
                        '''
                if(eachTask.recvStatus == True):
                    self.changeWaitTaskStatus(eachTask)
                    bvtTest = BvtTest(eachTask,self.taskQueue)
                    bvtTest.start()
            self.taskLock.release()
    
    def delFile(self,info):
        if(info.binaryPath != None):
            dirPath = os.path.dirname(info.binaryPath)
        delCmd = "rd /S /Q "+dirPath
        ret = subprocess.call(delCmd,shell=True)
        print("delete "+dirPath)