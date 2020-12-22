# Internal linking

## Setup

### Prerequsites

- Conda

### Create environment

```
    $ conda env create -f environment.yml
```

### Activate environment

```
    $ conda activate internal-linking
```

### Download Polish language for `spacy`

```
    $ python -m spacy download pl_core_news_sm
```

## Jupyter Lab

### Running

In order to run Jupyter Lab make sure you have the environment activated and then run the following command in you terminal:

```
    $ jupyter-lab
```