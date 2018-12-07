# SirMordred 0.1.38 [![Build Status](https://travis-ci.org/chaoss/grimoirelab-sirmordred.svg?branch=master)](https://travis-ci.org/chaoss/grimoirelab-sirmordred)[![Coverage Status](https://coveralls.io/repos/github/chaoss/grimoirelab-sirmordred/badge.svg?branch=master)](https://coveralls.io/github/chaoss/grimoirelab-sirmordred?branch=master)

SirMordred is the tool used to coordinate the execution of the GrimoireLab platform, via a configuration file. Below you can find details about the different sections composing the configuration file.

## General Sections

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
 * **log_backup_count** (int: 5): Number of rotate logs files to preserve
 * **log_handler** (str: file): use rotate for rotating the logs automatically
 * **log_max_bytes** (int: 104857600): Max number of bytes per log file
 * **logs_dir** (str: logs): Directory with the logs of sirmordred (**Required**)
 * **min_update_delay** (int: 60): Short delay between tasks (collect, enrich ...)
 * **scroll_size** (int: 100): Number of items to read from Elasticsearch when scrolling
 * **short_name** (str: Short name): Short name of the project (**Required**)
 * **update** (bool: False): Execute the tasks in loop (**Required**)
 * **aliases_file** (str: ./aliases.json): JSON file to define aliases for raw and enriched indexes
 * **menu_file** (str: ./menu.yaml): YAML file to define the menus to be shown in Kibiter
### [panels] 

 * **community** (bool: True): Include community section in dashboard
 * **kibiter_default_index** (str: git): Default index pattern for Kibiter
 * **kibiter_time_from** (str: now-90d): Default time interval for Kibiter
 * **kibiter_url** (str): Kibiter URL (**Required**)
 * **kibiter_version** (str: None): Kibiter version
 * **kafka** (bool: False): Include KIP section in dashboard
 * **gitlab-issues** (bool: False): Enable GitLab issues menu
 * **gitlab-merges** (bool: False): Enable GitLab merge requests menu
 * **mattermost** (bool: False): Enable Mattermost menu
 * **strict** (bool: True): Enable strict panels loading
 
### [phases] 

 * **collection** (bool: True): Activate collection of items (**Required**)
 * **enrichment** (bool: True): Activate enrichment of items (**Required**)
 * **identities** (bool: True): Do the identities tasks (**Required**)
 * **panels** (bool: True): Load panels, create alias and other tasks related (**Required**)
 * **report** (bool: False): Generate the PDF report for a project (alpha)
 * **track_items** (bool: False): Track specific items from a gerrit repository
### [projects] 

 * **load_eclipse** (bool: False): Load the projects from Eclipse
 * **projects_file** (str: projects.json): Projects file path with repositories to be collected group by projects
 * **projects_url** (str: None): Projects file URL
### [report] 

 * **config_file** (str: report.cfg): Config file for the report (**Required**)
 * **data_dir** (str: report_data): Directory in which to store the report data (**Required**)
 * **end_date** (str: 2100-01-01): End date for the report (**Required**)
 * **filters** (list: []): General filters to be applied to all queries
 * **interval** (str: quarter): Interval for the report (**Required**)
 * **offset** (str: None): Date offset to be applied to start and end
 * **start_date** (str: 1970-01-01): Start date for the report (**Required**)
### [sortinghat] 

 * **affiliate** (bool: True): Affiliate identities to organizations (**Required**)
 * **autogender** (bool: False): Add gender to the profiles (executes autogender)
 * **autoprofile** (list: ['customer', 'git', 'github']): Order in which to get the identities information for filling the profile (**Required**)
 * **bots_names** (list: []): Name of the identities to be marked as bots
 * **database** (str: sortinghat_db): Name of the Sortinghat database (**Required**)
 * **host** (str: mariadb): Host with the Sortinghat database (**Required**)
 * **identities_api_token** (str: None): API token for remote operation with GitHub and Gitlab
 * **identities_export_url** (str: None): URL in which to export the identities in Sortinghat
 * **identities_file** (list: []): File path with the identities to be loaded in Sortinghat
 * **identities_format** (str: sortinghat): Format of the identities data to be loaded
 * **load_orgs** (bool: False): 
 * **matching** (list: ['email']): Algorithm for matching identities in Sortinghat (**Required**)
 * **no_bots_names** (list: []): Name of the identities to be unmarked as bots
 * **orgs_file** (str: None): File path with the organizations to be loaded in Sortinghat
 * **password** (str: ): Password to access the Sortinghat database (**Required**)
 * **reset_on_load** (bool: False): Unmerge and remove affiliations for all identities on load
 * **sleep_for** (int: 3600): Delay between task identities executions (**Required**)
 * **strict_mapping** (bool: True): rigorous check of values in identities matching (i.e, well formed email addresses)
 * **unaffiliated_group** (str: Unknown): Name of the organization for unaffiliated identities (**Required**)
 * **user** (str: root): User to access the Sortinghat database (**Required**)
### [track_items] 

 * **project** (str: TrackProject): Gerrit project to track (**Required**)
 * **raw_index_gerrit** (str: ): Name of the gerrit raw index (**Required**)
 * **raw_index_git** (str: ): Name of the git raw index (**Required**)
 * **upstream_raw_es_url** (str: ): URL with the file with the gerrit reviews to track (**Required**)
## Backend Sections

In this section, a template of a backend section is shown.
Further information about Perceval backends parameters are available at:

* Params details: http://perceval.readthedocs.io/en/latest/perceval.backends.core.html
* Examples: https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

### [backend-name:tag] # :tag is optional
* **collect** (bool: True): enable/disable collection phase
* **raw_index** (str: None): Index name in which to store the raw items (**Required**)
* **enriched_index** (str: None): Index name in which to store the enriched items (**Required**)
* **studies** (list: []): List of studies to be executed
* **backend-param-1**: ..
* **backend-param-2**: ..
* **backend-param-n**: ..

#### Enrichment params
Some backend sections allow to specify specific enrichment options, listed below.

##### [jenkins]
* **node_regex**: regular expression for extracting node name from `builtOn` field. This
  regular expression **must contain at least one group**. First group will be used to extract
  node name. More groups are allowed but not used to extract anything else.

## Studies Sections

In this section, a template of a study section is shown.
A complete list of studies parameters is available at:

* https://github.com/chaoss/grimoirelab-sirmordred/blob/master/tests/test_studies.cfg

### [studies-name:tag] # :tag is optional
* **study-param-1**: ..
* **study-param-2**: ..
* **study-param-n**: ..
