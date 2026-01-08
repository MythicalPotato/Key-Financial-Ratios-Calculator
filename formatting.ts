function main(workbook: ExcelScript.Workbook) {
	let selectedSheet = workbook.getActiveWorksheet();
	// Auto fit the columns of all cells on selectedSheet
	selectedSheet.getRange().getFormat().autofitColumns();
	// Set format for range B:F on selectedSheet
	selectedSheet.getRange("B:F").setNumberFormatLocal("$#,##0.00");
	// Set format for range G:L on selectedSheet
	selectedSheet.getRange("G:L").setNumberFormatLocal("0.00%");
	// Set format for range M:O on selectedSheet
	selectedSheet.getRange("M:O").setNumberFormatLocal('0.00"x"');
	// Set format for range P:P on selectedSheet
	selectedSheet.getRange("P:P").setNumberFormatLocal('0 "days"');
}