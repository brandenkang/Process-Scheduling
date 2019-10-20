import sys
import globalv
globalv.init()

class Process:  
    def __init__(self,A,B,C,M,i):
        self.A = A
        self.B = B
        self.C = C
        self.M  = M
        self.i = i
        self.q = 2
        self.state = "unstarted" 
        self.burst = 0
        self.prev = 0 
        self.readyTime = 0
        self.runTime = 0
        self.turnTime = 0
        self.ioTime = 0
        self.waitingTime = 0
        self.finTime = 0
        self.remTime = C

    def updateClock(self):
        state = self.state 
        if state not in ["unstarted", "terminated"]:
            self.turnTime+=1
            if state == "ready":
                self.waitingTime+=1
            elif state == "running":
                self.runTime += 1
                self.remTime -= 1
                self.q -=1 if globalv.RR > 0 else 0
                self.burst -=1 if self.burst > 0 else 0
            elif state == "blocked":
                self.burst -=1 if self.burst > 0 else 0 
                self.ioTime +=1
        return 

    def updateCurr(self):
        time = globalv.time.getTime()
        if self.state == "unstarted":
            if time == self.A:
                self.ready()
        elif self.state == "running":
            if self.remTime == 0:
                self.state = "terminated"
                self.finTime = time
            elif self.burst == 0:
                self.block()
            elif globalv.RR:
                if self.q == 0:
                    self.ready()
        elif self.state == "blocked":
            if self.burst == 0:
                self.ready()
        elif self.state == "ready" or self.state == "terminated": 
            pass 

    def IO(self):
        self.burst = self.M * self.prev 
        return 

    def CPU(self):
        self.prev = 1 + int(globalv.randomFile.readline().strip()) % self.B
        self.burst = self.prev
        return

    def ratio(self):
        turnT = self.turnTime 
        runT = max(1,self.runTime)
        return turnT/runT 

    def ready(self):
        self.state = "ready"
        self.readyTime = globalv.time.getTime()

    def running(self):
        self.state = "running"
        if self.burst == 0:
            self.CPU()
        if globalv.RR == True:
            self.q = 2

    def block(self):
        self.state = "blocked"
        self.IO()
    
    def printProcesses(self):
        print("({} {} {} {})  ".format(self.A, self.B, self.C, self.M), end='')

    def printAll(self):
        print("(A, B, C, M) = ({}, {}, {}, {})\nFinish Time: {}\nTurnaround Time: {}\nI/O Time: {}\nWaiting Time: {}\n"
        .format(self.A, self.B, self.C, self.M, self.finTime, self.finTime-self.A, self.ioTime, self.waitingTime))

class Time:
    def __init__(self):
        self.time = 0

    def update(self):
        self.time+=1
        
    def getTime(self):
        return self.time
        
def parse():
    processArr = [] 
    with open(sys.argv[-1], 'r') as f:
        lines = f.read()
    lines = [int(i) for i in lines.strip().split()]
    num = lines.pop(0)
    for i in range(num): 
        processArr.append(lines[4*i:4*i + 4])
    return processArr, num

"""--------------------------------------PROCESS TABLE--------------------------------------"""
def processState(pArr, state):
    newList = []
    for process in pArr:
        if process.state == state:
            newList.append(process)
    return newList

def updateTime(pArr):
   if processState(pArr, "blocked"):
        globalv.IOUtilisation += 1
   for process in pArr:
        process.updateClock()
   return 

def updateAllStates(pArr):
    for process in pArr:
        process.updateCurr()
    return

def sortByInput(pArr):
    pArr.sort(key=lambda process: process.i)
    return pArr

def sortByArrival(pArr):
     pArr.sort(key=lambda process: process.A)
     return pArr

def sortByShortest(pArr):
    pArr.sort(key=lambda process: process.C - process.runTime)
    return pArr

def sortByReady(pArr):
    pArr.sort(key=lambda process: process.readyTime)
    return pArr

