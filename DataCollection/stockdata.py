import pandas as pd
import tushare as ts
from datetime import date
from datetime import timedelta  
import os
import time
import logging
import produceStockDataHelper
import threading
from pytdx.hq import TdxHq_API
from pytdx.hq import TDXParams

# global data
basePath = "./Data/"

pro = ts.pro_api()
api = TdxHq_API()
filePath = "./History/" + date.today().strftime("%Y%m%d") + ".xlsx"

historyPath = "History"
dataPath = "Data"

# Shanghai - 600,601,603
# Shenzhen - 000
# GEM - 300
def contactStockCode(number):
    switcher={
                "60":number+'.SH',
                "30":number+'.SZ',
                "00":number+'.SZ',
                "68":number+'.SH',
            }
    return  switcher.get(number[0:2],"")

def getProperToken(number):
    switcher={
            "0":tonyToken,
            "1":cymToken,
            "2":zhugeToken,
            "3":douziToken,
        }
    return  switcher.get(number,tonyToken)

def getStockScore(stockInfo):
    highPrice = stockInfo['high']
    ma5 = stockInfo['ma5']
    ma13 = stockInfo['ma13']
    ma21 = stockInfo['ma21']
    ma34 = stockInfo['ma34']
    ma55 = stockInfo['ma55']
    ma89 = stockInfo['ma89']
    ma144 = stockInfo['ma144']
    ma233 = stockInfo['ma233']

    if((highPrice > ma233).bool()):
        return 9

    if((highPrice > ma144).bool()):
        return 8
    
    if((highPrice > ma89).bool()):
        return 7

    if((highPrice > ma55).bool()):
        return 6

    if((highPrice > ma34).bool()):
        return 5

    if((highPrice > ma21).bool()):
        return 4
    
    if((highPrice > ma13).bool()):
        return 3
        
    if((highPrice > ma5).bool()):
        return 2
    # lower than ma5 prive
    return 1

def getLatestTradingDate(tradingDate):
    df = pro.trade_cal(exchange='SSE', start_date=tradingDate.strftime("%Y%m%d"), end_date=tradingDate.strftime("%Y%m%d"))
    isOpen = df.iloc[[0]]['is_open'] == 1
    if(isOpen.bool()):
        return tradingDate

    return getLatestTradingDate(tradingDate - timedelta(days=1))

def getUniqueKey(key, result):
    if( key in  result):
        key += 0.1
        return  getUniqueKey(key, result)
    return key

def printResult(result):
    sortedKeys = sorted(result.keys(),reverse = True)
    for key in sortedKeys:
      print(result[key])

def exportToExcel(data):
    dateName = date.today().strftime("%Y%m%d")
    df = pd.DataFrame.from_dict(data, orient="index", columns=['Name',dateName])
    print(df)
    df.to_excel(filePath, index=False)

def prepareStockData(stockNumbers, token, filename):
    ts.set_token(token)
     # get data form tu share for every stock
    latestTradingDate = getLatestTradingDate(date.today())
    pastDate = latestTradingDate - timedelta(days=365)  
    totalScores = 0
    totalStocks = 0
    suspendStocks = ""
    exceptionStocks = ""       
    total = len(stockNumbers)

    for number in stockNumbers:                    
        stockCode = contactStockCode(number)
        if len(stockCode) == 0:
            msg = "Can not find corresponding stock code: " + str(number)
            print(msg)
            logging.warning(msg)
            continue

        print('begin to deal with board name: '+ filename + " ,stock code:" + str(stockCode) + ", total stocks: " + str(total) + ", remain: "+ str(total - totalStocks)) 
        logging.info('begin to deal with board name: '+ filename + " ,stock code:" + str(stockCode) + ", total stocks: " + str(total) + ", remain: "+ str(total - totalStocks)) 
        
        retryCount = 0
        needRetry = True
        while(((retryCount < 3) and needRetry)):
            try:
                # check if suspend, we need to ignore it                
                suspend = pro.suspend(ts_code=stockCode, suspend_date=latestTradingDate.strftime("%Y%m%d"), resume_date='', fields='')                

                if(suspend.empty == False):
                    suspendStocks += stockCode + ','
                    continue

                df = ts.pro_bar(ts_code=stockCode, start_date=pastDate.strftime("%Y%m%d"), end_date=latestTradingDate.strftime("%Y%m%d"), ma=[5, 13, 21, 34, 55, 89, 144, 233])   

                if(df.empty == False):
                    totalScores += getStockScore(df.iloc[[0]])
                    totalStocks += 1
                else :
                    exceptionStocks += stockCode + ','
                time.sleep(0.05)
                needRetry = False
                
            except Exception as e:    
                retryCount += 1
                needRetry = True                            
                time.sleep(5)
                print("Begin to retry current stock: " + str(stockCode) + ", Retry count: " + str(retryCount))
                logging.exception(e)

    boardScores = 0
    if(totalStocks != 0):
        boardScores = totalScores/totalStocks  
    else:
        logging.warning("Can not get any stocks with board name: " + str(filename))

    key = getUniqueKey(boardScores, result)    
    
    try:
        lock.acquire()            
        result[key] = [filename, str(round(boardScores,2))]           
    finally:
        lock.release()

    if len(suspendStocks) != 0:
        logging.info("Board: "+filename+", These are suspend stocks for"+ suspendStocks)

    if len(exceptionStocks) != 0:
        logging.info( "Board: "+filename+", These are the exception stocks: " + exceptionStocks)  

    logging.info("End with board name:" + str(filename))   

