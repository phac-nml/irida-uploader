# MiSeq (Software Control Version 2.6)

## File Structure

The file structure for a miseq run should be correct by default, but if you are having problems uploading, please verify your file structure is correct.

```
.
├── CompletedJobInfo.xml
├── Data
│   └── Intensities
│       └── BaseCalls
│           ├── sample1_S1_L001_R1_001.fastq.gz
│           ├── sample1_S1_L001_R2_001.fastq.gz
│           ├── sample2_S1_L001_R1_001.fastq.gz
│           ├── sample2_S1_L001_R2_001.fastq.gz
│           ├── sample3_S1_L001_R1_001.fastq.gz
│           └── sample3_S1_L001_R2_001.fastq.gz
└── SampleSheet.csv
```

Example files can be found: `/example_sample_sheets/miseq_run/`

## Preparing your miseq sample sheet
Before using the uploader, you must prepare your sequencing run with IRIDA-specific project IDs. You can either enter the project IDs when you're creating your sample sheet using the Illumina Experiment Manager or after creating the sample sheet by editing `SampleSheet.csv` with Microsoft Excel or Windows Notepad.

An example, completed `SampleSheet.csv` with the `Sample_Project` column filled in looks like:

```
[Header]
IEMFileVersion,4
Investigator Name,Investigator 1
Experiment Name,Experiment
Date,2015-05-14
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,Nextera XT
Description,
Chemistry,Amplicon

[Reads]
251
251

[Settings]
ReverseComplement,0
Adapter,ATCGATCGATCG

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
sample1,,plate1,A01,N801,ATCGAAA,S801,ATCGAAA,1,
sample2,,plate1,A01,N801,ATCGAAA,S801,ATCGAAA,1,
sample3,,plate1,A01,N801,ATCGAAA,S801,ATCGAAA,1,
```