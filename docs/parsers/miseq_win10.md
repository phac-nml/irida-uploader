# MiSeq on Windows 10

The upgrade to Windows 10 comes with v4.0 of MiSeq Control Software (MCS) and v3.0 of Local Run Manager (LRM). The upgrade of LRM to v3.0 no longer allows sample sheets created in IEM to be uploaded before starting a run. You can still create sample sheets with IEM (ex. 1.19.1; downloadable from Illumina’s website). You can also create a sample sheet manually using a template.

Options for starting a irida uploader compatible run:

1. **Easiest option - using IEM to create a sample sheet.** A run will need to be created in local run manager by selecting "Create Run" from the LRM dashboard, then selecting the correct analysis module (ex. GenerateFASTQ). Run parameters should be entered or chosen from the drop-downs provided for "Run Name", "Description", "Library Prep Kit", "Index Kit", "Read type" (single read or paired end), number of index reads (0, 1 or 2), number of cycles for each read, and custom primer information if required.  If custom indexing is used (ie. anything not supplied by Illumina), the Library Prep Kit and Index Kit used should have Custom selected.  Once the run parameters are defined, add the appropriate number of rows to the sample table (one row per sample on the run) and then copy and paste (one column at a time) the information captured in the IEM generated sample sheet to this sample table.  The sample table includes the following columns: Sample ID, Sample Name (optional; you can duplicate the Sample ID column), Description (optional; you can list the organism), Plate Well (only for some index kits, usually TruSeq), and the Indexes used with each sample.  Forward (i5) and reverse (i7) sequences will need to be entered as text, copy and paste the exact sequence.  Once the index sequences are entered, verify that the correct number of cycles are indicated for indexing.  Then select save run and proceed to starting the MiSeq sequencing run. 

2. **Fully manual option - creating a sample sheet from template (available below).** In the Header section, adjust the Date, Library Prep Kit, Index Kit, and Description fields.  Adjust the number of reads to the number of cycles you would like.  And in the Data/Sample Table, fill out the columns with the information specific to each sample.  Save this sample sheet, create a run in LRM and upload this sample sheet.  This requires the user to know their index files and how to manipulate them.

3. **Creating sample sheet in IEM and modifying for upload**. Note this option is **not recommended** due to its complexity. Open the IEM generated sample sheet in excel and modify.  In the Header section, remove the IEMFileVersion, Investigator Name, Application, Instrument Type, Assay and Index Adapters rows.  Change the Experiment Name to GenerateFastQ_SampleSheet.  After the Date row, add another row called Module and enter GenerateFASTQ – 3.0.1.  After the Workflow row, add two rows – one called Library Prep Kit and the other called Index Kit.  The Library Prep Kit and Index Kit that you enter must match the exact string of text that Illumina uses (check how it’s written in the drop-downs or refer to page 3 of the Local Run Manager Generate FastQ Release Notes).  Additional/custom library prep kits and index kits can be added and deleted to LRM following the instructions in the Local Run Manager v3 Software Guide.  In the Settings section, remove the ReverseComplement row and add an AdvancedSetting1 row beneath the Adapter row.  In the Data/Sample Table section, some columns will need to be deleted and the remaining ones will need to be rearranged so they are in the following order: Sample_ID, Description, Index_Plate, Index_Plate_Well, I&_Index_ID, index, I5_Index_ID, index2, Sample_Project.  Once saved, create a run in LRM and upload this sample sheet.

## File Structure

The file structure of a Windows 10 MiSeq run is similar to the `miseq_v31` and `miniseq` software.

If you are having problems uploading, please verify your file structure is correct.

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

## Example sample sheet

```
[Header],,,,,,,,
Experiment Name,GenerateFastQ_SampleSheet,,,,,,,
Date,2021-01-26,,,,,,,
Module,GenerateFASTQ - 3.0.1,,,,,,,
Workflow,GenerateFASTQ,,,,,,,
Library Prep Kit,Illumina DNA Prep,,,,,,,
Index Kit,IDT-ILMN Nextera DNA UD Indexes Set A B C D - 384 Indexes,,,,,,,
Description,This is a sample sheet template,,,,,,,
Chemistry,Amplicon,,,,,,,
[Reads],,,,,,,,
151,,,,,,,,
151,,,,,,,,
[Settings],,,,,,,,
adapter,CTGTCTCTTATACACATCT,,,,,,,
AdvancedSetting1,123,,,,,,,
[Data],,,,,,,,
Sample_ID,Description,Index_Plate,Index_Plate_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project
S1,Desc1,A,A01,UDP0001,GAACTGAGCG,UDP0001,TCGTGGAGCG,Proj1
S2,Desc2,B,A02,UDP0105,CAGCAATCGT,UDP0105,TGTGATGTAT,Proj2
S3,Desc3,C,A03,UDP0209,GCTAGACTAT,UDP0209,AATACGACAT,Proj3
S4,Desc4,D,A04,UDP0313,TTAATAGCAC,UDP0313,ACCACGTCTG,Proj4
```