def getBlockFile(blockNumber):
    switcher={
        "0":TDXParams.BLOCK_DEFAULT,
        "1":TDXParams.BLOCK_FG,
        "2":TDXParams.BLOCK_GN,
        "3":TDXParams.BLOCK_SZ,            
    }
    return  switcher.get(blockNumber,TDXParams.BLOCK_GN)

def getBlockInfos(blockNumber):    
    blockFile = getBlockFile(blockNumber)
    with api.connect('119.147.212.81', 7709):
        data = api.get_and_parse_block_info(blockFile)    
        df = pd.DataFrame(data)
        fileName = ""
        codelist = ""
        for index, row in df.iterrows():
            if(row["code_index"] == 0):
                if(fileName != ''):
                    # export to excel
                    fh = open(fileName,'w', encoding='utf-8')
                    fh.write(codelist.strip(','))
                    fh.close()
                    print("current board is completed: "+ fileName)

                fileName = basePath + str(row["blockname"]) + ".txt"
                codelist = ""
            
            codelist = codelist + row['code'] + ','    

# config logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logFileName = "stockdata_"+ date.today().strftime("%Y%m%d")+".log"
logging.basicConfig(filename=logFileName, level=logging.INFO, format=LOG_FORMAT)
print("Begin to deal with Stocks..............")
if(os.path.exists(historyPath) == False):
    os.mkdir(historyPath)

if(os.path.exists(dataPath) == False):
    os.mkdir(dataPath)

needRefreshBoardInfo = input("Do you want to refresh Board infos? Y or N \n")
if(needRefreshBoardInfo == "Y" or needRefreshBoardInfo == "y"):
    blockNumber = input("Please select board info:\n 0: BLOCK_DEFAULT \n 1: BLOCK_FG\n 2: BLOCK_GN\n 3: BLOCK_SZ\n")
    getBlockInfos(blockNumber)    

threads = []
lock = threading.Lock()

consumer1 = produceStockDataHelper.consumerThread(1,"Consumer1")
consumer2 = produceStockDataHelper.consumerThread(2,"Consumer2")
consumer3 = produceStockDataHelper.consumerThread(3,"Consumer3")
consumer4 = produceStockDataHelper.consumerThread(4,"Consumer4")

consumer1.start()
consumer2.start()
consumer3.start()
consumer4.start()

threads.append(consumer1)
threads.append(consumer2)
threads.append(consumer3)
threads.append(consumer4)



files = os.listdir(basePath)
totalBoardAcount = len(files)
logging.info("Board Total Account:" + str(totalBoardAcount))
print("Board Total Account:" + str(totalBoardAcount))
totalBoardAcountLog = totalBoardAcount

with os.scandir(basePath) as entries:
    result = dict()
    try:
        count = 1
        for entry in entries:
            with open(basePath+entry.name) as f:                    
                logging.info("Begin with board name:" + str(f.name)+ ", remain count: " +  str(totalBoardAcountLog))
                print("Begin with board name:" + str(f.name)+ ", remain count: " +  str(totalBoardAcountLog))
                totalBoardAcountLog -= 1

                content = f.read()
                stockNumbers = content.split(',')
         
                token = getProperToken(count % 4)

                data = []
                data.append(prepareStockData)
                data.append(stockNumbers)
                data.append(token)
                data.append(f.name)

                produceStockDataHelper.Produce(data)
                          
    except Exception as e:        
        logging.error("Run script failed: ", e) 
        exitFlag = 1

    # wait for queue is empty
    while not produceStockDataHelper.workQueue.empty():
        pass

    # exit thread
    produceStockDataHelper.exitFlag = 1

    # wait for all threads are done
    for t in threads:
        t.join()                 

    printResult(result)
    print("We already run "+str(len(result))+" module")
    logging.info("Board Real Total Account:" + str(len(result)))
    exportToExcel(result)
    logging.info("Get stock data completed")

k=input("press close to exit") 