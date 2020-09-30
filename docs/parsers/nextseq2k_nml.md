# NextSeq2000

The Software on the NextSeq2000 does not allow for automatic generation of a SampleSheet that includes a project column, so create a copy of the sample sheet called UploadList.csv and add the `Sample_Project` column ourselves.

If you would like to use this parser you will also need to create this new file and `Sample_Project` column.

## File Structure

Please verify your file structure is correct.

```
.
├── CopyComplete.txt
├── UploadList.csv
├── Analysis
│   └── 1
│       └── Data
│           └── fastq
│               ├── sample1_S1_L001_R1_001.fastq.gz
│               ├── sample1_S1_L001_R2_001.fastq.gz
│               ├── sample2_S1_L001_R1_001.fastq.gz
│               ├── sample2_S1_L001_R2_001.fastq.gz
│               ├── sample3_S1_L001_R1_001.fastq.gz
│               └── sample3_S1_L001_R2_001.fastq.gz
```

Example files can be found: `/example_sample_sheets/miseq_run/`

## Preparing your nextseq2000 upload list

Before using the uploader, you must prepare your sequencing run with IRIDA-specific project IDs.

Copy and rename the CSV file made by the software to `UploadList.csv` (It will have a name something like `NGS-1001 BCLconvert.csv`)

Then add the `Sample_Project` column to the `[BCLConvert_Data]` table.

An example completed `UploadList.csv` with the `Sample_Project` column filled in looks like:

```
[Header]
FileFormatVersion,2
Run Name,NGS1001
InstrumentPlatform,NextSeq1k2k
InstrumentType,NextSeq2000

[Reads]
Read1Cycles,101
Read2Cycles,101
Index1Cycles,8
Index2Cycles,8

[BCLConvert_Settings]
SoftwareVersion,3.5.8
AdapterRead1,CTGTCTTCTCTCTC
AdapterRead2,CGTCTCTCTCTCTC

[BCLConvert_Data]
Sample_ID,Index,Index2,Sample_Project
sample1,ATCGAAA,ATCGAAA,1
sample2,ATCGAAA,ATCGAAA,1
sample3,ATCGAAA,ATCGAAA,2
```