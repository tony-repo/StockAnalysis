import queue
import threading

exitFlag = 0
queueLock = threading.Lock()
workQueue = queue.Queue()

def Produce(data):        
    workQueue.put(data,block=False)             
    

class consumerThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        
    def run(self):
        print ("开始线程：" + self.name)
        consumer_data(self.name)
        print ("退出线程：" + self.name)

def consumer_data(threadName):
    #while not exitFlag:  
    while not exitFlag:  
        try:
            print("Begin to work with thread: " + threadName)
            queueLock.acquire()                 
            if not workQueue.empty():   
                
                data = workQueue.get(block=False)   
                workQueue.task_done()               
                queueLock.release()
                if  data is None: 
                    continue
                else:
                    func = data[0]
                    stockNumbers = data[1]
                    token = data[2]
                    filename = data[3]
                    func(stockNumbers, token, filename)
            else:
                queueLock.release()
        except queue.Empty:
            break  

