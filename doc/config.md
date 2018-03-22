# Mordred 0.1.19 configuration params

This is an automatic generated doc. Don't modify it by hand.
Use python mordred/config.py to generate it.

## General Sections

### [es_collection] 

 * **arthur** (bool: False): Use arthur for collecting items from perceval
 * **arthur_url** (str: None): URL for the arthur service
 * **password** (str: None): Password for connection to Elasticsearch
 * **redis_url** (str: None): URL for the redis service
 * **url** (str: http://172.17.0.1:9200) (Required): Elasticsearch URL
 * **user** (str: None): User for connection to Elasticsearch
### [es_enrichment] 

 * **autorefresh** (bool: True): Execute the autorefresh of identities
 * **password** (str: None): Password for connection to Elasticsearch
 * **url** (str: http://172.17.0.1:9200) (Required): Elasticsearch URL
 * **user** (str: None): User for connection to Elasticsearch
### [general] 

 * **bulk_size** (int: 1000): Number of items to include in Elasticsearch bulk operations
 * **debug** (bool: True) (Required): Debug mode (logging mainly)
 * **log_backup_count** (int: 5): Number of rotate logs files to preserve
 * **log_handler** (str: file): use rotate for rotating the logs automatically
 * **log_max_bytes** (int: 104857600): Max number of bytes per log file
 * **logs_dir** (str: logs) (Required): Directory with the logs of mordred
 * **min_update_delay** (int: 60): Short delay between tasks (collect, enrich ...)
 * **scroll_size** (int: 100): Number of items to receive in Elasticsearch when scrolling
 * **short_name** (str: Short name) (Required): Short name of the project
 * **update** (bool: False) (Required): Execute the tasks in loop
### [panels] 

 * **kibiter_default_index** (str: git): Default index pattern for Kibiter
 * **kibiter_time_from** (str: now-90d): Default time interval for Kibiter
 * **kibiter_url** (str: None): Kibiter URL
 * **kibiter_version** (str: None): Kibiter version
### [phases] 

 * **collection** (bool: True) (Required): Activate collection of items
 * **enrichment** (bool: True) (Required): Activate enrichment of items
 * **identities** (bool: True) (Required): Do the identities tasks
 * **panels** (bool: True) (Required): Load panels, create alias and other tasks related
 * **report** (bool: False): Generate the PDF report for a project (alpha)
 * **track_items** (bool: False): Track specific items from a gerrit repository
### [projects] 

 * **load_eclipse** (bool: False): Load the projects from Eclipse
 * **projects_file** (str: projects.json): Projects file path with repositories to be collected group by projects
 * **projects_url** (str: None): Projects file URL
### [report] 

 * **config_file** (str: report.cfg) (Required): Config file for the report
 * **data_dir** (str: report_data) (Required): Directory in which to store the report data
 * **end_date** (str: 2100-01-01) (Required): End date for the report
 * **filters** (list: []): General filters to be applied to all queries
 * **interval** (str: quarter) (Required): Interval for the report
 * **offset** (str: None): Date offset to be applied to start and end
 * **start_date** (str: 1970-01-01) (Required): Start date for the report
### [sortinghat] 

 * **affiliate** (bool: True) (Required): Affiliate identities to organizations
 * **autogender** (bool: False): Add gender to the profiles (executes autogender)
 * **autoprofile** (list: ['customer', 'git', 'github']) (Required): Order in which to get the identities information for filling the profile
 * **bots_names** (list: []): Name of the identities to be marked as bots
 * **database** (str: sortinghat_db) (Required): Name of the Sortinghat database
 * **host** (str: mariadb) (Required): Host with the Sortinghat database
 * **identities_api_token** (str: None): API token for remote operation with GitHub and Gitlab
 * **identities_export_url** (str: None): URL in which to export the identities in Sortinghat
 * **identities_file** (list: []): File path with the identities to be loaded in Sortinghat
 * **identities_format** (str: sortinghat): Format of the identities data to be loaded
 * **load_orgs** (bool: False): 
 * **matching** (list: ['email']) (Required): Algorithm for matching identities in Sortinghat
 * **no_bots_names** (list: []): Name of the identities to be unmarked as bots
 * **orgs_file** (str: None): File path with the organizations to be loaded in Sortinghat
 * **password** (str: ) (Required): Password to access the Sortinghat database
 * **reset_on_load** (bool: False): Unmerge and remove affiliations for all identities on load
 * **sleep_for** (int: 3600) (Required): Delay between task identities executions
 * **strict_mapping** (bool: True): rigorous check of values in identities matching (i.e, well formed email addresses)
 * **unaffiliated_group** (str: Unknown) (Required): Name of the organization for unaffiliated identities
 * **user** (str: root) (Required): User to access the Sortinghat database
### [track_items] 

 * **project** (str: TrackProject) (Required): Gerrit project to track
 * **raw_index_gerrit** (str: ) (Required): Name of the gerrit raw index
 * **raw_index_git** (str: ) (Required): Name of the git raw index
 * **upstream_raw_es_url** (str: ) (Required): URL with the file with the gerrit reviews to track
## Sample Backend Section

In this section the perceval backends param should be also added
### [apache]

 * **enriched_index** (str: None) (Required): Index name in which to store the enriched items
 * **raw_index** (str: None) (Required): Index name in which to store the raw items
 * **studies** (list: None): List of studies to be executed
