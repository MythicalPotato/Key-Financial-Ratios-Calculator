// global.d.ts
declare namespace ExcelScript {
    interface Workbook {
        getActiveWorksheet(): Worksheet;
    }
    interface Worksheet {
        getRange(address?: string): Range;
    }
    interface Range {
        getFormat(): RangeFormat;
        setNumberFormatLocal(format: string): void;
    }
    interface RangeFormat {
        autofitColumns(): void;
    }
}