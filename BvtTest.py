import multiprocessing
import random
import time
import os
import configparser
import subprocess
import platform
from CommonInfo import *
from TaskInfo import *
   
class BvtTest(multiprocessing.Process):
    def __init__(self,info,tQueue):
        multiprocessing.Process.__init__(self)
        self.taskInfo = info
        self.taskQueue = tQueue
        self.toolPath = CommonInfo.toolDir
        self.outputPath = self.taskInfo.outputDir+os.path.sep+self.taskInfo.taskId
        if(os.path.exists(self.outputPath)==False):
            os.mkdir(self.outputPath)
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        
    def analysisResult(self, resultFile):
        CASE_BEGIN_TAG   = "[ RUN      ]"
        CASE_PASS_TAG    = "[       OK ]"
        CASE_FAIL_TAG    = "[  FAILED  ]"
        CASE_FINISH_TAG  = "test cases ran."
        caseResult = []
        OverAllResult='PASS'
        resCrashed = True
        if(False == os.path.isfile(resultFile)):
            print("[analysisResult]ERROR:%s does not exist!"%resultFile)
            return 'ABORT'
        f = open(resultFile,'r')
        resultStr = f.readlines()
        caseName = ""
        for line in resultStr:
            if(line.find(CASE_BEGIN_TAG) != -1):
                index = line.index(CASE_BEGIN_TAG)
                caseName = line[index+len(CASE_BEGIN_TAG)+1:].strip()
            elif(caseName != "" and line.find(CASE_PASS_TAG) != -1):
                st=line.rfind('(')
                et=line.rfind(')')
                if(st != -1 and et != -1):
                    t=line[st+1:et]
                else:
                    t='NA'
                caseResult.append((caseName,t,'PASS'))
                caseName=""
            elif(caseName != "" and line.find(CASE_FAIL_TAG) != -1):
                st=line.rfind('(')
                et=line.rfind(')')
                if(st != -1 and et != -1):
                    t=line[st+1:et-1]
                else:
                    t='NA'
                caseResult.append((caseName,t,'FAIL'))
                OverAllResult='FAIL'     
                caseName=""
            elif(line.find(CASE_FINISH_TAG) != -1):
                resCrashed = False
        if (caseName != ""):
            caseResult.append((caseName,'NA','CRASH'))
        if (resCrashed == True):
            OverAllResult = 'CRASH'
        print("[analysisResult]: %s"%caseResult)
        print("OverAllResult:",OverAllResult)
        return OverAllResult
  
    def run_bvt_win_local(self,configSection):
        testFilter = self.config.get(configSection, 'test_filter')
        sysstr = platform.system()
        outputfile=self.outputPath+os.path.sep+"output.txt"
        print("[run_bvt_win_local]:start bvt for conf:%s"%(self.taskInfo.taskId,))  
        bvtFile=self.taskInfo.binaryPath
        if(os.path.isfile(bvtFile)):
            result = 'PASS'
        else:
            result = 'ABORT'
        if("Windows" == sysstr and 'PASS' == result):
            runcmd = bvtFile
            runcmd += " --gtest_output=xml:"+self.outputPath+os.path.sep+"detail.xml"
            runcmd += " -l "+self.outputPath+os.path.sep+"sct.log"+" --gtest_filter=" + testFilter
            print("[run_bvt_win_local(%s)]: %s"%(self.taskInfo.taskId,runcmd))  
            p = subprocess.Popen(runcmd, shell = False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = p.communicate()
            outputstr = out.decode()
            #print("[run_bvt_win_local(%s)]: %s"%(self.taskInfo.taskId,outputstr))
            f = open(outputfile,'w')
            f.write(outputstr)
            f.close()
            result = self.analysisResult(outputfile)
        return result

    def run_bvt_win_remote(self,configSection):   
        executable=self.config.get(configSection,'exec')
        #conf=self.config.get(configSection,'conf')
        user=self.config.get(configSection,'user')
        passwd=self.config.get(configSection,'passwd')
        deviceIp=self.config.get(configSection,'device_ip')
        devicePort=self.config.get(configSection,'device_port')
        remoteRoot=self.config.get(configSection,'remote_root')
        remoteFolder=self.config.get(configSection,'remote_folder')+os.path.sep+self.taskInfo.taskId
        #binaryDir = remoteRoot+os.path.sep+remoteFolder
        testFilter = self.config.get(configSection, 'test_filter')
        outputfile=self.outputPath+os.path.sep+"output.txt"      
        sysstr = platform.system()
        bvtFile=self.taskInfo.binaryPath
        if(os.path.isfile(bvtFile)):
            result = 'PASS'
        else:
            result = 'ABORT'
            
        if("Windows" == sysstr and 'PASS' == result):
            #cleancmd = "winrs -r:http://"+deviceIp+':'+devicePort +" -timeout:1800000 "+' -u:'+user+' -p:'+passwd+' rd /S /Q '+ remoteRoot + remoteFolder
            #ret = subprocess.call(cleancmd, shell=False)
            readycmd = "winrs -r:http://"+deviceIp+':'+devicePort +" -timeout:1800000 "+' -u:'+user+' -p:'+passwd+' mkdir '+ remoteRoot + remoteFolder
            ret = subprocess.call(readycmd,shell=False)
            pushcmd="copy /Y " + bvtFile +' ' + os.path.sep + os.path.sep + deviceIp + os.path.sep + remoteFolder + os.path.sep + executable
            ret = subprocess.call(pushcmd, shell=True)   
            runcmd = "winrs -r:http://"+deviceIp+':'+devicePort +" -timeout:1800000 "+' -u:'+user+' -p:'+passwd+' '+ remoteRoot + remoteFolder + os.path.sep + executable
            runcmd += " -l " + remoteRoot + remoteFolder + os.path.sep+"sct.log"
            runcmd += " --gtest_output=xml:"+ remoteRoot + remoteFolder + os.path.sep+"detail.xml"
            runcmd += " --gtest_filter=" + testFilter
            #print(runcmd)    
            p = subprocess.Popen(runcmd, shell = False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = p.communicate()
            outputstr = out.decode()
            f = open(outputfile,'w')
            f.write(outputstr)
            f.close()
            pushcmd="copy /Y " + os.path.sep + os.path.sep + deviceIp + os.path.sep + remoteFolder + os.path.sep +"detail.xml"+" "+self.outputPath+os.path.sep+"detail.xml"
            ret = subprocess.call(pushcmd, shell=True)
            cleancmd = "winrs -r:http://"+deviceIp+':'+devicePort +" -timeout:1800000 "+' -u:'+user+' -p:'+passwd+' rd /S /Q '+ remoteRoot + remoteFolder
            ret = subprocess.call(cleancmd, shell=False)
            result = self.analysisResult(outputfile)
            
        return result
    
    def run_bvt_android(self,configSection):
        print("[run_bvt_android]:run android bvt")
        executable=self.config.get(configSection,'exec')
        pkg_name=self.config.get(configSection,'pkg_name')
        app_name=self.config.get(configSection,'app_name')
        log_file=self.config.get(configSection,'log_file')
        test_filter = self.config.get(configSection,'test_filter')
        sysstr = platform.system()
        outputfile="C:\\"+self.taskInfo.taskId+"\\"+log_file
        apkFile=self.taskInfo.binaryPath
        if(os.path.isfile(apkFile)):
            result = 'PASS'
        else:
            result = 'ABORT'
      
        if("Windows" == sysstr and 'PASS' == result):
            print("[run_bvt_android(%s)]: Uninstall" %(self.taskInfo.taskId,))
            cleancmd=self.toolPath+os.path.sep+"adb.exe shell pm uninstall " + pkg_name
            print("[run_bvt_android(%s)]: %s"%(self.taskInfo.taskId,cleancmd))
            ret = subprocess.call(cleancmd, shell=False)
            print("[run_bvt_android(%s)]: Uninstall ret=%d"%(self.taskInfo.taskId,ret))
            print("[run_bvt_android(%s)]: Push to device" %(self.taskInfo.taskId,))
            pushcmd=self.toolPath+os.path.sep+"adb.exe install " + apkFile
            print("[run_bvt_android(%s)]: %s"%(self.taskInfo.taskId,pushcmd))
            ret = subprocess.call(pushcmd, shell=False)
            print("[run_bvt_android(%s)]: Push to device: ret=%d"%(self.taskInfo.taskId,ret))
            print("[run_bvt_android(%s)]: Launch BVT",(self.taskInfo.taskId,))
            runcmd=self.toolPath+os.path.sep+"adb.exe shell am start -n " + pkg_name + "/."+ app_name+ " --es gtest_output xml:/sdcard/"+"detail.xml"
            runcmd += " --es gtest_filter " + test_filter
            runcmd += " --es exitOnComplete true"
            print("[run_bvt_android(%s)]: %s"%(self.taskInfo.taskId,runcmd))
            ret = subprocess.call(runcmd, shell=False)
            print("[run_bvt_android(%s)]: BVT ret=%d" %(self.taskInfo.taskId,ret))
            pullcmd=self.toolPath+os.path.sep+"adb.exe pull /data/data/" + pkg_name + "/"+ log_file + " "+self.outputPath
            pullDetailCmd=self.toolPath+os.path.sep+"adb.exe pull /sdcard/"+"detail.xml"+" "+self.outputPath
            print("[run_bvt_android(%s)]: %s"%(self.taskInfo.taskId,pullcmd))
            time.sleep(300) #sleep 5mins first
            for i in range(25):
                print("[run_bvt_android(%s)]:trying %d time pulling"%(self.taskInfo.taskId,i))
                ret = subprocess.call(pullcmd, shell=False)
                if(ret == 0):
                    subprocess.call(pullDetailCmd, shell=False)
                    break
                else:
                    time.sleep(60)
            stopcmd=self.toolPath+os.path.sep+"adb.exe shell am force-stop " + pkg_name
            ret = subprocess.call(stopcmd, shell=False)     
            result = self.analysisResult(outputfile)
        return result
    
    def run_bvt_ssh(self,configSection):
        remotePath=self.config.get(configSection, "remote_path")+ "/"+self.taskInfo.taskId 
        executable=self.config.get(configSection, "exec")
        user=self.config.get(configSection, "user")
        passwd=self.config.get(configSection, "passwd")
        deviceIp=self.config.get(configSection, "remote_ip")
        testFilter = self.config.get(configSection,"test_filter")
        outputfile=self.outputPath+os.path.sep+"output.txt"
        print("[run_bvt_ssh]:start bvt for conf:%s"%(configSection,))
        sysstr = platform.system()      
        bvtFile=self.taskInfo.binaryPath
        if(os.path.isfile(bvtFile)):
            result = 'PASS'
        else:
            result = 'ABORT'      
        if("Windows" == sysstr and 'PASS' == result):  
            cleancmd=self.toolPath+os.path.sep+"PLINK.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + " rm -rf " + remotePath
            ret = subprocess.call(cleancmd)
            readycmd=self.toolPath+os.path.sep+"PLINK.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + " mkdir " + remotePath
            ret = subprocess.call(readycmd)
            pushcmd=self.toolPath+os.path.sep+"PSCP.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + bvtFile + ' ' + deviceIp + ":" + remotePath
            ret = subprocess.call(pushcmd)
            chmodcmd=self.toolPath+os.path.sep+"PLINK.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + " chmod 755 " + remotePath + '/' + executable
            ret = subprocess.call(chmodcmd)      
            runcmd=self.toolPath+os.path.sep+"PLINK.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + " " + remotePath + '/' + executable + " --gtest_output=xml:"+remotePath+"/detail.xml"
            runcmd += " --gtest_filter=" + testFilter
            connectionType='-ssh'
            print("[run_bvt_ssh(%s)]: %s"%(self.taskInfo.taskId,runcmd))  
            p = subprocess.Popen(runcmd, shell = True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = p.communicate()
            outputstr = out.decode()
            print(outputfile)
            f = open(outputfile,'w')
            f.write(outputstr)
            f.close()
            #pullcmd=self.toolPath+os.path.sep+"PSCP.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + ":" + remotePath+"/detail.xml 。"
            pullcmd=self.toolPath+os.path.sep+"PSCP.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + ":" + remotePath + "/detail.xml " + CommonInfo.outputDir+"\\"+self.taskInfo.taskId 
            ret = subprocess.call(pullcmd)
            cleancmd=self.toolPath+os.path.sep+"PLINK.EXE" + ' ' + "-l " + user + ' ' + "-pw " + passwd + ' ' + deviceIp + " rm -rf " + remotePath
            ret = subprocess.call(cleancmd)
            
            result = self.analysisResult(outputfile)
            p.wait()
        return result

    def run(self):
        try:
            self.selectTest()
        except:
            print("@@@ Test Run Fail. @@@")
        
        
    def selectTest(self):
        print('[LOG: bvt test',self.taskInfo.taskId,' run]')
        if (self.taskInfo.operPlatform == CommonInfo._OPER_IOS):
            result = self.run_bvt_ssh("ios-armv7")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_ANDROID):
            result = self.run_bvt_android("android-armv6-ndk")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_WINRTARM7):
            result = self.run_bvt_win_remote("winrt-armv7")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_MACI386):
            result = self.run_bvt_ssh("mac-i386")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_MACX64):
            result = self.run_bvt_ssh("mac-x86_64")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_LINUXX64):
            result = self.run_bvt_ssh("linux-x86_64-glibc")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_LINUXI386):
            result = self.run_bvt_ssh("linux-i386-glibc")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_BLUEI386):
            result = self.run_bvt_win_remote("blue-i386")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_BLUEX64):
            result = self.run_bvt_win_remote("blue-x86_64")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_WINI386):
            result = self.run_bvt_win_local('win-i386')
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_WINI386):
            result = self.run_bvt_win_remote("winrt-i386")
        elif(self.taskInfo.operPlatform == CommonInfo._OPER_WINRTX64):
            result = self.run_bvt_win_remote("winrt-x86_64")
        else:
            result = 'ABORT'
        if(result == 'PASS'):
            print('#######',self.taskInfo.taskId,' pass #####')
            self.taskInfo.testResult = CommonInfo._TESTRESULT_PASS
        else:
            self.taskInfo.testResult = CommonInfo._TESTRESULT_FAIL
            print('#######',self.taskInfo.taskId,' fail #####')
        self.taskInfo.taskStatus = CommonInfo._TESTCASE_FINISH
        self.taskQueue.put(self.taskInfo)
        
