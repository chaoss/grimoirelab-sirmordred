# Mordred configuration params

This is an automatic generated doc. Don't modify it by hand.
Use python mordred/config.py to generate it.

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

 * **bulk_size** (int: 1000): Number of items to include in Elasticsearch bulk operations
 * **debug** (bool: True): Debug mode (logging mainly) (**Required**)
 * **log_backup_count** (int: 5): Number of rotate logs files to preserve
 * **log_handler** (str: file): use rotate for rotating the logs automatically
 * **log_max_bytes** (int: 104857600): Max number of bytes per log file
 * **logs_dir** (str: logs): Directory with the logs of mordred (**Required**)
 * **min_update_delay** (int: 60): Short delay between tasks (collect, enrich ...)
 * **scroll_size** (int: 100): Number of items to receive in Elasticsearch when scrolling
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
 * **github-repos** (bool: False): Enable GitHub repo stats menu
 * **gitlab-issues** (bool: False): Enable GitLab issues menu
 * **gitlab-merges** (bool: False): Enable GitLab merge requests menu
 * **mattermost** (bool: False): Enable Mattermost menu
 * **strict** (bool: True): Enable strict panels loading
 * **contact** (str: None): Support repository URL
### [phases] 

 * **collection** (bool: True): Activate collection of items (**Required**)
 * **enrichment** (bool: True): Activate enrichment of items (**Required**)
 * **identities** (bool: True): Do the identities tasks (**Required**)
 * **panels** (bool: True): Load panels, create alias and other tasks related (**Required**)
### [projects] 

 * **load_eclipse** (bool: False): Load the projects from Eclipse
 * **projects_file** (str: projects.json): Projects file path with repositories to be collected grouped by projects
 * **projects_url** (str: None): Projects file URL, the projects_file is required to store the file locally
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
## Sample Backend Section

In this section the perceval backends param should be also added
### [apache]

 * **enriched_index** (str: None): Index name in which to store the enriched items (**Required**)
 * **raw_index** (str: None): Index name in which to store the raw items (**Required**)
 * **studies** (list: None): List of studies to be executed
