'''
Created on Aug 5, 2013

@author: t-xche
'''
import CommonInfo
from HandleMsg import *
from ServerCom import *
from TaskInfo import *
import subprocess
import select
import socket
import time
import os

class MasterServer:
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.errputs = []
        self.timeout = 1
        self.serverCom = ServerCom()
        
    def createConnect(self):
        try:
            self.serverSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.serverSock.setblocking(False)
            serverAddr = (CommonInfo.ServerIp,CommonInfo.ServerPort)
            self.serverSock.bind(serverAddr)
            self.serverSock.listen(100)
            self.inputs.append(self.serverSock)
            print('[LOG: server start OK]')
            return True
        except:
            print('[ERROR: server start fail]')
            return False
        
    def arbiter(self):
        while True:
            readable,writable,exceptional = select.select(self.inputs,self.outputs,self.errputs,self.timeout)
            if (readable) :
                for serviceSock in readable:
                    if serviceSock is self.serverSock:
                        clientSock,clientAddr = serviceSock.accept()
                        print('[LOG: connect from',clientAddr,"]")
                        clientSock.setblocking(True)
                        clientSock.settimeout(3)
                        self.inputs.append(clientSock)
                        continue
                    
                    else:
                        try:   
                            msg = serviceSock.recv(CommonInfo._SOCK_SIZE)
                            msg = msg.decode("ascii")
                            if(len(msg)==0):
                                self.serverCom.closeAbnormal(serviceSock)
                                self.inputs.remove(serviceSock)
                                serviceSock.close()
                                continue
                        except:
                            self.serverCom.closeAbnormal(serviceSock)
                            self.inputs.remove(serviceSock)
                            serviceSock.close()
                            continue
                        
                        msg = msg.strip('\0')
                        jsonMsg = json.loads(msg)
                        msgType = self.serverCom.parseMsgType(jsonMsg)
                
                        if(msgType == CommonInfo._MSGTYPE_NEWTASK):
                            print("[LOG:",jsonMsg.get("taskId"),' recv task req]')
                            newTask = self.serverCom.handleTaskReq(jsonMsg,serviceSock)
                            self.serverCom.sendTaskReqAck(serviceSock, newTask)
                            continue
                        
                        if(msgType == CommonInfo._MSGTYPE_APPREADY):
                            print("[LOG:",jsonMsg.get("taskId"),' recv app ready]')
                            recvTask = self.serverCom.findTaskByMsg(jsonMsg)
                            if(recvTask==None):
                                continue
                            if(self.serverCom.handleAppReady(recvTask, serviceSock)==False):
                                self.serverCom.closeAbnormal(serviceSock)
                                self.inputs.remove(serviceSock)
                            else:
                                self.serverCom.sendAppRecvAck(recvTask, CommonInfo._RECV_SUCCESS, serviceSock)

                        if(msgType == CommonInfo._MSGTYPE_STATUSREQ):
                            reqTask = self.serverCom.handleTaskStatusReq(jsonMsg)
                            if(reqTask==None):
                                continue
                            sendFlag = self.serverCom.sendTaskStatusAck(serviceSock, reqTask)
                            if(sendFlag==False):
                                self.inputs.remove(serviceSock)
                                serviceSock.close()
                                continue
                            
                            if(reqTask.taskStatus == CommonInfo._TESTCASE_FINISH):
                                time.sleep(1)
                                print("[LOG:",jsonMsg.get("taskId"),' test case finish]')
                                self.serverCom.sendTestResult(serviceSock, reqTask)
                                print("[LOG:",jsonMsg.get("taskId"),' recv analysis result]')
                                self.serverCom.closeNormal(reqTask, serviceSock)
                                self.inputs.remove(serviceSock)
                                serviceSock.close()
                                print("[LOG:",jsonMsg.get("taskId"),' client close]')
                            reqTask = None
                            continue

            self.serverCom.testControl()
            time.sleep(1)
         
    def init(self):
        if(os.path.exists(CommonInfo.binaryDir)):
            print("[INIT: %s EXISTS]" %(CommonInfo.binaryDir,))
        else:
            os.mkdir(CommonInfo.binaryDir)
            print("[INIT %s not exists, CREATE it.]" %(CommonInfo.binaryDir,))
        if(os.path.exists(CommonInfo.outputDir)):
            print("[INIT: %s EXISTS]" %(CommonInfo.outputDir,))
        else:
            os.mkdir(CommonInfo.outputDir)
            print("[INIT %s not exists, CREATE it.]" %(CommonInfo.outputDir,))
            
        if (os.path.exists(CommonInfo.toolDir)==False):
            print("[ERROR: tools dir NOT exists]")
            return False
        
        missTool = []
        for toolName in CommonInfo.toolNames:
            if(os.path.exists(CommonInfo.toolDir+"\\"+toolName)):
                continue
            else:
                missTool.append(toolName)
        if(len(missTool)==0):
            print("[INIT: tools EXISTS]")
            print("[INIT: OK.]")
            return True
        else:
            print("[ERROR: INIT FAIL.]")
            print("[NOT exits tools: ",self.toolDir,end="\\")
            for missName in missTool:
                print(missName,end=" ")
            print("]")
            return False
        
    def closeAll(self):
        for eachSock in self.inputs:
            eachSock.close()

if __name__ == '__main__':
    masterServer = MasterServer()
    flag = masterServer.init()
    if flag:
        flag = masterServer.createConnect()
    if flag :
        masterServer.arbiter()
        masterServer.closeAll()
