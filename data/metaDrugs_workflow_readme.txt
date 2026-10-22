*******************************************************************
MetaDrugs workflow
*******************************************************************

Data analysis pipeline for investigating drug-host-microbiome relationships in cardiometabolic disease (MetaCardis cohort). 

For questions and requests, please contact:
Sofia K. Forslund (sofia.forslund@mdc-berlin.de) 
and Till Birkner  (till.birkner@mdc-berlin.de)

*******************************************************************
Contents: 
-------------------------------------------------------------------
Data files:
metadata.tar.gz - archived cohort metadata files*
input_features.tar.gz - archived preprocessed serum and urine metabolome and gut microbiome features 
output_complete.tar.gz - archived example analysis output files for each of the input feature file
output_rerun.tar.gz - archived empty directory for generating test output files as described in this document

*Please note: Due to conflicts with Danish Data Protection laws, metadata from the Danish subset of the cohort were removed in this repository. Please reach out for a potential case-by-case access request for access to the complete set of metadata.
-------------------------------------------------------------------
Text files:
archived in feature_names.tar.gz:
atcs_names - full names for atcs drug compounds
contrast_names - full names for disease comparison groups
file_names - brief description of the files in input_features folder
gmm_names - full names of GMM modules
kegg_names - full names of KEGG modules
ko_names - full names of KO modules
metadata_names - full names of metadata features
mOTU_names - species names for metagenomics data
taxon_names - taxon names for metagenomics data
-------------------------------------------------------------------
Scripts:
-------------------------------------------------------------------
runFrame.r - main wrapper script envoking the analysis pipeline
-------------------------------------------------------------------
runFrame_rel_comb.r - script calculating drug combination effects
runFrame_rel.r - script calculating dosage effects 
testCombPresenceSeparate.r - testing of significant drug combination effects beyond single drug effects
testDosagePresenceSeparate.pl - testing of significant drug dosage effects beyond single drug effects
testDosagePresenceSeparateNegative.pl - testing of unique drug dosage effects beyond single drug effects
-------------------------------------------------------------------
prettifyResults_uncollapsed.pl - wrapper scripts to create and format a single analysis output file
makeTables.r - wrapper script to make excel tables with analysis results
-------------------------------------------------------------------
Example output file:
-------------------------------------------------------------------
output_all_formatted_noc_uncollapsed_complete.tsv - contains all disease-drug-host-microbiome feature analysis results in one place.
*******************************************************************

*******************************************************************
Running the pipeline
*******************************************************************
Requirements: 
R version >v4.0.0
perl version >v5.16.3
Download metadeconfoundR package at: https://github.com/TillBirkner/metadeconfoundR
Other R packages: orddom, sets, reshape2, plyr, lmtest, xlsx

To run the pipeline, please extract the archived data files into the master directory.

1) Perform feature deconfounding and drug and disease association analysis with host and microbiome features for each feature file in the input_features folder separately. 

Note: the pipeline takes a long time to run (>1h per file scaling with file size). For a test, we recommend to run on the smallest feature file, e.g. input_features/hub.cellcount.motu.Domain.v2.data.frame.r, which should take about 15 min using 4 cores.

Run runFrame.r script for each feature file separately with input parameters:
[1] path to metadata folder
[2] path to input feature file
[3] output file name
[4] [optional] number of cores 

Example run: (~10-15 min)
Rscript runFrame.r metadata/ input_features/hub.cellcount.motu.Domain.v2.data.frame.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r 4

-------------------------------------------------------------------

2) For each output file, perform the additional analysis of which drug combinations can be shown to be fully synergistic. (< 10 sec)

Run testCombPresenceSeparate.pl script for each output file separately with input parameters:
[1] path to output file
[2] output file name

Example run:
perl testCombPresenceSeparate.pl output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_comb_effects

3) For each output file from (2), perform second post-hoc testing step. (< 10 sec)

Run runFrame_rel_comb.r script for each output file separately with input parameters:
[1] path to metadata folder
[2] input feature file
[3] drug combination feature results file
[4] name of output file

Example run:
Rscript runFrame_rel_comb.r metadata/ input_features/hub.cellcount.motu.Domain.v2.data.frame.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_comb_effects output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_comb_effects_tested

4) For each output file, perform the additional analysis of which dosage-level drug results show effect beyong drug intake. (< 10 sec)

Run  testDosagePresenceSeparate.pl script for each output file separately with input parameters:
[1] path to output file
[2] output file name

Example run:
perl testDosagePresenceSeparate.pl output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_dosage_effects

5) For each output file from (4), perform second post-hoc testing step. (< 10 sec)

Run runFrame_rel.r script for each output file separately with input parameters:
[1] path to metadata folder
[2] input feature file
[3] drug combination feature results file
[4] name of output file

Example run:
Rscript runFrame_rel.r metadata/ input_features/hub.cellcount.motu.Domain.v2.data.frame.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_dosage_effects output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_dosage_effects_tested

6) Perform analysis of features detectable only through dosage analysis, not drug presence/absence analysis. (< 10 sec)

Run  testDosagePresenceSeparateNegative.pl script for each output file separately with input parameters:
[1] path to output file
[2] output file name

Example run:
perl testDosagePresenceSeparateNegative.pl output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r output_rerun/hub.cellcount.motu.Domain.v2.data.frame.r.output.r_dosage_only_effects

-------------------------------------------------------------------

7) Run wrapper script to create one output file for all analyses. (< 10 sec)

File prettifyResultsFiles_uncollapsed.pl reads feature names from the above mentioned text files and takes list of output files as input. 
Script creates a file named output_all_formatted_noc_uncollapsed.tsv as output.

Example run: 
perl prettifyResultsFiles_uncollapsed.pl output_rerun/*output.r

8) Make excel tables with results. (~1-2 min)

Example run:
Rscript makeTables.r output_all_formatted_noc_uncollapsed.tsv

This script creates several excel files with drug intake, dosage, combination analyses, etc.
