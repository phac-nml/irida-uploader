# Directory Upload

## File Structure

To upload using the directory parser, Organize your files according to the following
```
.
├── file_1.fastq.gz
├── file_2.fastq.gz
├── samp_F.fastq.gz
├── samp_R.fastq.gz
├── germ_f.fastq.gz
├── germ_r.fastq.gz
└── SampleList.csv

```

Example files can be found: `/example_sample_sheets/directory_run/`

## File Names

When uploading paired end reads, your file names must indicate forward/reverse.

Use the same name between files, with the difference of including `1` / `2`, `F` / `R`, `f` / `r`, as shown above.

## Preparing your sample list file
Before using the uploader, you must create a `SampleList.csv` file.

It must contain the following fields

`Sample_Name` : This is what the sample will be identified as on IRIDA after upload.

`Project_ID`: The IRIDA project the sample will be uploaded to.

`File_Forward`: Always needed, the forward read file.

`File_Reverse`: Needed for paired end reads, the reverse read file.

An example, completed `SampleList.csv` with all the columns filled in looks like:

```
[Data]
Sample_Name,Project_ID,File_Forward,File_Reverse
my-sample-1,75,file_1.fastq.gz,file_2.fastq.gz
my-sample-2,75,samp_F.fastq.gz,samp_R.fastq.gz
my-sample-3,76,germ_f.fastq.gz,germ_r.fastq.gz
```

Another example, but with only single end reads:

```
[Data]
Sample_Name,Project_ID,File_Forward,File_Reverse
my-sample-1,75,file_1.fastq.gz
my-sample-2,75,samp_F.fastq.gz
my-sample-3,76,germ_f.fastq.gz
```
