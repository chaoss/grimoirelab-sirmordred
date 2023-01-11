# SirMordred [![Build Status](https://github.com/chaoss/grimoirelab-sirmordred/workflows/tests/badge.svg)](https://github.com/chaoss/grimoirelab-sirmordred/actions?query=workflow:tests+branch:master+event:push) [![Coverage Status](https://coveralls.io/repos/github/chaoss/grimoirelab-sirmordred/badge.svg?branch=master)](https://coveralls.io/github/chaoss/grimoirelab-sirmordred?branch=master) [![PyPI version](https://badge.fury.io/py/sirmordred.svg)](https://badge.fury.io/py/sirmordred)

SirMordred is the tool used to coordinate the execution of the GrimoireLab platform, via two main configuration files, the `setup.cfg` and `projects.json`, which are summarized in their corresponding sections.

## Contents

* [Setup.cfg](#setupcfg-)
* [Projects.json](#projectsjson-)
* [Supported data sources](#supported-data-sources-)
* [Micro Mordred](#micro-mordred-)
* [Getting started](/Getting-Started.md#getting-started-)
* [Troubleshooting](/Getting-Started.md#troubleshooting-)
* [How to](/Getting-Started.md#how-to-)


## Setup.cfg [&uarr;](#contents)

The setup file holds the configuration to arrange all processes underlying GrimoireLab. It is composed of sections that allow defining the general settings such as which phases to activate (e.g., collection, enrichment) and where to store the logs, as well as the location and credentials for SortingHat and the ElasticSearch instances where the raw and enriched data is stored. Furthermore, it also includes backend sections to set up the parameters used by Perceval to access the software development tools (e.g., GitHub tokens, Gerrit username) and fetch their data.

Dashboards can be automatically uploaded via the `setup.cfg` if the phase `panels` is enabled. The `Data Status` and `Overview` dashboards will contain
widgets that summarize the information of the data sources declared in the `setup.cfg`. Note that the widgets are not updated when adding
new data sources, thus you need to manually delete the dashboards `Data Status` and `Overview` (under **Stack Management > Saved Objects** in Kibiter), and restart mordred again (making sure that the option `panels` is enabled).

### [es_collection]

 * **url** (str: http://172.17.0.1:9200): Elasticsearch URL (**Required**)
### [es_enrichment]

 * **autorefresh** (bool: True): Execute the autorefresh of identities
 * **autorefresh_interval** (int: 2): Time interval (days) to autorefresh identities
 * **url** (str: http://172.17.0.1:9200): Elasticsearch URL (**Required**)
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
 * **update_hour** (int: None): The hour of the day the tasks will run ignoring `min_update_delay` (collect, enrich ...)
### [panels]

 * **community** (bool: True): Include community section in dashboard
 * **kibiter_default_index** (str: git): Default index pattern for Kibiter
 * **kibiter_time_from** (str: now-90d): Default time interval for Kibiter
 * **kibiter_url** (str): Kibiter URL (**Required**)
 * **kibiter_version** (str: None): Kibiter version
 * **kafka** (bool: False): Include KIP section in dashboard
 * **github-comments** (bool: False): Enable GitHub comments menu. Note that if enabled, the github2:issue and github2:pull sections in the setup.cfg and projects.json should be declared
 * **github-events** (bool: False): Enable GitHub events menu. Note that if enabled, the github:event section in the setup.cfg and projects.json should be declared
 * **github-repos** (bool: False): Enable GitHub repo stats menu. Note that if enabled, the github:repo section in the setup.cfg and projects.json should be declared
 * **gitlab-issues** (bool: False): Enable GitLab issues menu. Note that if enabled, the gitlab:issue section in the setup.cfg and projects.json should be declared
 * **gitlab-merges** (bool: False): Enable GitLab merge requests menu. Note that if enabled, the gitlab:merge sections in the setup.cfg and projects.json should be declared
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
 * **host** (str: 127.0.0.1):  Host with the Sortinghat database (**Required**)
 * **port** (int: None):  GraphQL server port
 * **path** (str: None) GraphQL path
 * **ssl** (bool: False) GraphQL server use SSL/TSL connection
 * **matching** (list: ['email']): Algorithm for matching identities in Sortinghat (**Required**)
 * **password** (str: ): Password to access the Sortinghat database (**Required**)
 * **reset_on_load** (bool: False): Unmerge and remove affiliations for all identities on load
 * **sleep_for** (int: 3600): Delay between task identities executions (**Required**)
 * **strict_mapping** (bool: True): rigorous check of values in identities matching (i.e, well formed email addresses, non-overlapping enrollment periods)
 * **unaffiliated_group** (str: Unknown): Name of the organization for unaffiliated identities (**Required**)
 * **user** (str: root): User to access the Sortinghat database (**Required**)
### [backend-name:tag] (tag is optional)

* **collect** (bool: True): enable/disable collection phase
* **raw_index** (str: None): Index name in which to store the raw items (**Required**)
* **enriched_index** (str: None): Index name in which to store the enriched items (**Required**)
* **studies** (list: []): List of studies to be executed
* **anonymize** (bool: False): enable/disable anonymization of personal user information
* **backend-param-1**: ..
* **backend-param-2**: ..
* **backend-param-n**: ..

The template of a backend section is shown above.
Further information about Perceval backends parameters are available at:

* Params details: https://perceval.readthedocs.io/en/latest/perceval/perceval-backends.html
* Examples: https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

Note that some backend sections allow to specify specific enrichment options, which are listed below.

### [jenkins]
* **node_regex**: regular expression for extracting node name from `builtOn` field. This
  regular expression **must contain at least one group**. First group will be used to extract
  node name. More groups are allowed but not used to extract anything else.

### [studies-name:tag] (tag is optional)

* **study-param-1**: ..
* **study-param-2**: ..
* **study-param-n**: ..

A template of a study section is shown above. A complete list of studies parameters is available at:

* https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

## Projects.json [&uarr;](#contents)

The projects.json aims at describing the repositories grouped by a project that will be shown on the dashboards.

The project file enables the users to list the instances of the software development tools to analyse, such
as local and remote Git repositories, the URLs of GitHub and GitLab issue trackers, and the name of Slack channels.
Furthermore, it also allows the users to organize these instances into nested groups, which structure is reflected in
the visualization artifacts (i.e., documents and dashboards). Groups can be useful to represent projects within a single
company, sub-projects within a large project such as Linux and Eclipse, or the organizations within a collaborative project.

1. First level: project names
2. Second level: data sources and metadata
3. Third level: data source URLs

There are some filters, labels, and a special section:
* Filter `--filter-no-collection=true`: This filter is used to show old enriched data within the dashboards from
repositories that don't exist anymore in upstream.
* Filter `--filter-raw` and the section `unknown`: The data sources will only collected at the section `unknown`
but this allow to add the same source in different sections to enrich using the filter `--filter-raw`.
* Label ` --labels=[example]`: The data source will have the label of `example` which can be used to create visualisations for specific sets of data
* Section `unknown`: If the data source is only under this section it will be enriched as project `main`.

```
{
    "Chaoss": {
        "gerrit": [
            "gerrit.chaoss.org --filter-raw=data.projects:CHAOSS"
        ]
        "git": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https://<username>:<api-token>@github.com/chaoss/grimoirelab-sirmordred"
        ],
        "github": [
            "https:/github.com/chaoss/grimoirelab-perceval --filter-no-collection=true",
            "https:/github.com/chaoss/grimoirelab-sirmordred  --labels=[example]"
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

## Supported data sources [&uarr;](#contents)

These are the data sources GrimoireLab supports: [askbot](#askbot-), [bugzilla](#bugzilla-), [bugzillarest](#bugzillarest-), [cocom](#cocom-), [colic](#colic-), [confluence](#confluence-), [crates](#crates-), [discourse](#discourse-), [dockerhub](#dockerhub-), [dockerdeps](#dockerdeps-), [dockersmells](#dockersmells-), [functest](#functest-), [gerrit](#gerrit-), [git](#git-), [github](#github-), [github2](#github2-), [gitlab](#gitlab-), [gitter](#gitter-), [google_hits](#google_hits-), [groupsio](#groupsio-), [hyperkitty](#hyperkitty-), [jenkins](#jenkins-), [jira](#jira-), [kitsune](#kitsune-), [mattermost](#mattermost-), [mbox](#mbox-), [mediawiki](#mediawiki-), [meetup](#meetup-), [mozillaclub](#mozillaclub-), [nntp](#nntp-), [pagure](#pagure-), [phabricator](#phabricator-), [pipermail](#pipermail-), [puppetforge](#puppetforge-), [redmine](#redmine-), [remo](#remo-), [rocketchat](#rocketchat-), [rss](#rss-), [slack](#slack-), [stackexchange](#stackexchange-), [supybot](#supybot-), [telegram](#telegram-), [twitter](#twitter-)

#### askbot [&uarr;](#supported-data-sources-)
Questions and answers from Askbot site
- projects.json
```
{
    "Chaoss": {
        "askbot": [
            "https://askbot.org/"
        ]
    }
}
```
- setup.cfg
```
[askbot]
raw_index = askbot_raw
enriched_index = askbot_enriched
```
#### bugzilla [&uarr;](#supported-data-sources-)
Bugs from Bugzilla

- projects.json
```
{
    "Chaoss": {
        "bugzilla": [
            "https://bugs.eclipse.org/bugs/"
        ]
    }
}
```
- setup.cfg
```
[bugzilla]
raw_index = bugzilla_raw
enriched_index = bugzilla_enriched
backend-user = yyyy (optional)
backend-password = xxxx (optional)
no-archive = true (suggested)
```
#### bugzillarest [&uarr;](#supported-data-sources-)
Bugs from Bugzilla server (>=5.0) using its REST API

- projects.json
```
{
    "Chaoss": {
        "bugzillarest": [
            "https://bugzilla.mozilla.org"
        ]
    }
}
```

- setup.cfg
```
[bugzillarest]
raw_index = bugzillarest_raw
enriched_index = bugzillarest_enriched
backend-user = yyyy (optional)
backend-password = xxxx (optional)
no-archive = true (suggested)
```
#### cocom [&uarr;](#supported-data-sources-)
Code complexity integration.
Some graal dependencies like `cloc` might be required, https://github.com/chaoss/grimoirelab-graal#how-to-installcreate-the-executables

- projects.json
```
{
    "Chaoss":{
        "cocom": [
            "https://github.com/chaoss/grimoirelab-toolkit"
        ]
    }
}
```
- setup.cfg
```
[cocom]
raw_index = cocom_chaoss
enriched_index = cocom_chaoss_enrich
category = code_complexity_lizard_file
studies = [enrich_cocom_analysis]
branches = master
worktree-path = /tmp/cocom/
```
#### colic [&uarr;](#supported-data-sources-)
Code license backend.
- projects.json
```
{
    "Chaoss":{
        "colic": [
            "https://github.com/chaoss/grimoirelab-toolkit"
        ]
    }
}
```
- setup.cfg
```
[colic]
raw_index = colic_chaoss
enriched_index = colic_chaoss_enrich
category = code_license_nomos
studies = [enrich_colic_analysis]
exec-path = /usr/share/fossology/nomos/agent/nomossa
branches = master
worktree-path = /tmp/colic
```
#### confluence [&uarr;](#supported-data-sources-)
contents from Confluence

- projects.json
```
{
    "Chaoss": {
        "confluence": [
            "https://wiki.open-o.org/"
        ]
    }
}
```
- setup.cfg
```
[confluence]
raw_index = confluence_raw
enriched_index = confluence_enriched
no-archive = true (suggested)
```
#### crates [&uarr;](#supported-data-sources-)
packages from Crates.io

- projects.json
```
{
    "Chaoss": {
        "crates": [
            ""
        ]
    }
}
```
- setup.cfg
```
[crates]
raw_index = crates_raw
enriched_index = crates_enriched
```
#### discourse [&uarr;](#supported-data-sources-)
Topics from Discourse
- projects.json
```
{
    "Chaoss": {
        "discourse": [
            "https://foro.mozilla-hispano.org/"
        ]
    }
}
```
- setup.cfg
```
[discourse]
raw_index = discourse_raw
enriched_index = discourse_enriched
no-archive = true (suggested)
```
#### dockerhub [&uarr;](#supported-data-sources-)
Repositories info from DockerHub
- projects.json
```
{
    "Chaoss": {
        "dockerhub": [
            "bitergia kibiter"
        ]
    }
}
```
- setup.cfg
```
[dockerhub]
raw_index = dockerhub_raw
enriched_index = dockerhub_enriched
no-archive = true (suggested)
```
#### dockerdeps [&uarr;](#supported-data-sources-)
Dependencies extracted from Dockerfiles. Requires https://github.com/crossminer/crossJadolint
- projects.json
```
{
    "Chaoss": {
        "dockerdeps": [
            "https://github.com/chaoss/grimoirelab"
        ]
    }
}
```
- setup.cfg
```
[dockerdeps]
raw_index = dockerdeps_raw
enriched_index = dockerdeps_enrich
category = code_dependencies_jadolint
exec-path = <jadolint-local-path>/jadolint.jar
in-paths = [Dockerfile, Dockerfile-full, Dockerfile-secured, Dockerfile-factory, Dockerfile-installed]
```
#### dockersmells [&uarr;](#supported-data-sources-)
Smells extracted from Dockerfiles. Requires https://github.com/crossminer/crossJadolint
- projects.json
```
{
    "Chaoss": {
        "dockersmells": [
            "https://github.com/chaoss/grimoirelab"
        ]
    }
}
```
- setup.cfg
```
[dockersmells]
raw_index = dockersmells_raw
enriched_index = dockersmells_enrich
category = code_quality_jadolint
exec-path = <jadolint-local-path>/jadolint.jar
in-paths = [Dockerfile, Dockerfile-full, Dockerfile-secured, Dockerfile-factory, Dockerfile-installed]
```
#### functest [&uarr;](#supported-data-sources-)
Tests from functest
- projects.json
```
{
    "Chaoss": {
        "functest": [
            "http://testresults.opnfv.org/test/"
        ]
    }
}
```
- setup.cfg
```
[functest]
raw_index = functest_raw
enriched_index = functest_enriched
no-archive = true (suggested)
```
#### gerrit [&uarr;](#supported-data-sources-)
Reviews from Gerrit

You have to add your public key in the gerrit server.

- projects.json
```
{
    "Chaoss": {
        "gerrit": [
            "review.opendev.org"
        ]
    }
}
```
- setup.cfg
```
[gerrit]
raw_index = gerrit_raw
enriched_index = gerrit_enriched
user = xxxx
no-archive = true (suggested)
blacklist-ids = [] (optional)
max-reviews = 500 (optional)
studies = [enrich_demography:gerrit, enrich_onion:gerrit, enrich_demography_contribution:gerrit] (optional)

[enrich_demography:gerrit] (optional)

[enrich_onion:gerrit] (optional)
in_index = gerrit_enriched
out_index = gerrit-onion_enriched

[enrich_demography_contribution:gerrit] (optional)
date_field = grimoire_creation_date
author_field = author_uuid
```
#### git [&uarr;](#supported-data-sources-)
Commits from Git

**Note:** If you want to analyze private git repositories, make sure you pass the credentials directly in the URL.

- projects.json
```
{
    "Chaoss": {
        "git": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https://<username>:<api-token>@github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[git]
raw_index = git_raw
enriched_index = git_enriched
latest-items = true (suggested)
studies = [enrich_demography:git, enrich_git_branches:git, enrich_areas_of_code:git, enrich_onion:git, enrich_extra_data:git] (optional)

[enrich_demography:git] (optional)

[enrich_git_branches:git] (optional)
run_month_days = [1, 23] (optional)

[enrich_areas_of_code:git] (optional)
in_index = git_raw
out_index = git-aoc_enriched

[enrich_onion:git] (optional)
in_index = git_enriched
out_index = git-onion_enriched

[enrich_extra_data:git]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_forecast_activity]
out_index = git_study_forecast
```
#### github [&uarr;](#supported-data-sources-)
Issues and PRs from GitHub

##### issue
- projects.json
```
{
    "Chaoss": {
        "github:issue": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[github:issue]
raw_index = github_raw
enriched_index = github_enriched
api-token = xxxx
category = issue
sleep-for-rate = true
no-archive = true (suggested)
studies = [enrich_onion:github,
           enrich_geolocation:user,
           enrich_geolocation:assignee,
           enrich_extra_data:github,
           enrich_backlog_analysis,
           enrich_demography:github] (optional)

[enrich_onion:github] (optional)
in_index_iss = github_issues_onion-src
in_index_prs = github_prs_onion-src
out_index_iss = github-issues-onion_enriched
out_index_prs = github-prs-onion_enriched

[enrich_geolocation:user] (optional)
location_field = user_location
geolocation_field = user_geolocation

[enrich_geolocation:assignee] (optional)
location_field = assignee_location
geolocation_field = assignee_geolocation

[enrich_extra_data:github]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_backlog_analysis]
out_index = github_enrich_backlog
interval_days = 7
reduced_labels = [bug,enhancement]
map_label = [others, bugs, enhancements]

[enrich_demography:github]
```
##### pull request
- projects.json
```
{
    "Chaoss": {
        "github:pull": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[github:pull]
raw_index = github-pull_raw
enriched_index = github-pull_enriched
api-token = xxxx
category = pull_request
sleep-for-rate = true
no-archive = true (suggested)
studies = [enrich_geolocation:user,
           enrich_geolocation:assignee,
           enrich_extra_data:github,
           enrich_demography:github] (optional)

[enrich_geolocation:user]
location_field = user_location
geolocation_field = user_geolocation

[enrich_geolocation:assignee]
location_field = assignee_location
geolocation_field = assignee_geolocation

[enrich_extra_data:github]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_demography:github]
```
##### repo
The number of forks, stars, and subscribers in the repository.

- projects.json
```
{
    "Chaoss": {
        "github:repo": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[github:repo]
raw_index = github-repo_raw
enriched_index = github-repo_enriched
api-token = xxxx
category = repository
sleep-for-rate = true
no-archive = true (suggested)
studies = [enrich_extra_data:github, enrich_demography:github]

[enrich_extra_data:github]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_demography:github]
```
#### githubql [&uarr;](#supported-data-sources-)
Events from GitHub

The corresponding dashboards can be automatically uploaded by setting `github-events`
to `true` in the `panels` section within the `setup.cfg`

- projects.json
```
{
    "Chaoss": {
        "githubql": [
            "https://github.com/chaoss/grimoirelab-toolkit"
        ]
    }
}
```
- setup.cfg
```
[panels]
github-events = true

[githubql]
raw_index = github_event_raw
enriched_index = github_event_enriched
api-token = xxxxx
sleep-for-rate = true
sleep-time = "300" (optional)
no-archive = true (suggested)
studies = [enrich_duration_analysis:kanban, enrich_reference_analysis] (optional)

[enrich_duration_analysis:kanban]
start_event_type = MovedColumnsInProjectEvent
fltr_attr = board_name
target_attr = board_column
fltr_event_types = [MovedColumnsInProjectEvent, AddedToProjectEvent]

[enrich_duration_analysis:label]
start_event_type = UnlabeledEvent
target_attr = label
fltr_attr = label
fltr_event_types = [LabeledEvent]

[enrich_reference_analysis] (optional)
```

#### github2 [&uarr;](#supported-data-sources-)
Comments from GitHub

The corresponding dashboards can be automatically uploaded by setting `github-comments`
to `true` in the `panels` section within the `setup.cfg`

##### issue
- projects.json
```
{
    "Chaoss": {
        "github2:issue": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[github2:issue]
api-token = xxxx
raw_index = github2-issues_raw
enriched_index = github2-issues_enriched
sleep-for-rate = true
category = issue
no-archive = true (suggested)
studies = [enrich_geolocation:user, enrich_geolocation:assignee, enrich_extra_data:github2, enrich_feelings] (optional)

[enrich_geolocation:user] (optional)
location_field = user_location
geolocation_field = user_geolocation

[enrich_geolocation:assignee] (optional)
location_field = assignee_location
geolocation_field = assignee_geolocation

[enrich_extra_data:github2]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_feelings]
attributes = [title, body]
nlp_rest_url = http://localhost:2901
```
##### pull request
- projects.json
```
{
    "Chaoss": {
        "github2:pull": [
            "https:/github.com/chaoss/grimoirelab-perceval",
            "https:/github.com/chaoss/grimoirelab-sirmordred"
        ]
    }
}
```
- setup.cfg
```
[github2:pull]
api-token = xxxx
raw_index = github2-pull_raw
enriched_index = github2-pull_enriched
sleep-for-rate = true
category = pull_request
no-archive = true (suggested)
studies = [enrich_geolocation:user, enrich_geolocation:assignee, enrich_extra_data:git, enrich_feelings] (optional)

[enrich_geolocation:user] (optional)
location_field = user_location
geolocation_field = user_geolocation

[enrich_geolocation:assignee] (optional)
location_field = assignee_location
geolocation_field = assignee_geolocation

[enrich_extra_data:github2]
json_url = https://gist.githubusercontent.com/zhquan/bb48654bed8a835ab2ba9a149230b11a/raw/5eef38de508e0a99fa9772db8aef114042e82e47/bitergia-example.txt

[enrich_feelings]
attributes = [title, body]
nlp_rest_url = http://localhost:2901
```

#### gitlab [&uarr;](#supported-data-sources-)
Issues and MRs from GitLab

GitLab issues and merge requests need to be configured in two different sections.
The corresponding dashboards can be automatically uploaded by setting `gitlab-issue` and `gitlab-merge`
to `true` in the `panels` section within the `setup.cfg`

If a given GitLab repository is under more than 1 level, all the slashes `/` starting from the second level have to be
replaced by `%2F`. For instance, for a repository with a structure similar to this one
`https://gitlab.com/Molly/lab/first`.
##### issue
- projects.json
```
{
    "Chaoss": {
        "gitlab:issue": [
            "https://gitlab.com/Molly/first",
            "https://gitlab.com/Molly/lab%2Fsecond"
        ]
    }
}
```
- setup.cfg
```
[panels]
gitlab-issues = true

[gitlab:issue]
category = issue
raw_index = gitlab-issues_raw
enriched_index = gitlab-issues_enriched
api-token = xxxx
sleep-for-rate = true
no-archive = true (suggested)
studies = [enrich_onion:gitlab-issue] (optional)

[enrich_onion:gitlab-issue] (optional)
in_index = gitlab-issues_enriched
out_index = gitlab-issues-onion_enriched
data_source = gitlab-issues
```
##### merge request
- projects.json
```
{
    "Chaoss": {
        "gitlab:merge": [
            "https://gitlab.com/Molly/first",
            "https://gitlab.com/Molly/lab%2Fsecond"
        ],
    }
}
```
- setup.cfg
```
[panels]
gitlab-merges = true

[gitlab:merge]
category = merge_request
raw_index = gitlab-mrs_raw
enriched_index = gitlab-mrs_enriched
api-token = xxxx
sleep-for-rate = true
no-archive = true (suggested)
studies = [enrich_onion:gitlab-merge] (optional)

[enrich_onion:gitlab-merge] (optional)
in_index = gitlab-mrs_enriched
out_index = gitlab-mrs-onion_enriched
data_source = gitlab-merges

```
#### gitter [&uarr;](#supported-data-sources-)
Messages from gitter rooms

You have to join the rooms you want to mine.

- projects.json
```
{
    "Chaoss": {
        "gitter": [
            "https://gitter.im/jenkinsci/jenkins",
        ]
    }
}
```
- setup.cfg
```
[gitter]
raw_index = gitter_raw
enriched_index = gitter_enriched_raw
api-token = xxxxx
sleep-for-rate = true
sleep-time = "300" (optional)
no-archive = true (suggested)
```

#### google_hits [&uarr;](#supported-data-sources-)
Number of hits for a set of keywords from Google
- projects.json
```
{
    "Chaoss": {
        "google_hits": [
            "bitergia grimoirelab"
        ]
    }
}
```
- setup.cfg
```
[google_hits]
raw_index = google_hits_raw
enriched_index =google_hits_enriched
```
#### groupsio [&uarr;](#supported-data-sources-)
Messages from Groupsio

To know the lists you are subscribed to: https://gist.github.com/valeriocos/ad33a0b9b2d13a8336230c8c59df3c55

- projects.json
```
{
    "Chaoss": {
        "groupsio": [
            "group1",
            "group2"
        ]
    }
}
```
- setup.cfg
```
[groupsio]
raw_index = groupsio_raw
enriched_index = groupsio_enriched
email = yyyy
password = xxxx
```
#### hyperkitty [&uarr;](#supported-data-sources-)
Messages from a HyperKitty
- projects.json
```
{
    "Chaoss": {
        "hyperkitty": [
            "https://lists.mailman3.org/archives/list/mailman-users@mailman3.org"
        ]
    }
}
```
- setup.cfg
```
[hyperkitty]
raw_index = hyperkitty_raw
enriched_index = hyperkitty_enriched
```
#### jenkins [&uarr;](#supported-data-sources-)
Builds from a Jenkins

- projects.json
```
{
    "Chaoss": {
        "jenkins": [
            "https://build.opnfv.org/ci"
        ]
    }
}
```
- setup.cfg
```
[jenkins]
raw_index = jenkins_raw
enriched_index = jenkins_enriched
no-archive = true (suggested)
```
#### jira [&uarr;](#supported-data-sources-)
Issues data from JIRA issue trackers

- projects.json
```
{
    "Chaoss":{
        "jira": [
            "https://jira.opnfv.org"
        ]
    }
}
```
- setup.cfg
```
[jira]
raw_index = jira_raw
enriched_index = jira_enriched
no-archive = true (suggested)
backend-user = yyyy (optional)
backend-password = xxxx (optional)
```
#### kitsune [&uarr;](#supported-data-sources-)
Questions and answers from KitSune

- projects.json
```
{
    "Chaoss": {
        "kitsune": [
            ""
        ]
    }
}
```
- setup.cfg
```
[kitsune]
raw_index = kitsune_raw
enriched_index = kitsune_enriched
```

#### mattermost [&uarr;](#supported-data-sources-)
Messages from Mattermost channels
- projects.json
```
{
    "Chaoss": {
        "mattermost": [
            "https://chat.openshift.io 8j366ft5affy3p36987pcugaoa"
        ]
    }
}
```
- setup.cfg
```
[mattermost]
raw_index = mattermost_raw
enriched_index = mattermost_enriched
api-token = xxxx
studies = [enrich_demography:mattermost] (optional)

[enrich_demography:mattermost] (optional)
```
#### mbox [&uarr;](#supported-data-sources-)
Messages from MBox files

For mbox files, it is needed the name of the mailing list and the path where the mboxes can be found. In the example
below, the name of the mailing list is set to "mirageos-devel".
- projects.json
```
{
    "Chaoss": {
        "mbox": [
            "mirageos-devel /home/bitergia/mbox/mirageos-devel/"
        ]
    }
}
```
- setup.cfg
```
[mbox]
raw_index = mbox_raw
enriched_index = mbox_enriched
```
#### mediawiki [&uarr;](#supported-data-sources-)
Pages and revisions from MediaWiki

-projects.json
```
{
    "Chaoss": {
        "mediawiki": [
            "https://www.mediawiki.org/w https://www.mediawiki.org/wiki"
        ]
    }
}
```
- setup.cfg
```
[mediawiki]
raw_index = mediawiki_raw
enriched_index = mediawiki_enriched
no-archive = true (suggested)
```
#### meetup [&uarr;](#supported-data-sources-)
Events from Meetup groups

For meetup groups it is only needed the identifier of the meetup group
and an API token: https://chaoss.github.io/grimoirelab-tutorial/gelk/meetup.html#gathering-meetup-groups-data
- projects.json
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
- setup.cfg
```
[meetup]
raw_index = meetup_raw
enriched_index = meetup_enriched
api-token = xxxx
sleep-for-rate = true
sleep-time = "300" (optional)
no-archive = true (suggested)

```
#### mozillaclub [&uarr;](#supported-data-sources-)
Events from Mozillaclub
- projects.json
```
{
    "Chaoss": {
        "mozillaclub": [
            "https://spreadsheets.google.com/feeds/cells/1QHl2bjBhMslyFzR5XXPzMLdzzx7oeSKTbgR5PM8qp64/ohaibtm/public/values?alt=json"
        ]
    }
}
```
- setup.cfg
```
[mozillaclub]
raw_index = mozillaclub_raw
enriched_index = mozillaclub_enriched
```
#### nntp [&uarr;](#supported-data-sources-)
Articles from NNTP newsgroups

The way to setup netnews is adding the server and the news channel to be monitored. In the example below,
the `news.myproject.org` is the server name.
- projects.json
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
- setup.cfg
```
[nntp]
raw_index = nntp_raw
enriched_index =  nntp_enriched
```
#### pagure [&uarr;](#supported-data-sources-)
Issues from Pagure repositories

- projects.json
```
{
    "Chaoss": {
        "pagure": [
            "https://pagure.io/Test-group/Project-example-namespace"
        ]
    }
}
```
- setup.cfg
```
[pagure]
raw_index = pagure_raw
enriched_index = pagure_enriched
api-token = xxxx
sleep-for-rate = true
sleep-time = "300" (optional)
no-archive = true (suggested)
```
#### phabricator [&uarr;](#supported-data-sources-)
Tasks from Phabricator

- projects.json
```
{
    "Chaoss": {
        "phabricator": [
            "https://phabricator.wikimedia.org"
        ]
    }
}
```
- setup.cfg
```
[phabricator]
raw_index = phabricator_raw
enriched_index = phabricator_enriched
api-token = xxxx
no-archive = true (suggested)
```
#### pipermail [&uarr;](#supported-data-sources-)
Messages from Pipermail

- projects.json
```
{
    "Chaoss": {
        "pipermail": [
            "https://lists.linuxfoundation.org/pipermail/grimoirelab-discussions/"
        ]
    }
}
```
- setup.cfg
```
[pipermail]
raw_index = pipermail_raw
enriched_index = pipermail_enriched
```
#### puppetforge [&uarr;](#supported-data-sources-)
Modules and their releases from Puppet's forge

- projects.json
```
{
    "Chaoss": {
        "puppetforge": [
            ""
        ]
    }
}
```
- setup.cfg
```
[puppetforge]
raw_index = puppetforge_raw
enriched_index = puppetforge_enriched
```
#### redmine [&uarr;](#supported-data-sources-)
Issues from Redmine
- project.json
```
{
    "Chaoss": {
        "redmine": [
            "http://tracker.ceph.com/"
        ]
    }
}
```
- setup.cfg
```
[redmine]
raw_index = redmine_raw
enriched_index = redmine_enriched
api-token = XXXXX
```
#### remo [&uarr;](#supported-data-sources-)
Events, people and activities from ReMo
- project.json
```
{
    "Chaoss": {
        "remo": [
            "https://reps.mozilla.org"
        ]
    }
}
```
- setup.cfg
```
[remo]
raw_index = remo_raw
enriched_index = remo_enriched
```
#### rocketchat [&uarr;](#supported-data-sources-)
Messages from Rocketchat channels
- projects.json
```
{
    "Chaoss": {
        "rocketchat": [
            "https://open.rocket.chat general"
        ]
    }
}
```
- setup.cfg
```
[rocketchat]
raw_index = rocketchat_raw
enriched_index = rocketchat_enriched
api-token = xxxx
sleep-for-rate = true
user-id = xxxx
no-archive = true (suggested)
```
#### rss [&uarr;](#supported-data-sources-)
Entries from RSS feeds

- project.json
```
{
    "Chaoss": {
        "remo": [
            "https://reps.mozilla.org"
        ]
    }
}
```
- setup.cfg
```
[rss]
raw_index = rss_raw
enriched_index = rss_enriched
```
#### slack [&uarr;](#supported-data-sources-)
Messages from Slack channels

The information needed to monitor slack channels is the channel id.
- projects.json
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
- setup.cfg
```
[slack]
raw_index = slack_raw
enriched_index = slack_enriched
api-token = xxxx
no-archive = true (suggested)
```
#### stackexchange [&uarr;](#supported-data-sources-)
Questions, answers and comments from StackExchange

- projects.json
```
{
    "Chaoss": {
        "stackexchange": [
            "http://stackoverflow.com/questions/tagged/chef",
            "http://stackoverflow.com/questions/tagged/chefcookbook",
            "http://stackoverflow.com/questions/tagged/ohai",
            "http://stackoverflow.com/questions/tagged/test-kitchen",
            "http://stackoverflow.com/questions/tagged/knife"
        ]
    }
}
```
- setup.cfg
```
[stackexchange]
raw_index = stackexchange_raw
enriched_index = stackexchange_enriched
api-token = xxxx
no-archive = true (suggested)
```
#### supybot [&uarr;](#supported-data-sources-)
Messages from Supybot log files

For supybot files, it is needed the name of the IRC channel and the path where the logs can be found. In the example
below, the name of the channel is set to "irc://irc.freenode.net/atomic".
- projects.json
```
{
    "Chaoss": {
        "supybot": [
            "irc://irc.freenode.net/atomic /home/bitergia/irc/percevalbot/logs/ChannelLogger/freenode/#atomic"
        ]
    }
}
```
- setup.cfg
```
[supybot]
raw_index = supybot_raw
enriched_index = supybot_enriched
```

#### telegram [&uarr;](#supported-data-sources-)
Messages from Telegram

You need to have an API token: https://github.com/chaoss/grimoirelab-perceval#telegram

- projects.json
```
{
    "Chaoss": {
        "telegram": [
            "Mozilla_analytics"
        ]
    }
}
```
- setup.cfg
```
[telegram]
raw_index = telegram_raw
enriched_index = telegram_enriched
api-token = XXXXX
```
#### twitter [&uarr;](#supported-data-sources-)
Messages from Twitter

You need to provide a [search query](https://developer.twitter.com/en/docs/tweets/search/guides/build-standard-query) and an API token (which requires to create an [app](https://developer.twitter.com/en/docs/basics/apps/overview)). The script at https://gist.github.com/valeriocos/7d4d28f72f53fbce49f1512ba77ef5f6 helps obtaining a token.

- projects.json
```
{
    "Chaoss": {
        "twitter": [
            "bitergia"
        ]
    }
}
```
- setup.cfg
```
[twitter]
raw_index = twitter_raw
enriched_index = twitter_enriched
api-token = XXXX
```

#### weblate [&uarr;](#supported-data-sources-)
Changes from Weblate

You need to have an API token: The token can be obtained after registering to a weblate
instance (e.g., https://translations.documentfoundation.org/), via the page <instance>/accounts/profile/#api

- projects.json
```
{
    "Chaoss": {
        "weblate": [
            "https://translations.documentfoundation.org"
        ]
    }
}
```
- setup.cfg
```
[weblate]
raw_index = weblate_raw
enriched_index = weblate_enriched
api-token = XXXX
no-archive = true (suggested)
sleep-for-rate = true (suggested)
studies = [enrich_demography:weblate] (optional)

[enrich_demography:weblate] (optional)
```

## Micro Mordred [&uarr;](#contents)

Micro Mordred is a simplified version of Mordred which omits the use of its scheduler. Thus, Micro Mordred allows running single Mordred tasks (e.g., raw collection, enrichment) per execution.

Micro Mordred is located in the [sirmordred/utils](https://github.com/chaoss/grimoirelab-sirmordred/tree/master/sirmordred/utils/micro.py) folder of this same repository. It can be executed via command line, its parameters are summarized below:
```
--debug: execute Micro Mordred in debug mode

--raw: activate raw task

--enrich: activate enrich task

--identities: activate merge identities task

--panels: activate panels task

--cfg: path of the configuration file

--backends: list of cfg sections where the active tasks will be executed

--logs-dir: single parameter denoting the path of folder in which logs are to be stored
```

Examples of possible executions are shown below:
```
cd .../grimoirelab-sirmordred/sirmordred/utils/
micro.py --raw --enrich --cfg ./setup.cfg --backends git # execute the Raw and Enrich tasks for the Git cfg section
micro.py --panels # execute the Panels task to load the Sigils panels to Kibiter
micro.py --raw --enrich --debug --cfg ./setup.cfg --backends groupsio --logs-dir logs # execute the raw and enriched tasks for the groupsio cfg section with debug mode on and logs being saved in the folder logs in the same directory as micro.py
```
