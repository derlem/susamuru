# susamuru
Our goal is to curate a NER dataset for morphologically challenging languages using Wikipedia. 

## tools (all of these are subject to change)
* python 3.6
* pipenv
* jupyter notebook

### how to create a kernel from a pipenv file (for creating 'susamuru' kernel)
* pipenv install
* pipenv shell
* python -m ipykernel install --user --name=susamuru

Now you can use our notebooks!

#### in order to remove our kernel from jupyter notebook:
* jupyter kernelspec uninstall susamuru