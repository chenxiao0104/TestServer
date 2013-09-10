from HandleMsg import *
from TaskInfo import *
from CommonInfo import *
from BvtTest import *
import os
import time
import multiprocessing
import subprocess

class ServerCom:
    def __init__(self):
        self.maxTaskId = 0
        self.runTaskList = []
        self.waitTaskList = []
        self.taskDic = {}
        self.taskQueue = multiprocessing.Queue()
        self.handleMsg = HandleMsg()
        now = time.localtime(time.time())
        self.day = now.tm_mday
        self.month = now.tm_mon
        self.year = now.tm_year
        self.androidFlag = True
        self.androidTimer = 0
        self.androidTaskInfo = None
        
    def sendMsg(self,msg,serverSock):
        length = len(msg)
        if(length<=0):
            return
        elif(length>CommonInfo._SOCK_SIZE):
            print("[BUG: msg length is greater than design size-",CommonInfo._SOCK_SIZE,"]")
            msg = msg.encode('ascii')
            serverSock.send(msg)
        else:
            tailSize = CommonInfo._SOCK_SIZE - length
            msg += '\0'*tailSize
            msg = msg.encode('ascii')
            serverSock.send(msg)
        
    def parseMsgType(self,jsonMsg):
        msgType = jsonMsg.get("msgType")
        return msgType
        
    def findTaskById(self,taskId):
        flag = False
        for eachTask in self.waitTaskList:
            if(eachTask.taskId == taskId):
                findInfo = eachTask
                flag = True
                break      
        if(flag==False):
            for eachTask in self.runTaskList:
                if(eachTask.taskId == taskId):
                    findInfo = eachTask
                    flag = True
                    break
        if(flag):  
            return findInfo
        else:
            return None
        
    def findTaskByMsg(self,jsonMsg):
        taskId = jsonMsg.get("taskId")
        taskInfo = self.findTaskById(taskId)
        return taskInfo
    
    def deleteTask(self,info,flag):
        try:
            if(flag==1):
                self.waitTaskList.remove(info)
            elif(flag==2):
                self.runTaskList.remove(info)
        except:
            pass
        
    def sendTaskReqAck(self,clientSock,taskInfo):
        msg = self.handleMsg.createTaskReqAck(taskInfo.taskId)
        self.sendMsg(msg, clientSock)
        #print(taskInfo.taskId,' send task ack')
        
    def sendAppRecvAck(self,recvTask,recvStatus,clientSock):
        taskId = recvTask.taskId
        msg = self.handleMsg.createAppRecvAck(taskId, recvStatus)
        self.sendMsg(msg, clientSock)
        print("[LOG: %s send app recv ack.]" %(recvTask.taskId,))
        
    def sendTaskStatusAck(self,clientSock,taskInfo):
        msg = self.handleMsg.createTaskStatusAck(taskInfo.taskId, taskInfo.taskStatus)
        self.sendMsg(msg, clientSock)
        print("[LOG: %s send task status ack.]" %(taskInfo.taskId,))
        if(taskInfo.taskStatus==CommonInfo._TESTCASE_FAIL):
            if(taskInfo in self.waitTaskList):
                self.waitTaskList.remove(taskInfo)
            elif(taskInfo in self.runTaskList):
                self.runTaskList.reomve(taskInfo)
            try:
                del self.taskDic[clientSock]
            except:
                pass
            return False
        return True
        
    def sendTestResult(self,clientSock,taskInfo):
        logPath = taskInfo.outputDir+os.path.sep+taskInfo.taskId+os.path.sep+"output.txt"
        if(os.path.exists(logPath)):
            fileSize = os.path.getsize(logPath)
        else:
            fileSize = 0
        msg = self.handleMsg.createTestResult(taskInfo,fileSize)
        self.sendMsg(msg, clientSock)
        print("[LOG: %s send test result.]" %(taskInfo.taskId,))
        if(taskInfo.testResult==CommonInfo._TESTRESULT_PASS or taskInfo.testResult==CommonInfo._TESTRESULT_FAIL):
            self.sendOutputfile(taskInfo, clientSock)
            print("[LOG: %s send outputfile.]" %(taskInfo.taskId,))
        
    def sendOutputfile(self,taskInfo,serverSock):
        logPath = taskInfo.outputDir+os.path.sep+taskInfo.taskId+os.path.sep+"output.txt"
        if(os.path.exists(logPath)):
            fileSize = os.path.getsize(logPath)
        else:
            fileSize = 0
            print("[ERROR: %s output.txt not exists.]" %(taskInfo.taskId,))
            return
        try:
            fp = open(logPath,"rb")
        except:
            print("[ERROR: %s open output.txt fail.]" %(taskInfo.taskId,))
        try:
            outputStr = fp.read(fileSize)
            serverSock.send(outputStr)
        except:
            print("[ERROR: %s read output.txt fail.]" %(taskInfo.taskId,))
            
        
    def handleTaskReq(self,jsonMsg,clientSock):
        newTask = TaskInfo()
        now = time.localtime(time.time())
        if(self.day!=now.tm_mday or self.month!=now.tm_mon or self.year!=now.tm_year):
            self.day = now.tm_mday
            self.month = now.tm_mon
            self.year = now.tm_year
            self.maxTaskId = 0
        taskId = str(self.year)+'_'+str(self.month)+'_'+str(self.day)+'_'+str(self.maxTaskId+1)
        self.taskDic[clientSock] = taskId
        print("[LOG: new task is %s.]" %(taskId,))
        self.maxTaskId += 1
        newTask.taskId = taskId

        oper = jsonMsg.get("operPlatform")
        newTask.operPlatform = oper
        if(newTask.operPlatform == CommonInfo._OPER_WINI386 or newTask.operPlatform == CommonInfo._OPER_WINRTARM7 or\
           newTask.operPlatform == CommonInfo._OPER_WINRTI386 or newTask.operPlatform == CommonInfo._OPER_WINRTX64 or\
           newTask.operPlatform == CommonInfo._OPER_BLUEI386 or newTask.operPlatform == CommonInfo._OPER_BLUEX64):
            extName = '.exe'
        elif (newTask.operPlatform == CommonInfo._OPER_ANDROID):
            extName = '.apk'
        else:
            extName = ''

        fileDir = CommonInfo.binaryDir+os.path.sep+newTask.taskId
        if(os.path.exists(fileDir)==False):
            os.mkdir(fileDir)
        filePath = fileDir+'\\bvttest'+extName
        newTask.binaryPath = filePath
        newTask.recvStatus = False
        self.waitTaskList.append(newTask)
        return newTask
        
    def handleAppReady(self,recvTask,clientSock):
        filePath = recvTask.binaryPath
        try:
            recvFile = open(filePath,'wb')
        except:
            self.deleteTask(recvTask, 1)
            return False
        
        _RECV_SIZE = 4096
        print("[LOG: ",recvTask.taskId,' begin to recv file]')
        while True:
            try:
                msg = clientSock.recv(_RECV_SIZE)
                if(len(msg)==0):
                    print('[WARN: recv client FAIL]')
                    self.deleteTask(recvTask, 1)
                    return False
                recvFile.write(msg)
            except:
                break
            
        recvFile.close()
        recvTask.recvStatus = True
        print("[LOG: ",recvTask.taskId,' recv file OK]')
        return True
        
    def handleTaskStatusReq(self,jsonMsg):
        taskId =jsonMsg.get("taskId")
        taskInfo = self.findTaskById(taskId)
        return taskInfo 
    
    def handleAccomplishTask(self):
        while (self.taskQueue.empty()==False):
            info = self.taskQueue.get()
            self.changeRunTaskStatus(info)
            #self.delFile(info)
        self.isAndroidRun()
        
    def testControl(self):
        #print('Test Controller start.')
        self.handleAccomplishTask()
        if(self.waitTaskList == []):
            #print("No Case to be running.")
            return
            
        for eachTask in self.waitTaskList:
            if(eachTask.recvStatus == True and eachTask.taskStatus == CommonInfo._TESTCASE_WAITING):
                len = os.path.getsize(eachTask.binaryPath)
                if(len==0):
                    print("[WARN: %s binary is not available.]" %(eachTask.taskId,))
                    self.changeFailTaskStatus(eachTask)
                else:
                    if(eachTask.operPlatform==CommonInfo._OPER_ANDROID):
                        if(self.androidFlag==False):
                            self.androidFlag = True
                            self.androidTimer = time.time()
                            self.androidTaskInfo = eachTask
                        else:
                            continue
                    print("[LOG: %s binary has the right size.]" %(eachTask.taskId,))
                    self.changeWaitTaskStatus(eachTask)
                    bvtTest = BvtTest(eachTask,self.taskQueue)
                    bvtTest.start()
            
    def changeWaitTaskStatus(self,info):
        info.taskStatus = CommonInfo._TESTCASE_RUNNING
        self.runTaskList.append(info)
        self.waitTaskList.remove(info)
        
    def changeRunTaskStatus(self,info):
        for eachTask in self.runTaskList:
            if(eachTask.taskId == info.taskId):
                eachTask.taskStatus = CommonInfo._TESTCASE_FINISH
                eachTask.testResult = info.testResult
                break
            
    def changeFailTaskStatus(self,info):
        info.taskStatus = CommonInfo._TESTCASE_FAIL
        
    def isAndroidRun(self):
        if(self.androidFlag==False or self.androidTaskInfo==None):
            return
        timeOut = 1800
        now = time.time()
        if((now-self.androidTimer)>timeOut):
            cleancmd=self.toolPath+os.path.sep+"adb.exe shell pm uninstall " + "com.microsoft.skype.sct"
            p = subprocess.Popen(cleancmd, shell=False)
            self.androidTaskInfo.taskStatus = CommonInfo._TESTCASE_TIMEOUT
            self.androidTaskInfo.testResult = CommonInfo._TESTRESULT_FAIL
            self.androidTaskInfo = None
            self.androidFlag = False
            p.wait()
            
        
    def delFile(self,info):
        if(info.binaryPath != None):
            dirPath = os.path.dirname(info.binaryPath)
        delCmd = "rd /S /Q "+dirPath
        ret = subprocess.call(delCmd,shell=True)
        print("delete "+dirPath)
    
    
    def closeNormal(self,info,serviceSock):
        try:
            self.runTaskList.remove(info)
        except:
            pass
        self.delFile(info)
        try:
            del self.taskDic[serviceSock]
        except:
            pass
        print("[LOG: close one case in normal]")
        
    def closeAbnormal(self,serviceSock):
        print("[WARN: close one case in abnormal]")
        taskId = self.taskDic.get(serviceSock)
        delTask = None
        flag = False
        index = 0
        for eachTask in self.waitTaskList:
            if(eachTask.taskId == taskId):
                delTask = eachTask
                flag = True
                break
            index += 1
        if(delTask!=None):
            del self.waitTaskList[index]
        if(flag==False):
            index = 0
            for eachTask in self.runTaskList:
                if(eachTask.taskId == taskId):
                    delTask = eachTask
                    flag = True
                    break
                index += 1
        if(delTask!=None):
            binaryDir = CommonInfo.binaryDir+os.path.sep+delTask.taskId
            outputDir = CommonInfo.outputDir+os.path.sep+delTask.taskId
            try:
                del self.runTaskList[index]
            except:
                pass
            if(os.path.exists(binaryDir)):
                try:
                    delCmd = "rd /S /Q "+binaryDir
                    ret = subprocess.call(delCmd,shell=True)
                except:
                    pass
            if(os.path.exists(outputDir)):
                try:
                    delCmd = "rd /S /Q "+outputDir
                    ret = subprocess.call(delCmd,shell=True)
                except:
                    pass
        try:
            del self.taskDic[serviceSock]
        except:
            pass

    
