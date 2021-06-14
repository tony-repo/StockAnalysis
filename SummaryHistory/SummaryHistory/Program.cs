using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using OfficeOpenXml;

namespace SummaryHistory
{
    class Program
    {
        private static string filePath = string.Empty;
        private const string basePath = "./Summary";
        private const string sourceBasePath = "./History";
        private static readonly string fileName = DateTime.Now.Date.ToString("yyyyMMdd") + ".xlsx";
        private static readonly string calculatedFileName = "CaculatedSummary" + DateTime.Now.Date.ToString("yyyyMMdd") + ".xlsx";

        public static void ExportToExcel(string fileName, List<string> headers, Dictionary<string, List<string>> datas)
        {
            Directory.CreateDirectory(basePath);
            filePath = Path.Combine(basePath, fileName);

            if (File.Exists(filePath))
            {
                File.Delete(filePath);
            }

            FileInfo createdFile = new FileInfo(filePath);
            using ExcelPackage package = new ExcelPackage(createdFile);
            ExcelWorksheet worksheet = package.Workbook.Worksheets.Add("Summary");
            for (int i = 1; i <= headers.Count; i++)
            {
                worksheet.Cells[1, i].Value = headers[i - 1];
            }

            int row = 2;
            foreach (var data in datas)
            {
                int col = 1;
                foreach (var value in data.Value)
                {


                    if (decimal.TryParse(value, out decimal decimalValue) && decimalValue < 1)
                    {
                        worksheet.Cells[row, col].Value = decimalValue;
                        if (decimalValue < 1)
                        {
                            worksheet.Cells[row, col].Style.Numberformat.Format = "#0\\.00%";
                        }
                        
                    }
                    else
                    {
                        worksheet.Cells[row, col].Value = value;
                    }

                    col++;
                }

                row++;
            }

            package.Save();
        }

        public static void CalculateExcel()
        {
            FileInfo existingFile = new FileInfo(filePath);
            using ExcelPackage package = new ExcelPackage(existingFile);
            ExcelWorksheet worksheet = package.Workbook.Worksheets[0];

            int rowCount = worksheet.Dimension.Rows;
            int colCount = worksheet.Dimension.Columns;

            // the whole columns format: Name, 20210608, 20210609
            // Header
            // Begin from 2, since the first column is 'Name'
            var headerNames = new List<string>();

            var firstColName = worksheet.Cells[1, 1].Value.ToString();
            headerNames.Add(firstColName);
            if (colCount - 1 < 2)
            {
                var col2 = worksheet.Cells[1, 2].Value.ToString();
                headerNames.Add(col2);
            }

            for (int col = 2; col <= colCount - 1; col++)
            {
                var preName = worksheet.Cells[1, col].Value.ToString();
                var nextName = worksheet.Cells[1, col + 1].Value.ToString();
                headerNames.Add(preName);
                headerNames.Add(nextName);
                headerNames.Add(preName + "-" + nextName);
            }

            Dictionary<string, List<string>> result = new Dictionary<string, List<string>>();

            for (int row = 2; row <= rowCount; row++)
            {
                List<string> datas = new List<string>();
                var rowName = worksheet.Cells[row, 1].Value.ToString();
                datas.Add(rowName);
                if (colCount - 1 < 2)
                {
                    var score = Convert.ToDecimal(worksheet.Cells[row, 2].Value);
                    datas.Add(score.ToString());
                }

                for (int col = 2; col <= colCount - 1; col++)
                {
                    var preScore = Convert.ToDecimal(worksheet.Cells[row, col].Value);
                    var nextScore = Convert.ToDecimal(worksheet.Cells[row, col + 1].Value);

                    datas.Add(preScore.ToString());
                    datas.Add(nextScore.ToString());
                    var calculatedScore = ((nextScore / preScore) - 1).ToString("#0.00");
                    datas.Add(calculatedScore);
                }
                result.Add(rowName, datas);
            }

            ExportToExcel(calculatedFileName, headerNames, result);
        }

        static void Main(string[] args)
        {
            try
            {
                ExcelPackage.LicenseContext = LicenseContext.NonCommercial;

                var headers = new List<string>();
                var files = Directory.GetFiles(sourceBasePath)?.OrderBy(s => s).ToList();

                if (files == null || !files.Any())
                {
                    Console.WriteLine("Can not find any files in History directory.");
                    return;
                }

                var result = new Dictionary<string, List<string>>();
                var remainCount = files.Count();

                foreach (var file in files)
                {
                    Console.WriteLine($"Begin to deal with file: {file}, remain file count: {remainCount--}");

                    FileInfo existingFile = new FileInfo(file);
                    using ExcelPackage package = new ExcelPackage(existingFile);
                    ExcelWorksheet worksheet = package.Workbook.Worksheets[0];

                    int rowCount = worksheet.Dimension.Rows;
                    int colCount = worksheet.Dimension.Columns;

                    for (int col = 1; col <= colCount; col++)
                    {
                        var headerName = worksheet.Cells[1, col].Value.ToString();
                        // Set Header Name 
                        if (headers.Contains(headerName))
                        {
                            continue;
                        }
                        headers.Add(headerName);
                    }

                    for (int row = 2; row <= rowCount; row++)
                    {
                        var name = worksheet.Cells[row, 1].Value.ToString();

                        if (result.TryGetValue(name, out List<string> data))
                        {
                            for (int col = 2; col <= colCount; col++)
                            {
                                var score = worksheet.Cells[row, col].Value.ToString();
                                data.Add(score);
                            }
                        }
                        else
                        {
                            data = new List<string>();
                            // Get specific data
                            for (int col = 1; col <= colCount; col++)
                            {
                                var score = worksheet.Cells[row, col].Value.ToString();
                                data.Add(score);
                            }
                            result.Add(name, data);
                        }
                    }
                }

                ExportToExcel(fileName, headers, result);

                Console.WriteLine($"Export to excel down. File path:{filePath}");

                Console.WriteLine($"Begin to Calculate excel.");
                CalculateExcel();
                Console.WriteLine($"Finished to Calculate excel.");
                Console.Read();
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
                throw;
            }
        }
    }
}
