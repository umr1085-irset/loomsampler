# loomsampler

A straightforward script to randomly sample items (usually cells) from a [loom](http://loompy.org/) file.

## Python environment requirements

A Conda environment file can be found here: `src/env.yml`

## Slurm compatible bash launcher

The script can be launched using Slurm:

```properties
sbatch launcher.sh
```

## Representativity

A minimum number of items can be passed to the script with the `-m, --minimum` option. Default value is 10.

For a given combination, if a number of items lower than this minimum value were to be sampled, use the minimum value instead, or as many items as possible if there are less items available.