def sortByHPRN(pArr):
    pArr.sort(key=lambda process: -process.ratio())
    return pArr  

def checkComplete(pArr):
    for process in pArr:
        if process.state != "terminated":
            return False
    globalv.finTime = globalv.time.getTime() - 1
    return True
        
def printData(pArr):
    throughput = 100*len(pArr) / globalv.finTime
    waitingTime = []
    for process in pArr: 
        waitingTime.append(process.waitingTime)
    finalWaitingTime = sum(waitingTime) / len(pArr)
    turnTime = [] 
    for process in pArr: 
        turnTime.append(process.turnTime) 
    finalTurnTime = sum(turnTime) / len(pArr)
    ioUtil = (globalv.IOUtilisation / globalv.finTime)
    cpuUtil = [] 
    for process in pArr: 
        cpuUtil.append(process.runTime) 
    finalCpuUtil = sum(cpuUtil) / globalv.finTime 
    print("Summary Data :\nI/O Utilisation: {:.6f}\nCPU Utilisation: {:.6f}\nThroughput: {:.6f} Processes Per 100 Cycles\nAvg. Turnaround Time: {:.6f}\nAvg. Waiting Time: {:.6f}\nFinishing Time: {}".format(ioUtil, finalCpuUtil, throughput, finalTurnTime, finalWaitingTime,globalv.finTime)) 

"""--------------------------------------SCEHDULING ALGORITHMS --------------------------------------"""
def schedulingAlgo(pArr, schedulingAlgo):
    checker = 0
    while not checkComplete(pArr):
        vLine = ""
        if globalv.verbose:
            print("Before Cycle {}      ".format(str(checker)),end='')
            for process in pArr:
                vLine += process.state + " " + str(process.burst) + "    "
            print(vLine)
            checker+=1
        updateTime(pArr)
        updateAllStates(pArr)
        if not (processState(pArr, "running")):
            allReady = sortByArrival(sortByInput(processState(pArr,"ready")))
            if schedulingAlgo == "FCFS":
                allReady = sortByReady(allReady) 
            if schedulingAlgo == "Round Robin":
                globalv.RR = True 
                allReady = sortByReady(allReady)
            if schedulingAlgo == "SJF":
                allReady = sortByShortest(allReady)
            if schedulingAlgo == "HPRN":
                allReady = sortByHPRN(allReady)
            if allReady:
                allReady.pop(0).running()
        globalv.time.update()
    print("Scheduling schedulingAlgo used: " + schedulingAlgo)
    return pArr

"""--------------------------------------PRINTING ALL--------------------------------------"""

def printEverything(method): 
    processes, num = parse()
    globalv.time = Time()
    pArr = [] 
    for i in range(len(processes)):
        pArr.append(Process(*processes[i],i)) 
    print("Original Input : "+str(num)+" ", end='')
    for process in pArr:
        process.printProcesses()
    print("\n")
    pArr = sortByArrival(pArr)
    print("Sorted Input :   "+str(num)+" ", end='')
    for process in pArr:
        process.printProcesses()
    pArr = schedulingAlgo(pArr, method)
    for i in range(len(pArr)):
        print("Process {}: ".format(str(i)))
        pArr[i].printAll()
    printData(pArr)

def runAllschedulingAlgos(): 
    schedulingList = ["FCFS", "Round Robin", "SJF", "HPRN"]
    for method in schedulingList: 
        if method == "FCFS": 
            printEverything(method)
        else:
            globalv.IOUtilisation = 0 
            globalv.finTime = 0
            globalv.randomFile.seek(0)
            printEverything(method)

"""--------------------------------------MAIN FUNCTION--------------------------------------"""
def main():
    globalv.randomFile = open("random-numbers.txt", 'r')
    if "--show-random" in sys.argv:
        globalv.random = True
    if "--verbose" in sys.argv:
        globalv.verbose = True
    runAllschedulingAlgos() 

if __name__ == "__main__":
    main()