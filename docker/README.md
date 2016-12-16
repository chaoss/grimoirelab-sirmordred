# Mordred

## Intro

Mordred Docker container will help you to deploy a Bitergia Analytics dashboard
using a set of configuration files. In the documentation below we assume you
already have a running MariaDB server, ElasticSearch 2.2 and Kibiter (our fork for Kibana
which container is bitergia/kibiter:4.4.1). If you don't want to install Kibiter
just use Kibana 4.4.1, but you'll miss the improvements we added ;).

The different files we will have to modify are:
- setup.cfg: Mordred's configuration file
- requirements.cfg: file with the versions of the components we will use
- projects.json: JSON file with projects and his repositories
- orgs_file.json: a Sorting Hat file format with companies/organizations and domains
- docker-compose.yml: easy, the file where the container is specified

Let's start hacking!.

## setup.cfg

The Mordred's configuration file have several sections but don't panic, it is
easier than you may think at a glance.

First, we define the project name, where the projects file will be. The only thing
you need to modify here is the "short_name".
```
[general]
short_name = Grimoire
update = false
debug = false
logs_dir = /home/bitergia/logs

[projects]
projects_file = /home/bitergia/conf/projects.json
```

The following two sections are used to store the 'raw' information we will
collect from the different data sources and to produce the 'enriched' data
we will create based on the 'raw' plus Sorting Hat information. In our example
we simply use the local ElasticSearch.

```
[es_collection]
url = http://elasticsearch:9200
user =
password =

[es_enrichment]
url = http://elasticsearch:9200
user =
password =
# Refresh identities and projects for all items after enrichment
autorefresh = false
studies = true
```

One of the key pieces of the Bitergia Analytics dashboard is Sorting Hat. In
the following example it is running in a container named 'mariadb'. If you have
it, don't need to modify anything for the demo.

The parameters 'matching' and 'autoprofile' are a essential part of Sorting Hat
functionality, if you wanna to learn more go to its command line help after
installing it or to https://github.com/MetricsGrimoire/sortinghat
```
[sortinghat]
host = mariadb
user = root
password =
database = grimoire_sh
load_orgs = true
orgs_file = /home/bitergia/conf/orgs_file.json
#matching  see: sortinghat unify --help
matching = email-name, github
autoprofile = customer, git, github
sleep_for = 86400
bots_names =
```

We can also enable of disable the different phases. Let's start will all of
them enabled.
```
[phases]
collection = true
identities = true
enrichment = true
panels = true
```

Last but not least, for every data source Bitergia Analytics supports, it is
needed to include the name of both the raw and enriched indices. These will
be use to contain the information in the Elastic Search server. Besides that
some extra parameters are needed for some data sources, in this case 'github'
needs a 'backend-token'. Get your own and include it here.
```
[git]
raw_index = git_grimoire_161116
enriched_index = git_grimoire_161116_enriched_161209b

[github]
raw_index = github_grimoire_161116
enriched_index = github_grimoire_161116_enriched_161123a
backend-token = [your github token]
```

## requirements.cfg

Place here our latest release file. Current one is named 'atom_girl' and
you can get it from https://github.com/Bitergia/mordred/blob/master/docker/unified_releases/atom_girl

This is the content
```
#!/bin/bash
SORTINGHAT='cc07e9bad23df2fbda785418773ab5eb0cc2fa8e'
GRIMOIREELK='0.17-1-g9c08bb2'
MORDRED='1.1.1-10-g1334b1c'
VIZGRIMOIREUTILS='f5db1da9982484ec7d437d69358e69f609128717'
PERCEVAL='0.4.0-46-g555adb1'
PERCEVAL_MOZILLA='d2298b851d7ac69f253b45018167c7356e24f935'
PANELS='fa236773c8c7b4d39c5c4dc34df7ba761569f076'
```

## projects.json and orgs_file

