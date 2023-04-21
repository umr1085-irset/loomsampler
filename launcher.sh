#!/bin/bash

#SBATCH --job-name="sampling"
#SBATCH --output=out.sampling.out
#SBATCH --mem=50G
#SBATCH --cpus-per-task=1
#SBATCH --partition=sihp # cluster partition to use
#SBATCH --mail-type=ALL # receive emails for all updates
#SBATCH --mail-user=<user_email> # user email
#SBATCH --chdir=<output_directory>

FILE=/path/to/my/loom/file.loom
OUT=/path/to/my/loom/file.light.loom

#----------------------------------------------------------------------------------------------

# check if script is started via SLURM or bash
# if with SLURM: there variable '$SLURM_JOB_ID' will exist
# `if [ -n $SLURM_JOB_ID ]` checks if $SLURM_JOB_ID is not an empty string
if [ -n $SLURM_JOB_ID ];  then
    # check the original location through scontrol and $SLURM_JOB_ID
    CURRPATH=$(scontrol show job $SLURM_JOBID | awk -F= '/Command=/{print $2}')
else
    # otherwise: started with bash. Get the real location.
    CURRPATH=$(realpath $0)
fi

BASEPATH="${CURRPATH%/*/*}"
SCRIPTPATH="$BASEPATH/loomsampler.py"

. /local/env/envconda.sh # source conda
conda activate /home/genouest/irset/privaud/.conda/envs/viewersampling # activate R environment
python $SCRIPTPATH -f $FILE -o $OUT -s 20000 -t 25000 -m 10 -v 'Clusters|ArticleID' # example
