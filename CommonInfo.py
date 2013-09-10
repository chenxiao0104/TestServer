class CommonInfo:
    #max size buff
    _MAX_SIZE = 1024
    _SOCK_SIZE = 512

    #NEW TASK
    _NEW_TASK = 0

    #msg length
    _MSGLEN_ALL = 6
    _MSGLEN_TASKID = 3
    
    #msg base value
    _BASE_VALUE = 10
    
    #recv flag
    _SEND_READY = 1
    _RECV_SUCCESS = 1
    _RECV_FAIL = 0
    
    #task status
    _TESTCASE_WAITING = 4001
    _TESTCASE_RUNNING = 4002
    _TESTCASE_FINISH = 4003
    _TESTCASE_FAIL = 4004
    _TESTCASE_TIMEOUT = 4005
    
    #Operation Platform
    _OPER_IOS = 5001
    _OPER_ANDROID = 5002
    _OPER_WINRTARM7 = 5003
    _OPER_MACI386 = 5004
    _OPER_MACX64 = 5005
    _OPER_LINUXX64 = 5006
    _OPER_LINUXI386 = 5007
    _OPER_BLUEI386 = 5008
    _OPER_BLUEX64 = 5009
    _OPER_WINI386 = 5010
    _OPER_WINRTI386 = 5011
    _OPER_WINRTX64 = 5012
    
    #Message Type
    _MSGTYPE_NEWTASK = 3001
    _MSGTYPE_TASKACK = 3002
    _MSGTYPE_APPRECV = 3003
    _MSGTYPE_STATUSREQ = 3004
    _MSGTYPE_STATUSACK = 3005
    _MSGTYPE_TESTRESULT = 3006
    _MSGTYPE_ANALYSIS = 3007
    _MSGTYPE_APPREADY = 3008
    _MSGTYPE_APPSEND = 3009
    _MSGTYPE_APPFINISH = 3010
    
    #New Task Request
    _NEWTASK_ACCEPT = 1
    _NEWTASK_REFUSE = 0
    
    #Binary Receive Status
    _APPRECV_PERMIT = 1
    _APPRECV_REFUSE = 0
    
    _APPRECV_SUCCESS = 1
    _APPRECV_FAIL  = 0
    
    #Test Case Result
    _TESTRESULT_ABORT = 2
    _TESTRESULT_PASS = 1
    _TESTRESULT_FAIL = 0
    
    #Analysis Result
    _ANALYSIS_PASS = 1
    _ANALYSIS_FAIL = 0
    
    #message content
    _MSGINDEX_TASKIDFST = 0
    _MSGINDEX_TASKIDSND = 1
    _MSGINDEX_TASKIDTRD = 2
    _MSGINDEX_MSGTYPE = 3
    _MSGINDEX_DATA = 4
    
    #
    toolDir = "C:\\tools"
    binaryDir = "C:\\bvttest"
    outputDir = "C:\\bvttest\\testOutput"
    toolNames = ["PLINK.EXE","PSCP.EXE","adb.exe","AdbWinApi.dll","AdbWinUsbApi.dll"]
    
    #server information
    ServerIp = "10.172.76.63"
    ServerPort = 15504
