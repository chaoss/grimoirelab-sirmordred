## Getting started [&uarr;](/README.md#contents)

SirModred relies on ElasticSearch, Kibiter and MySQL/MariaDB. The current versions used are:
- ElasticSearch 6.8.6
- Kibiter 6.8.6
- MySQL/MariaDB (5.7.24/10.0)

There are mainly 2 options to get started with SirMordred:
- [Source code and docker](#source-code-and-docker-):
In this method, the applications (ElasticSearch, Kibiter and MariaDB) are installed using docker and the GrimoireLab Components are installed using the source code.
- [Only docker](#only-docker-):
In this method, the applications (ElasticSearch, Kibiter and MariaDB) and the GrimoireLab Components are installed using docker.

## Source code and docker [&uarr;](#getting-started-)

### Getting the containers [&uarr;](#source-code-and-docker-)

You will have to install ElasticSearch (6.8.6), Kibiter (6.8.6) and a MySQL/MariaDB database (5.7.24/10.0). You can use the following docker-compose to have them running.

> Help: You need to install docker and docker-compose for this. Please refer the documentation.
> - https://docs.docker.com/install/linux/docker-ce/ubuntu/
> - https://docs.docker.com/compose/install/

> Note: 
> 1. You can omit (comment/remove) the `mariadb` section in case you have MariaDB or MySQL already installed in your system.
> 2. It is not mandatory to use docker to install ElasticSearch, Kibiter and MySQL/MariaDB database. They can be installed by other means too (source code). We are not much concerned about the method they are installed. Docker is the easiest way as it mostly avoids the errors caused by them.

#### docker-compose (with SearchGuard) [&uarr;](#getting-the-containers-)

Note: For accessing Kibiter and/or creating indexes login is required, the `username:password` is `admin:admin`.
```
services:
    mariadb:
      image: mariadb:10.0
      expose:
        - "3306"
      environment:
        - MYSQL_ROOT_PASSWORD=
        - MYSQL_ALLOW_EMPTY_PASSWORD=yes

    elasticsearch:
      image: bitergia/elasticsearch:6.8.6-secured
      command: elasticsearch -Enetwork.bind_host=0.0.0.0 -Ehttp.max_content_length=2000mb
      ports:
        - 9200:9200
      environment:
        - ES_JAVA_OPTS=-Xms2g -Xmx2g

    kibiter:
      restart: on-failure:5
      image: bitergia/kibiter:secured-v6.8.6-3
      environment:
        - PROJECT_NAME=Demo
        - NODE_OPTIONS=--max-old-space-size=1000
        - ELASTICSEARCH_USER=kibanaserver
        - ELASTICSEARCH_PASSWORD=kibanaserver
        - ELASTICSEARCH_URL=["https://elasticsearch:9200"]
        - LOGIN_SUBTITLE=If you have forgotten your username or password ...
      links:
        - elasticsearch
      ports:
        - 5601:5601
```

#### docker-compose (without SearchGuard) [&uarr;](#getting-the-containers-)

Note: Here, access to kibiter and elasticsearch don't need credentials.
```
version: '2.2'

services:
    elasticsearch:
      image: docker.elastic.co/elasticsearch/elasticsearch-oss:6.8.6
      command: elasticsearch -Enetwork.bind_host=0.0.0.0 -Ehttp.max_content_length=2000mb
      ports:
        - 9200:9200
      environment:
        - ES_JAVA_OPTS=-Xms2g -Xmx2g
        - ANONYMOUS_USER=true

    kibiter:
      restart: on-failure:5
      image: bitergia/kibiter:community-v6.8.6-3
      environment:
        - PROJECT_NAME=Demo
        - NODE_OPTIONS=--max-old-space-size=1000
        - ELASTICSEARCH_URL=http://elasticsearch:9200
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
```

Save the above into a docker-compose.yml file and run
```
$ docker-compose up -d
```
to get ElasticSearch, Kibiter and MariaDB running on your system.

### Cloning the repositories [&uarr;](#source-code-and-docker-)

In the next step, you will need to fork all the GitHub repos below and clone them to a target local folder (e.g., `sources`).

- [SirModred](https://github.com/chaoss/grimoirelab-sirmordred)
- [ELK](https://github.com/chaoss/grimoirelab-elk)
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

Each local repo should have two `remotes`: `origin` points to the forked repo, while `upstream` points to the original CHAOSS repo.

An example is provided below.
```
$ git remote -v
origin	https://github.com/valeriocos/perceval (fetch)
origin	https://github.com/valeriocos/perceval (push)
upstream	https://github.com/chaoss/grimoirelab-perceval (fetch)
upstream	https://github.com/chaoss/grimoirelab-perceval (push)
```

In order to add a remote to a Git repository, you can use the following command:
```
$ git remote add upstream https://github.com/chaoss/grimoirelab-perceval
```

#### ProTip [&uarr;](#cloning-the-repositories-)

You can use this use this [script](https://gist.github.com/vchrombie/4403193198cd79e7ee0079259311f6e8) to automate this whole process.
```
$ python3 glab-dev-env-setup.py --create --token xxxx --source sources
```

### Setting up PyCharm [&uarr;](#source-code-and-docker-)

> Help: 
> You need to install PyCharm (**Community Edition**) for this. Please refer the documentation.
> - https://www.jetbrains.com/help/pycharm/installation-guide.html
>
> You can follow this [tutorial](https://www.jetbrains.com/help/pycharm/quick-start-guide.html) to get familiar with PyCharm.

Once PyCharm is installed create a project in the grimoirelab-sirmordred directory. 
PyCharm will automatically create a virtual env, where you should install the dependencies listed in each 
requirements.txt, **excluding** the ones concerning the grimoirelab components.

To install the dependencies, you can click on `File` -> `Settings` -> `Project` -> `Project Interpreter`, and then the `+` located on the top right corner (see figure below).

![project-interpreter-configuration](https://user-images.githubusercontent.com/25265451/78168870-3e612580-746e-11ea-9df1-7ba94b84d07b.gif)

Later, you can add the dependencies to the grimoirelab components via `File` -> `Settings` -> `Project` -> `Project Structure`. 
The final results should be something similar to the image below.

![project-structure-configuration](https://user-images.githubusercontent.com/25265451/78168879-41f4ac80-746e-11ea-9e40-dbdb1b5d32f2.gif)

### Execution [&uarr;](#source-code-and-docker-)

Now that you have the ElasticSearch, Kibiter and MariaDB running on your system and the project configured in the PyCharm, we can execute micro-mordred/sirmordred. 

To execute micro-mordred, define a [setup.cfg](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/setup.cfg) and [projects.json](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/projects.json), and
run the following commands, which will collect and enrich the data coming from the git sections and upload the corresponding panels to Kibiter:
```
micro.py --raw --enrich --cfg ./setup.cfg --backends git cocom
micro.py --panels --cfg ./setup.cfg
```

Optionally, you can create a configuration in PyCharm to speed up the executions (`Run` -> `Edit configuration` -> `+`).

![add-micro-configuration](https://user-images.githubusercontent.com/25265451/78168875-402ae900-746e-11ea-8bd8-4b3e68992bdf.gif)

The final results should be something similar to the image below.

![result](https://user-images.githubusercontent.com/25265451/84477839-ee90ad00-acad-11ea-932f-cc7ce81e05a7.png)

## Only docker [&uarr;](#getting-started-)

Follow the instruction in the GrimoireLab tutorial to have [SirMordred in a container](https://chaoss.github.io/grimoirelab-tutorial/sirmordred/container.html)

---

## Troubleshooting [&uarr;](/README.md#contents)

Following is a list of common problems encountered while setting up GrimoireLab
* [Low Virtual Memory](#low-virtual-memory-)
* [Conflicts With Searchguard](#processes-have-conflicts-with-searchguard-)
* [Permission Denied](#permission-denied-)
* [Empty Index](#empty-index-)
* [Low File Descriptors](#low-file-descriptors-)
* [Rate Limit Exhausted](#rate-limit-exhausted-)
* [No Swap Space](#no-swap-space-)
* [SSL error](#ssl-error-)
* [Cloc installation](#cloc-installation-)
* [Not getting a full data set](#incomplete-data)

> **NOTE**: In order to see the logs, run ```docker-compose up``` without the ```-d``` or ```--detach``` option while starting/(re)creating/building/attaching containers for a service.

#### Low Virtual Memory [&uarr;](#troubleshooting-)

* Indications:gi
  Cannot open ```https://localhost:9200/``` in browser. Shows ```Secure connection Failed```,
  ```PR_END_OF_FILE_ERROR```, ```SSL_ERROR_SYSCALL in connection to localhost:9200``` messages.

* Diagnosis:
    Check for the following log in the output of ```docker-compose up```
   ```
   elasticsearch_1  | ERROR: [1] bootstrap checks failed
   elasticsearch_1  | [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
   ````
* Solution:
    Increase the kernel ```max_map_count``` parameter of vm. Execute the following command
    ```sudo sysctl -w vm.max_map_count=262144```
    Now stop the container services and re-run ```docker-compose up```.
    Note that this is valid only for current session. To set this value permanently, update the ```vm.max_map_count``` setting
    in /etc/sysctl.conf. To verify after rebooting, run sysctl vm.max_map_count.

#### Processes have conflicts with SearchGuard [&uarr;](#troubleshooting-)

* Indications:
    - Cannot open ```localhost:9200``` in browser, shows ```Secure connection Failed```
    - ```curl -XGET localhost:9200 -k``` gives
    ```curl: (52) Empty reply from server```

* Diagnosis:
    Check for the following log in the output of ```docker-compose up```
    ```
    elasticsearch_1  | [2020-03-12T13:05:34,959][WARN ][c.f.s.h.SearchGuardHttpServerTransport] [Xrb6LcS] Someone (/172.18.0.1:59838) speaks http plaintext instead of ssl, will close the channel
    ```
    Check for conflicting processes by running ```sudo lsof -i:58888``` (e.g.  58888 is the port number)

* Solution:
    1. Try to close the conflicting processes:
        You can do this easily with fuser (```sudo apt-get install fuser```), 
        run ```fuser -k 58888/tcp``` (e.g. 58888 is the port number).
        Re-run ```docker-compose up``` and check if ```localhost:9200``` shows up.
    2. Use a [docker-compose without SearchGuard](#docker-compose-without-searchguard-):
        Use the docker-compose above, this doesn't include SearchGuard.
        Note: With this docker-compose, access to the Kibiter and ElasticSearch don't require credentials.
        Re-run ```docker-compose up``` and check if ```localhost:9200``` shows up.

#### Permission Denied [&uarr;](#troubleshooting-)

* Indications:
  Can't create indices in Kibana. Nothing happens after clicking create index.

* Diagnosis:
  Check for the following log in the output of ```docker-compose up```
  ```
  elasticsearch_1 |[INFO ][c.f.s.c.PrivilegesEvaluator] No index-level perm match for User [name=readall, roles=[readall], requestedTenant=null] [IndexType [index=.kibana, type=doc]] [Action [[indices:data/write/index]]] [RolesChecked [sg_own_index, sg_readall]]

  elasticsearch_1 | [c.f.s.c.PrivilegesEvaluator] No permissions for {sg_own_index=[IndexType [index=.kibana, type=doc]], sg_readall=[IndexType [index=.kibana, type=doc]]}

  kibiter_1 | {"type":"response","@timestamp":CURRENT_TIME,"tags":[],"pid":1,"method":"post","statusCode":403,"req":{"url":"/api/saved_objects/index-pattern?overwrite=false","method":"post","headers":{"host":"localhost:5601","user-agent":YOUR_USER_AGENT,"accept":"application/json, text/plain, /","accept-language":"en-US,en;q=0.5","accept-encoding":"gzip, deflate","referer":"http://localhost:5601/app/kibana","content-type":"application/json;charset=utf-8","kbn-version":"6.1.4-1","content-length":"59","connection":"keep-alive"},"remoteAddress":YOUR_IP,"userAgent":YOUR_IP,"referer":"http://localhost:5601/app/kibana"},"res":{"statusCode":403,"responseTime":25,"contentLength":9},"message":"POST /api/saved_objects/index-pattern?overwrite=false 403 25ms - 9.0B"} 
  ```
  or any type of 403 error.
  
* Solution:
  This message generally appears when you try to create an index pattern but you are not logged in Kibana.
  Try logging in to Kibana (the login button is on the bottom left corner).
  The credentials used for login should be username: `admin` and password: `admin`.

#### Empty Index [&uarr;](#troubleshooting-)

* Indications and Diagnosis:
  Check for the following error after executing [Micro Mordred](https://github.com/chaoss/grimoirelab-sirmordred/tree/master/utils/micro.py)
  using ```micro.py --raw --enrich --panels --cfg ./setup.cfg --backends git```(Here, using git as backend)
  ```
  [git] Problem executing study enrich_areas_of_code:git, RequestError(400, 'search_phase_execution_exception', 'No mapping 
  found for [metadata__timestamp] in order to sort on')
  ```
* Solution:
  This error appears when the index is empty (here, ```git-aoc_chaoss_enriched``` index is empty). An index can be empty when 
  the local clone of the repository being analyzed is in sync with the upstream repo, so there will be no new commits to 
  ingest to grimoirelab.
  
  There are 2 methods to solve this problem:
 
  Method 1: Disable the param [latest-items](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/setup.cfg#L78) by setting it to false.
  
  Method 2: Delete the local clone of the repo (which is stored in ```~/.perceval/repositories```).
 
  Some extra details to better understand this behavior:
  
  The Git backend of perceval creates a clone of the repository (which is stored in ```~/.perceval/repositories```) and keeps the local
  copy in sync with the upstream one. This clone is then used to ingest the commits data to grimoirelab.
  Grimoirelab periodically collects data from different data sources (in this specific case, a git repository) in an incremental way. 
  A typical execution of grimoirelab for a git repository consists of ingesting only the new commits to the platform. These 
  commits are obtained by comparing the local copy with the upstream one, thus if the two repos are synchronized, then no 
  commits are returned and hence Index will be empty. In the case where all commits need to be extracted even if there is already a
  local clone, latest-items param should be disabled. Another option is to delete the local clone (which is stored at ```~/.perceval/repositories```),
  and by doing so the platform will clone the repo again and extract all commits. 
 
#### Low File Descriptors [&uarr;](#troubleshooting-)

* Indications:
    - Cannot open ```localhost:9200``` in browser, shows ```Secure connection Failed```
    - ```curl -XGET localhost:9200 -k``` gives
    ```curl: (7) Failed to connect to localhost port 9200: Connection refused```
    
* Diagnosis:
  Check for the following log in the output of ```docker-compose up```
  ```
    elasticsearch_1  | ERROR: [1] bootstrap checks failed
    elasticsearch_1  | [1]: max file descriptors [4096] for elasticsearch process is too low, increase to at least [65536]
  ```

* Solution:
  1. Increase the maximum File Descriptors (FD) enforced:
  
        You can do this by running the below command.
        ```
        sysctl -w fs.file-max=65536
        ```
        
        To set this value permanently, update `/etc/security/limits.conf` content to below.
        To verify after rebooting, run `sysctl fs.file-max`.
        ```
        elasticsearch   soft    nofile          65536
        elasticsearch   hard    nofile          65536
        elasticsearch   memlock unlimited
        ```
   
  1. Override `ulimit` parameters in the ElasticSearch docker configuration:
  
        Add the below lines to ElasticSearch service in 
        your compose file to override the default configurations of docker.
        ```
        ulimits:
        nofile:
          soft: 65536
          hard: 65536
        ```
#### Rate Limit Exhausted [&uarr;](#troubleshooting-)


* Indication: See error message ```RuntimeError: Rate limit exhausted.; 3581.0 seconds to rate reset```

* Solution : Enable the ```sleep-for-rate``` parameter. It increases rate by sleeping between API call retries.



#### No Swap Space [&uarr;](#troubleshooting-)


* Indication: While composing docker , NO SWAP SPACE would be displayed.

* Solution:  Edit the ```/etc/default/grub file``` with sudo previleges.
	
	```
	    GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1" 
		sudo update-grub
	```
    And restart the system.


#### SSL error [&uarr;](#troubleshooting-)

* Indication: localhost:9200 refuses connection error.

* Diagnosis: 

```
Retrying (Retry(total=10,connected=21,read=0,redirect=5,status=None)) after connection broken by 
'SSLError(SSLError{1,'[SSL: WRONG_VERSION_NUMBER] wrong version number {_ssl.c:852}'},)': /
```

* Solution:

  * Change 'https' to 'http' in the setup.cfg file

  ```
  [es_collection]
  # arthur = true
  # arthur_url = http://127.0.0.1:8080
  # redis_url = redis://localhost/8
  url = http://localhost:9200

  [es_enrichment]
  url = http://localhost:9200
  ```


#### Cloc installation [&uarr;](#troubleshooting-)

* Diagnosis:

```
: [Errno 2]No such file or directory : 'cloc': 'cloc'
```

* Solution:

  Execute the following command to install `cloc` (more details are available in the [Graal](https://github.com/chaoss/grimoirelab-graal#how-to-installcreate-the-executables) repo) 

  ```
  sudo apt-get install cloc
  ```
#### Incomplete data [&uarr;](#incomplete-data)

* Indication: Not all the data is being retrieved when rebuilding an index - only from a point in time forward.

* Diagnosis: After a rebuild of git-based indices you are not receiving a full dataset as expected, but only from the date of the re-index forward. That data is complete, but anything prior to that is missing.

* Solution: The `setup.cfg`  file has an option under the Git configuration section: `latest-items = true` - set this to `latest-items = false` to pull in all data from the beginnning. Once this has been processed, remember to set it back to `latest-items = true`!


---

## How to [&uarr;](/README.md#contents)

Following are some tutorials for ElasticSearch and Kibiter:

* [Query data in ElasticSearch](#query-data-in-elasticsearch-)
* [Dump the index mapping/data with elasticdump](#dump-the-index-mappingdata-with-elasticdump-)
* [Save changes made in dashboard by mounting the volume in ES](#save-changes-made-in-dashboard-by-mounting-the-volume-in-es-)
* [Build a data table visualization in Kibiter](#build-a-data-table-visualization-in-kibiter-)
* [Modify the menu](#modify-the-menu-)
* [Share a dashboard](#share-a-dashboard-)
* [Rename titles and resize a panel](#rename-titles-and-resize-a-panel-)
* [Update format of attributes](#update-format-of-attributes-)
* [Edit the name of a Visualization](#edit-the-name-of-a-visualization-)
* [Share a dashboard](#share-a-dashboard-)
* [Edit a Visualization](#edit-a-visualization-)
* [Check that the data is up to date](#check-that-the-data-is-up-to-date-)
* [Handle identities assigned to "Unknown" organization](#handle-identities-assigned-to-unknown-organization-)
* [Add a new organization/domain entry via Hatstall](#add-a-new-organizationdomain-entry-via-hatstall-)
* [Remove Dockers and start a fresh environment](#remove-existing-dockers-and-start-a-fresh-environment-)

### Elasticsearch

#### Query data in ElasticSearch [&uarr;](#how-to-)

To query data in ElasticSearch select Dev tools from the navigation menu in Kibiter and write
the required query in the console.

The below query counts the number of unique authors on a Git repository from 2018-01-01 until 2019-01-01.
```
GET _search
{
  "size":"0",
  "query": {
    "range": {
      "author_date": {
        "gte": "2018-01-01T00:00:00",
        "lte": "2019-01-01T00:00:00"
      }
    }
  },
  "aggs": {
    "author_unique": {
       "cardinality": {
        "field": "author_id"
      }
    }
  }
}

```

 The parameter `size` specifies that we dont need the data fetched from the index, this is included as
 only count of authors is required and not the data of authors. The parameter `query` includes
 the `range` of the field `author_date` for which the data is requested. The number of
 distinct author are calculated using `cardinality` of `author_id`.
 
 Output:
 ```
{
  "took": 0,
  "timed_out": false,
  "_shards": {
    "total": 16,
    "successful": 16,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": 128,
    "max_score": 0,
    "hits": []
  },
  "aggregations": {
    "author_unique": {
      "value": 11
    }
  }
}

``` 

The `value` field holds the number of distinct authors during the given time range. 

![Data Query to fetch count of unique authors in a git repository](https://user-images.githubusercontent.com/32506591/77189005-e553d200-6afc-11ea-8d40-59b6e7c4c723.png)

Alternatively, a data table visualization can be created using the steps mentioned [here](#build-a-data-table-visualization-in-kibiter-).Then, a `request` can be generated by click the `^` symbol at the bottom.
Kibiter then automatically generates a query as shown below.

![Creating data query through request](https://user-images.githubusercontent.com/32506591/77188682-5e065e80-6afc-11ea-9b00-a927690cc76e.png)


#### Dump the index mapping/data with elasticdump [&uarr;](#how-to-)

Indexes and mappings can be dumped (or uploaded) using [elasticdump](https://github.com/taskrabbit/elasticsearch-dump). The commands to install elasticdump, dump an index and its index pattern to a file are shown below.

**elasticdump installation**

```
sudo apt install npm
sudo -i
npm install elasticdump -g
```

CTRL+D to logout from root user

***

> Use the 'type' argument to either fetch data or mapping.


**Dump the index data**

```
elasticdump --input=http://localhost:9200/git_chaoss/ --output=git_data.json --type=data
```

**Dump the index mapping**

```
elasticdump --input=http://localhost:9200/git_chaoss/ --output=git_mapping.json --type=mapping
```
#### Save changes made in dashboard by mounting the volume in ES [&uarr;](#how-to-)

Creating new dashboard or new visualisation in the Kibana Dashabord can be saved permanently using volume mount in ElasticSearch

Using docker-compose:

1.Configure the docker-compose yml file:

```
services:
   elasticsearch:
      image: docker.elastic.co/elasticsearch/elasticsearch-oss:6.8.6
      command: elasticsearch -Enetwork.bind_host=0.0.0.0 -Ehttp.max_content_length=2000mb
      ports:
        - 9200:9200
      environment:
        - ES_JAVA_OPTS=-Xms2g -Xmx2g
        - ANONYMOUS_USER=true
      volumes:
        - <volumename>:/usr/share/elasticsearch/data
volumes:
  <volumename>:
```
	
2.Execute `docker-compose up -d`

3.Go to `localhost:5601` and create new dashboard according to your requirements 

4.Click on save 

5.Save with some new name for the created dashboard

6.Stop the container by `docker-compose down `command

7.Start again by `docker-compose up -d`

You can see all the changes are persistently stored in the local folder and hence cannot be deleted even if all the containers are stopped, reason being volumes are created.

`Note` : If you do not want to use volumes for storage then you should use `docker-compose stop` instead of `docker-compose down` , so that none of the containers is removed.

### Kibiter

#### Build a data table visualization in Kibiter [&uarr;](#how-to-)

1. Go to your Kibiter dashboard and select `Visualize` from the left navigation menu.

1. Click on the '+' icon next to the search bar to create a new visualization.

1. Select 'Data Table' to display the values in a table.

1. Select the index which is to be visualized.

1. Under the `Bucket` options click on `Split Row` to split the table into rows(or `Split Table` to split the table into additional tables) and set the following options:

* `Aggregation` - Set it to `Terms`. This selects the fields in the table based on a term present in the index.
* `Field` - Select the fields which are to be included in the table.
* `Order` - Order in which fields are displayed. 
* `Size` - Maximum number of fields to be included in the table.

7 . Click the apply changes button to get the date table visualization. You can also save the
    visualizations for future references.
    
The below image uses the [CHAOSS community dashboard](https://chaoss.biterg.io/app/kibana#/visualize/new?_g=())
to create a data table visualization on `mbox` index which is split row by the term `body_extract`.

![Data table visualization](https://user-images.githubusercontent.com/32506591/77189179-29df6d80-6afd-11ea-8f90-cf0d22973e39.png)


#### Modify the menu [&uarr;](#how-to-)

- Get the current menu: `GET <elasticsearch_url>/.kibana/doc/metadashboard`. It will return a json with the following structure:

```
{
  "metadashboard": [
      {
        "name": "Panel 1",
        "title": "Panel 1"
        "description": "This is a link to a panel",
        "panel_id": "panel_1",
        "type": "entry",
      },
      {
        "name": "Tab 1",
        "title": "Tab 1"
        "description": "This is a tab, when clicked a submenu with the panels will appear",
        "type": "menu",
        "dashboards": [
          {
            "description": "This is a link to a panel",
            "panel_id": "panel_1_tab_1",
            "type": "entry",
            "name": "Panel 1 of the Tab 1",
            "title": "Panel 1 of the Tab 1"
          },
          ...
        ],
      },
      ...
  ]
}
```

- If you want to add an **entry** (a link to a dashboard) you can do it in two different ways:

  1. Adding a link in the root menu:
    ```
    {
      "metadashboard": [
          {
            "name": "Panel 1",
            "title": "Panel 1"
            "description": "This is a link to a panel",
            "panel_id": "panel_1",
            "type": "entry",
          },
          //////////New entry///////////
          {
            "name": "New entry",
            "title": "New entry"
            "description": "This is a link to a panel",
            "panel_id": "<id_of_the_dashboard>",
            "type": "entry",
          },
          /////////////////////////////
          {
            "name": "Tab 1",
            "title": "Tab 1"
            "description": "This is a tab, when clicked a submenu with the panels will appear",
            "type": "menu",
            "dashboards": [
              {
                "description": "This is a link to a panel",
                "panel_id": "panel_1_tab_1",
                "type": "entry",
                "name": "Panel 1 of the Tab 1",
                "title": "Panel 1 of the Tab 1"
              },
              ...
            ],
          },
          ...
      ]
    }
    ```
    2. Adding a link in a submenu of a tab:
    ```
    {
      "metadashboard": [
          {
            "name": "Panel 1",
            "title": "Panel 1"
            "description": "This is a link to a panel",
            "panel_id": "panel_1",
            "type": "entry",
          },
          {
            "name": "Tab 1",
            "title": "Tab 1"
            "description": "This is a tab, when clicked a submenu with the panels will appear",
            "type": "menu",
            "dashboards": [
              {
                "description": "This is a link to a panel",
                "panel_id": "panel_1_tab_1",
                "type": "entry",
                "name": "Panel 1 of the Tab 1",
                "title": "Panel 1 of the Tab 1"
              },
              //////////New entry///////////
              {
                "name": "New entry",
                "title": "New entry"
                "description": "This is a link to a panel",
                "panel_id": "<id_of_the_dashboard>",
                "type": "entry",
              },
              /////////////////////////////
              ...
            ],
          },
          ...
      ]
    }
    ```
  
- If you want to add a new **tab** (item that will show a submenu with entries) you must do it in the root menu:

```
{
  "metadashboard": [
      {
        "name": "Panel 1",
        "title": "Panel 1"
        "description": "This is a link to a panel",
        "panel_id": "panel_1",
        "type": "entry",
      },
      {
        "name": "Tab 1",https://user-images.githubusercontent.com/35267629/79070495-efc84c80-7cf3-11ea-8543-66989e84c094.gif
        "title": "Tab 1"
        "description": "This is a tab, when clicked a submenu with the panels will appear",
        "type": "menu",
        "dashboards": [
          {
            "description": "This is a link to a panel",
            "panel_id": "panel_1_tab_1",
            "type": "entry",
            "name": "Panel 1 of the Tab 1",
            "title": "Panel 1 of the Tab 1"
          },
          ...
        ],
      },
      //////////New tab///////////
      {
        "name": "New tab",
        "title": "New tab"
        "description": "This is a tab, when clicked a submenu with the panels will appear",
        "type": "menu",
        "dashboards": [
          {
            "description": "This is a link to a panel",
            "panel_id": "<id_of_the_dashboard>",
            "type": "entry",
            "name": "Panel 1 of the New tab",
            "title": "Panel 1 of the New tab"
          },
          ...
        ],
      },
      ////////////////////////////
      ...
  ]
}
```


- Once the json of the menu has been modified, the final step is to upload it updating the version: `PUT <elasticsearch_url>/.kibana/doc/metadashboard`


> :warning: **If you change the structure or delete it** you won't see the menu.

> **Note**: the `<id_of_the_dashboard>` must be the identifier that Kibana/Kibiter put to a saved dashboard.

#### Rename titles and resize a panel [&uarr;](#how-to-)

1. All the gitter panel titles can be renamed and resized as shown.

![Resize and Rename](https://user-images.githubusercontent.com/35267629/79070495-efc84c80-7cf3-11ea-8543-66989e84c094.gif)

#### Update format of attributes [&uarr;](#how-to-)

1. In order to convert URLs in a table visualization from plain text to a link you need to update the format of the attribute in index pattern as shown.

![Update format](https://user-images.githubusercontent.com/6515067/79062792-79006480-7c9d-11ea-9f71-fc2372bbc326.gif)

Plain text URL -

![Plain Text](https://user-images.githubusercontent.com/35267629/79062222-b244ce80-7cb5-11ea-90fe-dd6082893ad3.png)

Hyperlink -

![Link](https://user-images.githubusercontent.com/35267629/79062221-b07b0b00-7cb5-11ea-88b3-677264e9918d.png)

#### Share a dashboard [&uarr;](#how-to-)

1. Click on `share` on top right corner of the browser. 

2. There will be 2 options: Share saved Dashboard or share snapshot.

3. Copy the link present under 'Link' under 'Share Saved dashboard' and use it anywhere. This will be a shortened url, and can be easily used accross browsers.

4. You can also extract the embedded iframe and add it to the HTML source. 


#### Edit the name of a visualization [&uarr;](#how-to-)

1. Go to `Save` visualization on top right of browser window.

2. Enter the new name. The default name is 'New Visualization'.

3. Uncheck the option that says 'save as a new visualization'. 

4. Now you can see the changed name of the visualization.


#### Edit a visualization [&uarr;](#how-to-)

1. Go to 'Visualize' option given on the left sidebar.

2. Open the saved visualization file. 

3. Make changes as per needs.

4. Save again by Clicking 'Save'.

#### Check that the data is up to date [&uarr;](#how-to-)

1. Go to `Data Status` on top right of browser window.

2. Check the last retrieval date to know the last date of data retrieval.


### Identity management

#### Handle identities assigned to "Unknown" organization [&uarr;](#how-to-)

To provide some context, [SortingHat](https://github.com/chaoss/grimoirelab-sortinghat) is the GrimoireLab tool
behind the scenes which is in charge of managing the identities information from the sources you are analyzing. 

SortingHat allows to manage affiliation information too, including the organization(s) a person/user belongs to
and the date periods for each of them. The organization a user belongs to can be inferred using the email domains
from every user, for instance: if we have a user who contributed to one of the sources with an email with domain
`@mozilla.com`, it will be automatically affiliated to `Mozilla` organization.

This automatic affiliation works because there is an entry in SortingHat registry matching `mozilla.com` domain
with `Mozilla` organization. When this automatic affiliation cannot be applied, that user will not have any 
affiliation information (at least for the period of time you are visualizing on the dashboard after setting a date
range with the time-picker), it will appear as `Unknown` on the dashboard.

<img src="https://user-images.githubusercontent.com/63613092/87360165-cb397600-c569-11ea-8dd5-141618e8c826.png" alt="example-unknown" width="600"/><br>

This could be happening because:
* (1) There is no email domain information for those users.
* (2) Their email domain(s) are not linked to any organization in SortingHat.
* (3) The same user can have different identities (e.g. contributions coming from different sources or accounts)
and they are considered as different individuals.

About possible solutions:
* (2) can be solved by adding the corresponding entry to SortingHat, i.e. via Hatstall.
* (3) can be solved by merging those identities under the same individual, which can be done via SortingHat too.

Note: by default, SortingHat is importing the list of organizations and domains
[from this file](https://github.com/chaoss/grimoirelab/blob/master/default-grimoirelab-settings/organizations.json).

#### Add a new organization/domain entry via Hatstall [&uarr;](#how-to-)

[Hatstall](https://github.com/chaoss/grimoirelab-hatstall) is a web interface to interact with SortingHat.
 
Tip: if you are executing GrimoireLab [via `docker-compose`](https://github.com/chaoss/grimoirelab/tree/master/docker-compose),
you can access Hatstall from  `http://127.0.0.1:8000/`. Default credentials are `admin`-`admin`, as explained in 
[this README section](https://github.com/chaoss/grimoirelab/tree/master/docker-compose#getting-started-in-3-steps). 

For adding a new organization domain from Hatstall, you have to click on `Organizations` tab on the nav bar, and then:
* First, look for the organization you are interested in (you can navigate though the pages or you can use the search bar).
  * If the organization you are looking for does not appear, click on `Add` button and add the new organization first.
* Once you have located the organization, click on `edit` and then a menu will pop-up on the right. There, you will be 
able to add new domains for that organization.

![example-add-domain](https://user-images.githubusercontent.com/9032790/87524852-ff578880-c688-11ea-8331-9e6a9062cf8d.png)

### Others

#### Remove existing dockers and start a fresh environment [&uarr;](#how-to-)

   - Stop and remove all the containers with `docker-compose down --remove-orphans`.
   
   - Run `docker ps` and ensure that there is no entry in the output.
    
   - Remove all unused containers, images, and volumes with  `docker system prune -a --volumes`.

   - Now, execute `docker-compose up -d` using the source code (see - https://github.com/chaoss/grimoirelab-sirmordred/blob/master/Getting-Started.md#source-code-and-docker- )

   - Check connection to Elasticsearch with `curl -XGET <elasticsearch-url> -k`.
        The output should be the similar to :
   
   ```
  {
  "name" : "1STIspn",
  "cluster_name" : "bitergia_elasticsearch",
  "cluster_uuid" : "NNHIQCbDQHG5sg2MX_WRjA",
  "version" : {
    "number" : "6.8.6",
    "build_flavor" : "oss",
    "build_type" : "tar",
    "build_hash" : "3d9f765",
    "build_date" : "2019-12-13T17:11:52.013738Z",
    "build_snapshot" : false,
    "lucene_version" : "7.7.2",
    "minimum_wire_compatibility_version" : "5.6.0",
    "minimum_index_compatibility_version" : "5.0.0"
  },
  "tagline" : "You Know, for Search"
  }

   ```
   - Execute micro mordred (see - https://github.com/chaoss/grimoirelab-sirmordred#micro-mordred-)
