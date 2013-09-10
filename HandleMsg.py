import json
from CommonInfo import *

class HandleMsg:
    '''
    def createTaskIdStr(self,taskId):
        taskStr = ''
        taskIdParts = taskId.split('_')
        taskIdFst = chr(int(taskIdParts[0])+CommonInfo._BASE_VALUE)
        taskStr += taskIdFst
        taskSn = int(taskIdParts[1])
        taskIdSnd = int(taskSn/100)
        taskIdTrd = taskSn%100
        taskStr += chr(taskIdSnd+CommonInfo._BASE_VALUE)
        taskStr += chr(taskIdTrd+CommonInfo._BASE_VALUE)
        return taskStr
        '''

    def parseTaskId(self,taskIdStr):
        taskIdFst = taskIdStr[CommonInfo._MSGINDEX_TASKIDFST]-CommonInfo._BASE_VALUE
        taskIdSnd = taskIdStr[CommonInfo._MSGINDEX_TASKIDSND]-CommonInfo._BASE_VALUE
        taskIdTrd = taskIdStr[CommonInfo._MSGINDEX_TASKIDTRD]-CommonInfo._BASE_VALUE
        interTaskId = int(taskIdSnd*100+taskIdTrd)
        taskId = str(taskIdFst)+'_'+str(interTaskId)
        return taskId
    
    def createTaskReqAck(self,taskId,permit=CommonInfo._NEWTASK_ACCEPT):
        jsonMsg = {}
        jsonMsg["taskId"] = taskId
        jsonMsg["msgType"] = CommonInfo._MSGTYPE_TASKACK
        jsonMsg["reqStatus"] = permit
        msg = json.dumps(jsonMsg)
        return msg

    def createAppRecvAck(self,taskId,status=CommonInfo._APPRECV_SUCCESS):
        jsonMsg = {}
        jsonMsg["taskId"] = taskId
        jsonMsg["msgType"] = CommonInfo._MSGTYPE_APPRECV
        jsonMsg["recvStatus"] = status
        msg = json.dumps(jsonMsg)
        return msg

    def createTaskStatusAck(self,taskId,status):
        jsonMsg = {}
        jsonMsg["taskId"] = taskId
        jsonMsg["msgType"] = CommonInfo._MSGTYPE_STATUSACK
        jsonMsg["taskStatus"] = status
        msg = json.dumps(jsonMsg)
        return msg
    
    def createTestResult(self,taskInfo,outputSize):
        jsonMsg = {}
        jsonMsg["taskId"] = taskInfo.taskId
        jsonMsg["msgType"] = CommonInfo._MSGTYPE_TESTRESULT
        jsonMsg["testResult"] = taskInfo.testResult
        if(taskInfo.testResult==CommonInfo._TESTRESULT_PASS or taskInfo.testResult==CommonInfo._TESTRESULT_FAIL):
            jsonMsg["outputPath"] = taskInfo.outputDir+taskInfo.taskId+"\\output.txt"
            jsonMsg["outputSize"] = outputSize
            jsonMsg["detailPath"] = taskInfo.outputDir+taskInfo.taskId+"\\detail.xml"
        else:
            jsonMsg["outputPath"] = "BVT abort, No output.txt"
            jsonMsg["outputSize"] = 0
            jsonMsg["detailPath"] = "BVT abort, No detail.xml"
        msg = json.dumps(jsonMsg)
        return msg

    def parseTaskReq(self,jsonMsg):
        oper = jsonMsg.get("operPlatform")
        return oper

    def parseAppReady(self,jsonMsg):
        taskId = jsonMsg.get("taskId")
        return taskId
    
