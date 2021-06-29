# StockAnalysis

Select proper stock

## Prerequisite

Need to get token from https://tushare.pro/

## Data Collection

We will use pytdx library to get Board infos

> Interface instruction: https://github.com/peter159/pytdx-1

This module use python to get stock data from TuShare

> We need to install below package before we run it

``` bash
    pip install openpyxl # For export to excel
    pip install tushare # For stock infos
    pip install pandas # For datatable in python
```

> Input and output path

* Input: `./Data` : we need to input txt file named with board name into here

``` text
    For example:

    file name: Finance.txt
    600318, 600588
```

* Output: `./History` : here is the calculated data(file will output as excel -> suffix is .xlsx)

> Package python to exe

``` bash

    pip install pyinstaller
    pyinstaller -F stockdata.py

```

## Summary

This module use .net core to do the summary part

> Input and output path

* Input: Input will use `./History` as the input data which is created by data collection

* Output: `./Summary` will as the output path

> Package .net core to exe

``` bash
    1. dotnet tool install --global dotnet-warp
    2. go to the solution folder
    3. dotnet-warp
```
