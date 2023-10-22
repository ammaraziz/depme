tools_lib = {

    # languages
    "R"          : ["R", "--version"],
    "perl"       : ["perl", "-v"],
    "python"     : ["python", "--version"],

    # mappers
    "bowtie2"    : ["bowtie2", "version"],
    "bwa"        : ["bwa", "mem"],

    # aligners
    "mafft"      : ["mafft", "--version"],
    "muscle"     : ["muscle", "--version"],
    "blast"      : ["blastn", "-version"],

    # misc

    # toolkits
    "seqkit"     : ["seqkit", "version"],
    "bcftools"   : ["bcftools", "version"],
    "bedtools"   : ["bedtools", "version"],

    # nextstrain
    "nextclade" : ["nextclade", "--version"],
    "augur"      : ["augur", "--version"],

    # workflows
    "snakemake"  : ["snakemake", "--version"],
    "nextflow"   : ["nextflow", "-version"],


}