# susamuru
Our goal is to curate a NER dataset for morphologically challenging languages using Wikipedia. 

## tools (all of these are subject to change)
* python 3.6
* pipenv

# How to run
* First clone the repository to your computer. `git clone git@github.com:derlem/susamuru.git`
* Go to directory /susamuru/susamuru `cd susamuru/susamuru`
* Install dependencies `pipenv install`
* Change to pipenv shell `pipenv shell`
* Download the wikipedia tr pages dump. Here is the [link](https://dumps.wikimedia.org/trwiki/20190401/trwiki-20190401-pages-articles-multistream.xml.bz2)
* Extract the dump to `/susamuru/susamuru/dumps` folder.
* Now you are good to go. Start the execution with: pipenv run python susamuru.py
* After the execution, you should be able to see the output file in `susamuru/susamuru/output` folder.