The projects.json file contains a list of projects and the data source associated
to it. In the example below git and github repositories associated to the project
named 'GrimoireLab'
```
{
    "GrimoireLab": {
            "github": [
                "https://github.com/grimoirelab/arthur",
                "https://github.com/grimoirelab/GrimoireELK",
                "https://github.com/grimoirelab/grimoirelab.github.io",
                "https://github.com/grimoirelab/panels",
                "https://github.com/grimoirelab/perceval",
                "https://github.com/grimoirelab/use_cases"
            ],
            "git": [
                "https://github.com/grimoirelab/arthur",
                "https://github.com/grimoirelab/GrimoireELK.git",
                "https://github.com/grimoirelab/grimoirelab.github.io.git",
                "https://github.com/grimoirelab/panels.git",
                "https://github.com/grimoirelab/perceval.git",
                "https://github.com/grimoirelab/use_cases.git"
            ]
        }
}
```

The orgs file contains a list of internet domains and organizations in
Sortinghat format. For the purpose of this demo just download it from
https://github.com/Bitergia/mordred/blob/master/docker/example_conf/orgs_file.json

## docker-compose.yml

So, now we have the input Mordred needs, let's set up its container.
```
mordred:
  image: bitergia/mordred:latest
  volumes:
    - /home/luis/demo/conf/:/home/bitergia/conf
    - /tmp/:/home/bitergia/logs
  links:
    - mariadb
    - elasticsearch

mariadb:
  restart: "always"
  image: mariadb:10.0
  expose:
    - "3306"
  ports:
    - "3306:3306"
  environment:
    - MYSQL_ROOT_PASSWORD=
    - MYSQL_ALLOW_EMPTY_PASSWORD=yes

elasticsearch:
  restart: "always"
  image: elasticsearch:2.2
  command: elasticsearch -Des.network.bind_host=0.0.0.0 -Dhttp.max_content_length=2000mb
  ports:
    - "9200:9200"

kibana:
  image: bitergia/kibiter:4.4.1
  environment:
    - PROJECT_NAME=mytest
    - NODE_OPTIONS=--max-old-space-size=200
  links:
    - elasticsearch
  ports:
    - "8081:5601"

kibana-ro:
  image: bitergia/kibiter:4.4.1-public
  environment:
    - PROJECT_NAME=mytest
    - NODE_OPTIONS=--max-old-space-size=200
  links:
    - elasticsearch
  ports:
    - "8091:5601"
```

## execute it!

Start the docker containers and the result should be available while you grab
a tea of coffee.

```
luis@hogaza ~/docker-containers/mordred » docker-compose up -d
Creating mordred_elasticsearch_1
Creating mordred_mariadb_1
Creating mordred_kibana-ro_1
Creating mordred_kibana_1
Creating mordred_mordred_1
```

- The log /tmp/mordred.log will say something like this when everything is done
```
luis@hogaza ~/docker-containers/mordred » tail -n4 /tmp/mordred.log
2016-12-16 07:22:47,449 - mordred - INFO - [github] enrichment finished in 00:00:16
2016-12-16 07:22:48,289 - mordred - INFO - [git] enrichment finished in 00:00:17
2016-12-16 07:22:52,134 - mordred - INFO - Adding dashboard menu definition
2016-12-16 07:22:52,357 - mordred - INFO - Adding dashboard menu definition
```
- now visit http://localhost:8091/
- on the left click on git, now click on the green start
- now visit http://localhost:8091/app/kibana#/dashboard/Overview, dashboards are
ready!

tip: you'll be able to edit all the dashboards using the same URL replacing the
port 8091 with 8081

## did you find any bugs?

If you found bugs or you think she is a witch, let us know by filling a bug!
```
Sir Bedevere: What makes you think she's a witch?
Peasant 3: Well, she turned me into a newt!
Sir Bedevere: A newt?
Peasant 3: [meekly after a long pause] ... I got better.
Crowd: [shouts] Burn her anyway!
```

Bitergia 2016. Software metrics for your peace of mind.
