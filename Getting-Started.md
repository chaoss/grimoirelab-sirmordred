## Getting started [&uarr;](/README.md#contents)

SirModred relies on ElasticSearch, Kibiter and MySQL/MariaDB. The current versions used are:
- ElasticSearch 6.1.0
- Kibiter 6.1.4
- MySQL/MariaDB (5.7.24/10.0)

There are 3 options to get started with SirMordred:
- [Source code](#source-code-)
- [Source code and docker](#source-code-and-docker-)
- [Only docker](#only-docker-)

You can also [set up a development environment in pycharm](#setting-up-a-pycharm-dev-environment-) and develop from there if you are comfortable with the Pycharm IDE.


### Source code [&uarr;](#getting-started-)

You will need to install ElasticSearch (6.1.0), Kibiter (6.1.4) and a MySQL/MariaDB database (5.7.24/10.0), and the following components:

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

### Source code and docker [&uarr;](#getting-started-)

You will have to install the GrimoireLab components listed above, and use the following docker-compose to have ElasticSearch, Kibiter and MariaDB.
Note that you can omit the `mariadb` section in case you have MySQL/MariaDB already installed in your system.

#### docker-compose (with SearchGuard) [&uarr;](#source-code-and-docker-)
Note: For accessing Kibiter and/or creating indexes login is required, the `username:password` is `admin:admin`.
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
    - ELASTICSEARCH_USER=kibanaserver
    - ELASTICSEARCH_PASSWORD=kibanaserver
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
#### docker-compose (without SearchGuard) [&uarr;](#source-code-and-docker-)
Note: Here, access to kibiter and elasticsearch don't need credentials.
```
version: '2.2'

services:
    elasticsearch:
      image: docker.elastic.co/elasticsearch/elasticsearch-oss:6.1.4
      command: /elasticsearch/bin/elasticsearch -E network.bind_host=0.0.0.0
      ports:
        - 9200:9200
      environment:
        - ES_JAVA_OPTS=-Xms2g -Xmx2g

    kibiter:
      restart: on-failure:5
      image: bitergia/kibiter:optimized-v6.1.4-4
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
docker-compose up -d
```
to get ElasticSearch, Kibiter and MariaDB. Comment/remove the mariadb section in case you have MariaDB or MySQL already installed in your system.

You can read more about docker and docker-compose [here](https://docs.docker.com/compose/)

### Only docker [&uarr;](#getting-started-)

Follow the instruction in the GrimoireLab tutorial to have [SirMordred in a container](https://chaoss.github.io/grimoirelab-tutorial/sirmordred/container.html)


### Setting up a Pycharm dev environment [&uarr;](#getting-started-)

This section provides details about how to set up a dev environment using PyCharm. The first step consists in forking
the GitHub repos below and cloning them to a target local folder (e.g., `sources`).

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

Then, you can download the [PyCharm community edition](https://www.jetbrains.com/pycharm/download/#section=linux), using any of the following alternatives:

* **Alternative 1: Install PyCharm via Snap Package Management**
    
    Install Snap Package Management using the below command.

     `sudo apt install snapd snapd-xdg-open`
    
    Now that `Snap` is installed, run the command below to install the community version of PyCharm.
    
     `sudo snap install pycharm-community --classic`

* **Alternative 2: Install PyCharm via Ubuntu Software Center**

    Open Ubuntu Software Center and search for PyCharm. Then, select and install the community version of PyCharm.

* **Alternative 3: Download PyCharm tar file**

    Go to the official website of [JetBrains]((https://www.jetbrains.com/pycharm/download/#section=linux)) and download the community version of PyCharm for your system.
    Then, extract the downloaded `tarfile` file using the below command.
    
    `tar -xzf tarfile`

    Go to the `bin` directory and run the PyCharm shell.

After the installation is complete, this [tutorial](https://www.jetbrains.com/help/pycharm/quick-start-guide.html)
can be followed to gain familiarity with PyCharm.

Once PyCharm is installed create a project in the grimoirelab-sirmordred directory. 
PyCharm will automatically create a virtual env, where you should install the dependencies listed in each 
requirements.txt, excluding the ones concerning the grimoirelab components.

To install the dependencies, you can click on `File` -> `Settings` -> `Project` -> `Project Interpreter`, and then the `+` located on the top right corner (see figure below).

![captura_22](https://user-images.githubusercontent.com/6515067/63195511-12299d80-c073-11e9-9774-5f274891720a.png)

Later, you can add the dependencies to the grimoirelab components via `File` -> `Settings` -> `Project` -> `Project Structure`. 
The final results should be something similar to the image below.

![captura_23](https://user-images.githubusercontent.com/6515067/63195579-4b620d80-c073-11e9-888b-3cdb67c04523.png)

Finally, you can use the docker-compose shown at Section [source-code-and-docker](#source-code-and-docker-), define a [setup.cfg](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/setup.cfg) and [projects.json](https://github.com/chaoss/grimoirelab-sirmordred/blob/master/utils/projects.json), and
run the following commands, which will collect and enrich the data coming from the git and cocom sections and upload the corresponding panels to Kibiter:
```
micro.py --raw --enrich --cfg ./setup.cfg --backends git cocom
micro.py --panels --cfg ./setup.cfg
```

Optionally, you can create a configuration in PyCharm to speed up the executions (`Run` -> `Edit configuration` -> `+`). The final results should be something similar to the image below.

![captura_24](https://user-images.githubusercontent.com/6515067/63195767-ccb9a000-c073-11e9-805a-e828a3ce1dc9.png)
 
## Troubleshooting [&uarr;](/README.md#contents)

Following is a list of common problems encountered while setting up GrimoireLab
* [Low Virtual Memory](#low-virtual-memory-)
* [Conflicts With Searchguard](#processes-have-conflicts-with-searchguard-)
* [Permission Denied](#permission-denied-)
* [Empty Index](#empty-index-)
* [Low File Descriptors](#low-file-descriptors-)
* [Rate Limit Exhausted](#rate-limit-exhausted-)
* [No Swap Space](#no-swap-space-)


---
**NOTE**

In order to see the logs, run ```docker-compose up``` without the ```-d``` or ```--detach``` option while
starting/(re)creating/building/attaching containers for a service.

---

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

## How to [&uarr;](/README.md#contents)

Following are some tutorials for ElasticSearch and Kibiter:

* [Build a data table visualization in Kibiter](#build-a-data-table-visualization-in-kibiter-)
* [Query data in ElasticSearch](#query-data-in-elasticsearch-)


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
