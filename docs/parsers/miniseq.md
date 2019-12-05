## File Structure

The file structure for a miniseq / iseq run should be correct by default, but if you are having problems uploading, please verify your file structure is correct.

```
.
├── CompletedJobInfo.xml
├── Alignment_1
│   └── <DateTimeFolder>
│       └── Fastq
│           ├── sample1_S1_L001_R1_001.fastq.gz
│           ├── sample1_S1_L001_R2_001.fastq.gz
│           ├── sample2_S1_L001_R1_001.fastq.gz
│           ├── sample2_S1_L001_R2_001.fastq.gz
│           ├── sample3_S1_L001_R1_001.fastq.gz
│           ├── sample3_S1_L001_R2_001.fastq.gz
│           └── <other files>
├── SampleSheet.csv
└── <other files>
```

Example files can be found: `/example_sample_sheets/miniseq_run/`

## Preparing your miniseq / iseq sample sheet
Before using the uploader, you must prepare your sequencing run with IRIDA-specific project IDs. You must do this manually after a run completes by editing `SampleSheet.csv` with Microsoft Excel or Windows Notepad.

Simply add the `Sample_Project` column to the `[Data]` header, and add the IRIDA project number.

An example, completed miniseq `SampleSheet.csv` with the `Sample_Project` column filled in looks like:

```
[Header]
Local Run Manager Analysis Id,3003
Date,10/27/2018
Experiment Name,20181026-MiniSeqTest
Workflow,GenerateFastQWorkflow
Description,Auto generated sample sheet.  Used by workflow module to kick off Isis analysis
Chemistry,Amplicon

[Reads]
251
251

[Settings]
Adapter,ATCGATCGATCG

[Data]
Sample_ID,Sample_Name,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project
sample1-3003,sample1,ATCGAAA,N801,ATCGAAA,S801,1
sample2-3003,sample2,ATCGAAA,N801,ATCGAAA,S801,1
sample3-3003,sample3,ATCGAAA,N801,ATCGAAA,S801,1
```

Note: An iseq run will look almost the same, but a `Description` field under `[DATA]` may also be present. This is expected and the parser should function normally with the field there.