# SirMordred


## Intro

SirMordred Docker container will help you to deploy the Bitergia Analytics dashboard
using a set of configuration files. In the documentation below we assume you
already have a running MariaDB server, ElasticSearch 2.2 and Kibiter (our fork for Kibana
which container is bitergia/kibiter:4.4.1). If you don't want to install Kibiter
just use Kibana 4.4.1, but you'll miss the improvements we added ;).

The different files we will have to modify are:
- setup.cfg: SirMordred's configuration file
- requirements.cfg: file with the versions of the components we will use
- projects.json: JSON file with projects and its repositories
- orgs_file.json: a Sorting Hat file format with companies/organizations and domains
- docker-compose.yml: easy, the file where the container is specified

Let's start hacking!.

## setup.cfg

SirMordred's configuration file have several sections but don't panic, it is
easier than you may think at a glance.

First, we define the project name. The only thing you need to modify here is
the "short_name".
```
[general]
short_name = Grimoire
update = true
debug = false
logs_dir = /home/bitergia/logs
```

You can do further adjustments, but not needed by default:

```
# to support the bitergia/kibiter:5.1.1 just change to 5
kibana = "4"
```

To increase the performance during collection and enrichment of data you
can modify the number of items that are pack in bulk packets and send to
Elasticsearch. In general it is safe to increase it to 5000 if the items
you are collection are between 1-10 KB.

```
# number of items per bulk request to Elasticsearch
bulk_size = 1000
```

During enrichment, the collect of the raw items to be enriched is done using
the scroll API. The number of items to be packed together has impact also
in the performance. 1000 is normally a safe value. The limit is 9999.

```
# number of items to get from Elasticsearch when scrolling
scroll_size = 1000
```

The "projects" section  specifies where the projects file is

```
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
orgs_file = [/home/bitergia/conf/orgs_file.json]
#matching  see: sortinghat unify --help
matching = [email-name, github]
autoprofile = [customer, git, github]
sleep_for = 86400
unaffiliated_group = Unknown
```

In order to load identities from a file or url or export the identities to a
GitHub repository, extra params are needed:

```
identities_file = [sh_identities.json]
identities_export_url = "https://github.com/<owner>/<repo>/blob/master/sh_identities.gz"
# Token with write permissions in the export GitHub repository
github_api_token = "42207XXXXXXXX"
```

For building the dashboard, sirmordred configures Kibiter. No config is needed
by default but sometimes is useful to change the default time frame is shown.

[panels]
kibiter_time_from="now-90d"
kibiter_default_index="git"

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

Place here our latest release file. Current one is named 'elasticgirl.11' and
you can get it from https://github.com/Bitergia/mordred/blob/master/docker/unified_releases/elasticgirl.12

If you don't need so much detail (it includes the different versions of the Bitergia stack) just include the name of the release in a variable named "RELEASE" as I did below:
```
#!/bin/bash
RELEASE='elasticgirl.12'
```

**NOTE**: in case you are using a version =< catwoman you'll need to use a special image of the docker image. It is called bitergia/mordred:catwoman, insted of bitergia/mordred:latest

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
a tea or coffee.

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

## upgrade to a newer version

In order to upgrade to a newer version:
- stop the mordred container (docker-compose stop)
- remove the mordred container (docker rm mordred_container)
- identify its name at https://github.com/Bitergia/mordred/blob/master/docker/unified_releases and updated the requirements.cfg file.
- deploy the new tools (docker-compose up -d)


**NOTE**: in case you are using a version =< catwoman you'll need to use a special image of the docker image. It is called bitergia/mordred:catwoman, insted of bitergia/mordred:latest


## did you find any bugs?

If you found bugs or you think she is a witch, let us know by filling a bug!
```
Sir Bedevere: What makes you think she's a witch?
Peasant 3: Well, she turned me into a newt!
Sir Bedevere: A newt?
Peasant 3: [meekly after a long pause] ... I got better.
Crowd: [shouts] Burn her anyway!
```

## Advanced features

Items to be enriched can be collected from a raw index using filters. A project can be specified as:

```
{
    "RDO": {
        "askbot": [
            "https://ask.openstack.org --filter-raw=data.tags:rdo"
        ]
    }
}
```

and to define in setup.cfg the raw index from which to get the raw items using the above filter:

```
[askbot]
raw_index = askbot_openstack_170524
enriched_index = askbot_openstack_170524_enriched_170529
es_collection_url = http://raw.elasticsearch:9200
```

Also, you can execute just one specific step in the phases of the config with "-p" param, and you can create a sample config file with the "-t" param.

All command line options can be accessed with:

```
(acs@dellx) (master *$% u=) ~/devel/mordred $ bin/mordred -h
usage: mordred [-h] [-c CONFIG_FILE] [-t CONFIG_TEMPLATE_FILE]
               [-p [PHASES [PHASES ...]]]

Mordred, the friendly friend of GrimoireELK

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config CONFIG_FILE
                        Configuration file
  -t CONFIG_TEMPLATE_FILE, --template CONFIG_TEMPLATE_FILE
                        Create template configuration file
  -p [PHASES [PHASES ...]], --phases [PHASES [PHASES ...]]
                        List of phases to execute (update is set to false)

Software metrics for your peace of mind
```


Above features are not included in this demo.


Bitergia 2017. Software metrics for your peace of mind.
