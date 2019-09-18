## File Structure

The file structure for a NextSeq run will need `bcl2fastq` run first to produce usable fastq files.
The generated structure should automatically work with the parser.

##### WARNING! If using `--batch` upload with an auto-upload script, incomplete fastq files could be uploaded if `bcl2fastq` has not finished when the upload begins.

If you are having problems uploading, please verify your file structure is correct.

```
<In this example, the run is has sequence data for project 22 and project 23
.
├── SampleSheet.md
├── Data
│   └── Intensities
│       └── BaseCalls
│           ├── 67
│           │   ├── SA20121712_S2_R1_001.fastq.gz
│           │   ├── SA20121712_S2_R2_001.fastq.gz
│           └── 68
│               ├── SA20121716_S2_R1_001.fastq.gz
│               └── SA20121716_S2_R2_001.fastq.gz
├── RTAComplete.txt
└── <other files>
```

Example files can be found: `/example_sample_sheets/nextseq_run/`

## Example NextSeq sample sheet

```
[Header]
IEMFileVersion,5
Investigator Name,Ikari Yui
Experiment Name,NGS-Adam
Date,2000-09-13
Workflow,GenerateFASTQ
Application,NextSeq FASTQ Only
Instrument Type,NextSeq/MiniSeq
Assay,Nextera XT
Index Adapters,"Nextera XT v2 Index Kit A"
Description,Contact Experiment
Chemistry,Amplicon

[Reads]
151
151

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
SA20121716,SA20121716,NGS-001 Plate FNC-7,A01,N701,TAAGGCGA,S502,ATAGAGAG,1094,Code Blue
SA20121712,SA20121712,NGS-001 Plate FNC-7,A02,N702,CGTACTAG,S502,ATAGAGAG,1094,Code Blue
```
