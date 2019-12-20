# SirMordred [![Build Status](https://travis-ci.org/chaoss/grimoirelab-sirmordred.svg?branch=master)](https://travis-ci.org/chaoss/grimoirelab-sirmordred)[![Coverage Status](https://coveralls.io/repos/github/chaoss/grimoirelab-sirmordred/badge.svg?branch=master)](https://coveralls.io/github/chaoss/grimoirelab-sirmordred?branch=master)

SirMordred is the tool used to coordinate the execution of the GrimoireLab platform, via two main configuration files, the `setup.cfg` and `projects.json`, which are summarized below,

## Setup.cfg

The setup file holds the configuration to arrange all process underlying GrimoireLab. It is composed of sections which allow to define the general settings such as which phases
to activate (e.g., collection, enrichment) and where to store the logs, as well as the location and credentials for SortingHat and the ElasticSearch instances where the raw and enriched data 
is stored. Furthermore, it also includes backend sections to set up the parameters used by Perceval to access the software development tools (e.g., GitHub tokens, gerrit username) and fetch their data.

### [es_collection] 

 * **arthur** (bool: False): Use arthur for collecting items from perceval
 * **arthur_url** (str: None): URL for the arthur service
 * **password** (str: None): Password for connection to Elasticsearch
 * **redis_url** (str: None): URL for the redis service
 * **url** (str: http://172.17.0.1:9200): Elasticsearch URL (**Required**)
 * **user** (str: None): User for connection to Elasticsearch
### [es_enrichment] 

 * **autorefresh** (bool: True): Execute the autorefresh of identities
 * **autorefresh_interval** (int: 2): Time interval (days) to autorefresh identities
 * **password** (str: None): Password for connection to Elasticsearch
 * **url** (str: http://172.17.0.1:9200): Elasticsearch URL (**Required**)
 * **user** (str: None): User for connection to Elasticsearch
### [general] 

 * **bulk_size** (int: 1000): Number of items to write in Elasticsearch using bulk operations
 * **debug** (bool: True): Debug mode (logging mainly) (**Required**)
 * **logs_dir** (str: logs): Directory with the logs of sirmordred (**Required**)
 * **min_update_delay** (int: 60): Short delay between tasks (collect, enrich ...)
 * **scroll_size** (int: 100): Number of items to read from Elasticsearch when scrolling
 * **short_name** (str: Short name): Short name of the project (**Required**)
 * **update** (bool: False): Execute the tasks in loop (**Required**)
 * **aliases_file** (str: ./aliases.json): JSON file to define aliases for raw and enriched indexes
 * **menu_file** (str: ./menu.yaml): YAML file to define the menus to be shown in Kibiter
 * **global_data_sources** (list: bugzilla, bugzillarest, confluence, discourse, gerrit, jenkins, jira): List of data sources collected globally, they are declared in the section 'unknown' of the projects.json
 * **retention_time** (int: None): the maximum number of minutes wrt the current date to retain the data
### [panels] 

 * **community** (bool: True): Include community section in dashboard
 * **kibiter_default_index** (str: git): Default index pattern for Kibiter
 * **kibiter_time_from** (str: now-90d): Default time interval for Kibiter
 * **kibiter_url** (str): Kibiter URL (**Required**)
 * **kibiter_version** (str: None): Kibiter version
 * **kafka** (bool: False): Include KIP section in dashboard
 * **github-repos** (bool: False): Enable GitHub repo stats menu. Note that if enabled, github:repo sections in the setup.cfg and projects.json should be declared
 * **gitlab-issues** (bool: False): Enable GitLab issues menu
 * **gitlab-merges** (bool: False): Enable GitLab merge requests menu
 * **mattermost** (bool: False): Enable Mattermost menu
 * **code-license** (bool: False): Enable code license menu. Note that if enabled, colic sections in the setup.cfg and projects.json should be declared
 * **code-complexity** (bool: False): Enable code complexity menu. Note that if enabled, cocom sections in the setup.cfg and projects.json should be declared
 * **strict** (bool: True): Enable strict panels loading
 * **contact** (str: None): Support repository URL
### [phases]

 * **collection** (bool: True): Activate collection of items (**Required**)
 * **enrichment** (bool: True): Activate enrichment of items (**Required**)
 * **identities** (bool: True): Do the identities tasks (**Required**)
 * **panels** (bool: True): Load panels, create alias and other tasks related (**Required**)
### [projects] 

 * **projects_file** (str: projects.json): Projects file path with repositories to be collected grouped by projects
 * **projects_url** (str: None): Projects file URL, the projects_file is required to store the file locally
### [sortinghat] 

 * **affiliate** (bool: True): Affiliate identities to organizations (**Required**)
 * **autogender** (bool: False): Add gender to the profiles (executes autogender)
 * **autoprofile** (list: ['customer', 'git', 'github']): Order in which to get the identities information for filling the profile (**Required**)
 * **database** (str: sortinghat_db): Name of the Sortinghat database (**Required**)
 * **host** (str: mariadb): Host with the Sortinghat database (**Required**)
 * **identities_api_token** (str: None): API token for remote operation with GitHub and Gitlab
 * **identities_export_url** (str: None): URL in which to export the identities in Sortinghat
 * **identities_file** (list: []): File path with the identities to be loaded in Sortinghat
 * **identities_format** (str: sortinghat): Format of the identities data to be loaded
 * **load_orgs** (bool: False): 
 * **matching** (list: ['email']): Algorithm for matching identities in Sortinghat (**Required**)
 * **orgs_file** (str: None): File path with the organizations to be loaded in Sortinghat
 * **password** (str: ): Password to access the Sortinghat database (**Required**)
 * **reset_on_load** (bool: False): Unmerge and remove affiliations for all identities on load
 * **sleep_for** (int: 3600): Delay between task identities executions (**Required**)
 * **strict_mapping** (bool: True): rigorous check of values in identities matching (i.e, well formed email addresses)
 * **unaffiliated_group** (str: Unknown): Name of the organization for unaffiliated identities (**Required**)
 * **user** (str: root): User to access the Sortinghat database (**Required**)
## [backend-name:tag] (tag is optional)

* **collect** (bool: True): enable/disable collection phase
* **raw_index** (str: None): Index name in which to store the raw items (**Required**)
* **enriched_index** (str: None): Index name in which to store the enriched items (**Required**)
* **studies** (list: []): List of studies to be executed
* **backend-param-1**: ..
* **backend-param-2**: ..
* **backend-param-n**: ..

The template of a backend section is shown above. 
Further information about Perceval backends parameters are available at:

* Params details: http://perceval.readthedocs.io/en/latest/perceval.backends.core.html
* Examples: https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

Note that some backend sections allow to specify specific enrichment options, which are listed below.

##### [jenkins]
* **node_regex**: regular expression for extracting node name from `builtOn` field. This
  regular expression **must contain at least one group**. First group will be used to extract
  node name. More groups are allowed but not used to extract anything else.
## [studies-name:tag] (tag is optional)

* **study-param-1**: ..
* **study-param-2**: ..
* **study-param-n**: ..

A template of a study section is shown above. A complete list of studies parameters is available at:

* https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

## Projects.json

The projects.json aims at describing the repositories grouped by project that will be shown on the dashboards.

The project file enables the users to list the instances of the software development tools to analyse, such
as local and remote Git repositories, the URLs of GitHub and GitLab issue trackers and the name of Slack channels.
Furthermore, it also allows the users to organize these instances into nested groups, which structure is reflected in
the visualization artifacts (i.e., documents and dashboards). Groups can be useful to represent projects within a single
company, sub-projects within a large project such as Linux and Eclipse, or the organizations within a collaborative project.

1. First level: project names
2. Second level: data sources and metadata
3. Third level: data source URLs

There are some filters and a special section:
* Filter `--filter-no-collection=true`: This filter is used to show old enriched data within the dashboards from
repositories that don't exist anymore in upstream.
* Filter `--filter-raw` and the section `unknown`: The data sources will only collected at the section `unknown`
but this allow to add the same source in different sections to enrich using the filter `--filter-raw`.
* Section `unknown`: If the data source is only under this section it will be enriched as project `main`.
```
{
    "Chaoss": {
        "gerrit": [
            "gerrit.chaoss.org --filter-raw=data.projects:CHAOSS"
        ]
        "git": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ],
        "github": [
            "https:/github.com/chaoss/grimoirelab-perceval --filter-no-collection=true",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    },
    "GrimoireLab": {
        "gerrit": [
            "gerrit.chaoss.org --filter-raw=data.projects:GrimoireLab"
        ],
        "meta": {
            "title": "GrimoireLab",
            "type": "Dev",
            "program" : "Bitergia",
            "state": "Operating"
        },
    }
    "unknown": {
        "gerrit": [
            "gerrit.chaoss.org"
        ],
        "confluence": [
            "https://wiki.chaoss.org"
        ]
}
```
In the projects.json above:
* The data included in the repo `gerrit.chaoss.org` will be collected entirely since the
repo is listed in the `unknown` section. However only the project `GrimoireLab` will be enriched as declared in the
`GrimoireLab` section.
* In the section `Chaoss` in the data source `github` the repository `grimoirelab-perceval` is not collected for
raw index but it will enriched in the enriched index.
* In the section `GrimoireLab` the metadata will showed in the enriched index as extra fields.
* In the section `unknown` the data source `confluence` will be enriched as the project `main`.

### Supported data sources

These are the data sources GrimoireLab supports:
- askbot: Questions and answers from Askbot site
- bugzilla: Bugs from Bugzilla
- bugzillarest: Bugs from Bugzilla server (>=5.0) using its REST API
- confluence: contents from Confluence
- crates: packages from Crates.io
- discourse: Topics from Discourse
- dockerhub: Repositories info from DockerHub
- functest: Tests from functest
- gerrit: Reviews from Gerrit
- git: Commits from Git
- github: Issues and PRs from GitHub
- gitlab: Issues and MRs from GitLab
- google_hits: number of hits for a set of keywords from Google
- groupsio: messages from Groupsio
- hyperkitty: Messages from a HyperKitty
- jenkins: Builds from a Jenkins
- jira: Issues data from JIRA issue trackers
- kitsune: Questions and answers from KitSune
- mattermost: Messages from Mattermost channels
- mbox: Messages from MBox files
- mediawiki: Pages and revisions from MediaWiki
- meetup: Events from Meetup groups
- mozillaclub: Events from Mozillaclub
- nntp: Articles from NNTP newsgroups
- phabricator: Tasks from Phabricator
- pipermail: Messages from Pipermail
- puppetforge: Modules and their releases from Puppet's forge
- redmine: Issues from Redmine
- remo: Events, people and activities from ReMo
- rss: Entries from RSS feeds
- slack: Messages from Slack channels
- stackexchange: Questions, answers and comments from StackExchange
- supybot: Messages from Supybot log files
- telegram: Messages from Telegram
- twitter: Messages from Twitter

The following sub-sections show how the data sources that is not an URL must be included in the data
sources file in order to be analyzed.

#### gitlab

GitLab issues and merge requests need to be configured in two different sections.

```
{
    "Chaoss": {
        "gitlab:issue": [
            "https://gitlab.com/Molly/first",
            "https://gitlab.com/Molly/second"
        ],
        "gitlab:merge": [
            "https://gitlab.com/Molly/first",
            "https://gitlab.com/Molly/second"
        ],
    }
}
```

If a given GitLab repository is under more than 1 level, all the slashes `/` starting from the second level have to be
replaced by `%2F`. For instance, for a repository with a structure similar to this one
`https://gitlab.com/Molly/lab/first`.

```
{
    "Chaoss": {
        "gitlab:issue": [
            "https://gitlab.com/Molly/lab%2Ffirst"
        ],
        "gitlab:merge": [
            "https://gitlab.com/Molly/lab%2Ffirst"
        ],
    }
}
```


#### mbox

For mbox files, it is needed the name of the mailing list and the path where the mboxes can be found. In the example
below, the name of the mailing list is set to "mirageos-devel".

```
{
    "Chaoss": {
        "mbox": [
            "mirageos-devel /home/bitergia/mbox/mirageos-devel/"
        ]
    }
}
```

#### meetup

For meetup groups it is only needed the identifier of the meetup group.

```
{
    "Chaoss": {
        "meetup": [
        "Alicante-Bitergia-Users-Group",
        "South-East-Bitergia-User-Group"
        ]
    }
}
```


#### nntp

The way to setup netnews is adding the server and the news channel to be monitored. In the example below,
the `news.myproject.org` is the server name.

```
{
    "Chaoss": {
        "nntp": [
            "news.myproject.org mozilla.dev.tech.crypto.checkins",
            "news.myproject.org mozilla.dev.tech.electrolysis",
            "news.myproject.org mozilla.dev.tech.gfx",
            "news.myproject.org mozilla.dev.tech.java"
            ]
    }
}
```

#### slack

The information needed to monitor slack channels is the channel id.

```
{
    "Chaoss": {
        "slack": [
            "A195YQBLL",
            "A495YQBM2"
        ]
    }
}
```

#### supybot

For supybot files, it is needed the name of the IRC channel and the path where the logs can be found. In the example
below, the name of the channel is set to "irc://irc.freenode.net/atomic".

```
{
    "Chaoss": {
        "supybot": [
            "irc://irc.freenode.net/atomic /home/bitergia/irc/percevalbot/logs/ChannelLogger/freenode/#atomic"
        ]
    }
}
```

#### twitter

For twitter it is only needed the name of the hashtag.

```
{
    "Chaoss": {
        "twitter": [
            "bitergia"
        ]
}
```

## Micro Mordred

Micro Mordred is a simplified version of Mordred which omits the use of its scheduler. Thus, Micro Mordred allows to run single Mordred tasks (e.g., raw collection, enrichment) per execution.

Micro Mordred is located in the [/utils](https://github.com/chaoss/grimoirelab-sirmordred/tree/master/utils/micro.py) folder of this same repository. It can be executed via command line, its parameters are summarized below:
```
--debug: execute Micro Mordred in debug mode

--raw: activate raw task
--arthur: use Arthur to collect the raw data

--enrich: activate enrich task

--identities: activate merge identities task

--panels: activate panels task

--cfg: path of the onfiguration file
--backends: list of cfg sections where the active tasks will be executed
```

Examples of possible executions are shown below:
```
cd .../grimoirelab-sirmordred/utils/
micro.py --raw --enrich --cfg ./setup.cfg --backends git #  execute the Raw and Enrich tasks for the Git cfg section
micro.py --panels # execute the Panels task to load the Sigils panels to Kibiter
``` 

## Getting started

SirModred relies on ElasticSearch, Kibiter and MySQL/MariaDB. The current versions used are:
- ElasticSearch 6.1.0
- Kibiter 6.1.4
- MySQL/MariaDB (5.7.24/10.0)
There are 3 options to get started with SirMordred:

### Source code

You will need to install ElasticSearch (6.1.0), Kibiter (6.1.4) and a MySQL/MariaDB database (5.7.24/10.0), and the following components:

- [SirModred](https://github.com/chaoss/grimoirelab-sirmordred)
- [ELK](https://github.com/chaoss/grimoirelab-elk)
- [King Arthur](https://github.com/chaoss/grimoirelab-kingarthur)
- [Graal](https://github.com/chaoss/grimoirelab-graal)
- [Perceval](https://github.com/chaoss/grimoirelab-perceval)
- [Perceval for Mozilla](https://github.com/chaoss/grimoirelab-perceval-mozilla)
- [Perceval for OPNFV](https://github.com/chaoss/grimoirelab-perceval-opnfv)
- [Perceval for Puppet](https://github.com/chaoss/grimoirelab-perceval-puppet)
- [Perceval for FINOS](https://github.com/Bitergia/grimoirelab-perceval-finos)
- [SortingHat](https://github.com/chaoss/grimoirelab-sortinghat)
- [Sigils](https://github.com/chaoss/grimoirelab-sigils)
- [Kidash](https://github.com/chaoss/grimoirelab-kidash)
- [Toolkit](https://github.com/chaoss/grimoirelab-toolkit)
- [Cereslib](https://github.com/chaoss/grimoirelab-cereslib)
- [Manuscripts](https://github.com/chaoss/grimoirelab-manuscripts)

### Source code and docker

You will have to install the GrimoireLab components listed above, and use the following docker-compose to have ElasticSearch, Kibiter and MariaDB.
Note that you can omit the `mariadb` section in case you have MySQL/MariaDB already installed in your system.

```
elasticsearch:
  restart: on-failure:5
  image: bitergia/elasticsearch:6.1.0-secured
  command: elasticsearch -Enetwork.bind_host=0.0.0.0 -Ehttp.max_content_length=2000mb
  environment:
    - ES_JAVA_OPTS=-Xms2g -Xmx2g
  ports:
    - 9200:9200

kibiter:
  restart: on-failure:5
  image: bitergia/kibiter:secured-v6.1.4-5
  environment:
    - PROJECT_NAME=Development
    - NODE_OPTIONS=--max-old-space-size=1000
    - ELASTICSEARCH_URL=https://elasticsearch:9200
  links:
    - elasticsearch
  ports:
    - 5601:5601
    
mariadb:
  restart: on-failure:5
  image: mariadb:10.0
  expose:
    - "3306"
  ports:
    - "3306:3306"
  environment:
    - MYSQL_ROOT_PASSWORD=
    - MYSQL_ALLOW_EMPTY_PASSWORD=yes
    - MYSQL_DATABASE=test_sh
  command: --wait_timeout=2592000 --interactive_timeout=2592000 --max_connections=300
  log_driver: "json-file"
  log_opt:
      max-size: "100m"
      max-file: "3"
```

### Only docker

Follow the instruction in the GrimoireLab tutorial to have [SirMordred in a container](https://chaoss.github.io/grimoirelab-tutorial/sirmordred/container.html)


### Setting up a Pycharm dev environment

This section provides details about how to set up a dev environment using PyCharm. The first step consists in forking
the GitHub repos below and cloning them to a target local folder (e.g., `sources`).

- [SirModred](https://github.com/chaoss/grimoirelab-sirmordred)
- [ELK](https://github.com/chaoss/grimoirelab-elk)
- [King Arthur](https://github.com/chaoss/grimoirelab-kingarthur)
- [Graal](https://github.com/chaoss/grimoirelab-graal)
- [Perceval](https://github.com/chaoss/grimoirelab-perceval)
- [Perceval for Mozilla](https://github.com/chaoss/grimoirelab-perceval-mozilla)
- [Perceval for OPNFV](https://github.com/chaoss/grimoirelab-perceval-opnfv)
- [Perceval for Puppet](https://github.com/chaoss/grimoirelab-perceval-puppet)
- [Perceval for FINOS](https://github.com/Bitergia/grimoirelab-perceval-finos)
- [SortingHat](https://github.com/chaoss/grimoirelab-sortinghat)
- [Sigils](https://github.com/chaoss/grimoirelab-sigils)
- [Kidash](https://github.com/chaoss/grimoirelab-kidash)
- [Toolkit](https://github.com/chaoss/grimoirelab-toolkit)
- [Cereslib](https://github.com/chaoss/grimoirelab-cereslib)
- [Manuscripts](https://github.com/chaoss/grimoirelab-manuscripts)


Each local repo should have two `remotes`: `origin` points to the forked repo, while `upstream` points to the original CHAOSS repo. An example
is provided below.
```
~/sources/perceval$ git remote -v
origin	https://github.com/valeriocos/perceval (fetch)
origin	https://github.com/valeriocos/perceval (push)
upstream	https://github.com/chaoss/grimoirelab-perceval (fetch)
upstream	https://github.com/chaoss/grimoirelab-perceval (push)
```

In order to add a remote to a Git repository, you can use the following command:
```
~/sources/perceval$ git remote add upstream https://github.com/chaoss/grimoirelab-perceval
```

Then, you can download the [PyCharm community edition](https://www.jetbrains.com/pycharm/download/#section=linux), and create a project in the 
grimoirelab-sirmordred directory. PyCharm will automatically create a virtual env, where you should install the dependencies listed in each 
requirements.txt, excluding the ones concerning the grimoirelab components.

To install the dependencies, you can click on `File` -> `Settings` -> `Project` -> `Project Interpreter`, and then the `+` located on the top right corner (see figure below).

![captura_22](https://user-images.githubusercontent.com/6515067/63195511-12299d80-c073-11e9-9774-5f274891720a.png)

Later, you can add the dependencies to the grimoirelab components via `File` -> `Settings` -> `Project` -> `Project Structure`. 
The final results should be something similar to the image below.

![captura_23](https://user-images.githubusercontent.com/6515067/63195579-4b620d80-c073-11e9-888b-3cdb67c04523.png)

Finally, you can use the docker-compose shown at Section [source-code-and-docker](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/README.md#source-code-and-docker), define a [setup.cfg](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/setup.cfg) and [projects.json](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/projects.json), and
run the following commands, which will collect and enrich the data coming from the git and cocom sections and upload the corresponding panels to Kibiter:
```
micro.py --raw --enrich --cfg ./setup.cfg --backends git cocom
micro.py --panels --cfg ./setup.cfg
```

Optionally, you can create a configuration in PyCharm to speed up the executions (`Run` -> `Edit configuration` -> `+`). The final results should be something similar to the image below.

![captura_24](https://user-images.githubusercontent.com/6515067/63195767-ccb9a000-c073-11e9-805a-e828a3ce1dc9.png)
 